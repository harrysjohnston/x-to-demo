"""X-to-Demo orchestration service with typed phases and JSON-first artifacts."""

from __future__ import annotations

import io
import logging
import re
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar
from uuid import uuid4

from app.config import settings
from app.pubsub import pubsub
from app.services.model_capabilities import (
    default_reasoning_effort,
    supports_reasoning,
    validate_model_name,
    validate_reasoning_effort,
)
from app.x_to_demo.pipeline import (
    PIPELINE_PHASES,
    PhaseCallMetrics,
    PhaseKey,
    PipelineArtifact,
    PipelinePhaseDefinition,
    PipelineRunInput,
    PipelineRunResult,
)
from app.x_to_demo.pipeline.artifacts import PipelineArtifactManager
from app.x_to_demo.pipeline.manifest import PipelineManifestManager
from app.x_to_demo.pipeline.phase_execution import run_structured_phase
from app.x_to_demo.pipeline.pricing import (
    PRICING_PATH,
    estimate_cost,
    load_pricing_table,
    merge_costs,
    merge_usage,
    normalize_model_for_pricing,
    parse_price,
)
from app.x_to_demo.pipeline.progress import publish_progress_event
from app.x_to_demo.pipeline.prompts import (
    build_phase_prompts,
    enforce_no_additional_properties,
    openai_compatible_schema,
    schema_excerpt_json,
)
from app.x_to_demo.pipeline.responses import (
    call_responses_with_progress_logs,
    create_conversation_id,
    extract_model,
    extract_output_text,
    extract_status,
    extract_structured_payload,
    extract_usage,
    response_to_dict,
)
from app.x_to_demo.renderers import parse_markdown_to_model

if TYPE_CHECKING:
    import asyncio

    from pydantic import BaseModel

logger = logging.getLogger(__name__)


class XToDemoPipelineService:
    """Runs a typed multi-phase X-to-Demo pipeline with resumable execution."""

    _PHASES: ClassVar[tuple[PipelinePhaseDefinition, ...]] = PIPELINE_PHASES
    _PHASES_BY_KEY: ClassVar[dict[PhaseKey, PipelinePhaseDefinition]] = {
        phase.key: phase for phase in _PHASES
    }
    _PHASE_INDEX: ClassVar[dict[PhaseKey, int]] = {
        phase.key: index for index, phase in enumerate(_PHASES)
    }
    _PHASE_TITLES: ClassVar[dict[PhaseKey, str]] = {phase.key: phase.title for phase in _PHASES}

    def __init__(
        self,
        *,
        responses_client: object,
        model: str,
        output_dir: Path,
        store_responses: bool,
        max_input_chars: int,
        response_wait_log_interval_seconds: float = 15.0,
    ) -> None:
        self.responses_client = responses_client
        self.model = model
        self.output_dir = output_dir
        self.store_responses = store_responses
        self.max_input_chars = max_input_chars
        self.response_wait_log_interval_seconds = max(response_wait_log_interval_seconds, 0.1)
        self._manifest_manager = PipelineManifestManager(self._PHASES)
        self._artifact_manager = PipelineArtifactManager(self._PHASES)

    def run(
        self,
        *,
        x_input: str,
        additional_context: str | None,
        feature_name_hint: str | None,
        user_id: int,
        model: str | None = None,
        reasoning_effort: str | None = None,
        stop_after_phase: PhaseKey | None = None,
    ) -> PipelineRunResult:
        """Execute pipeline phases from the beginning and persist artifacts."""
        run_input = self._validate_and_build_run_input(
            x_input=x_input,
            additional_context=additional_context,
            feature_name_hint=feature_name_hint,
        )
        selected_model, selected_reasoning_effort = self._resolve_model_settings(
            model=model,
            reasoning_effort=reasoning_effort,
        )
        resolved_stop_after = self._validate_phase_key(stop_after_phase or "code_spec")

        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + f"-{uuid4().hex[:8]}"
        created_at = datetime.now(UTC)
        run_dir = self._run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        conversation_id = self._create_conversation_id(run_id=run_id, user_id=user_id)

        manifest = self._initialize_manifest(
            run_id=run_id,
            created_at=created_at,
            selected_model=selected_model,
            selected_reasoning_effort=selected_reasoning_effort,
            stop_after_phase=resolved_stop_after,
            conversation_id=conversation_id,
            run_input=run_input,
        )
        self._persist_manifest(run_dir=run_dir, manifest=manifest)

        self._publish_progress_event(
            user_id=user_id,
            payload={
                "pipeline": "x-to-demo",
                "run_id": run_id,
                "status": "run_started",
                "model": selected_model,
                "reasoning_effort": selected_reasoning_effort,
                "stop_after_phase": resolved_stop_after,
                "is_resume": False,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

        phase_metrics: list[PhaseCallMetrics] = []
        try:
            self._execute_phase_range(
                run_dir=run_dir,
                manifest=manifest,
                user_id=user_id,
                selected_model=selected_model,
                selected_reasoning_effort=selected_reasoning_effort,
                start_phase="feature_spec",
                stop_after_phase=resolved_stop_after,
                initial_input=run_input,
                is_resume=False,
                phase_metrics=phase_metrics,
            )
            manifest["status"] = "completed" if resolved_stop_after == "code_spec" else "partial"
            manifest["updated_at"] = datetime.now(UTC).isoformat()
            self._append_phase_metrics(manifest, phase_metrics=phase_metrics, is_resume=False)
            self._persist_manifest(run_dir=run_dir, manifest=manifest)
            self._publish_progress_event(
                user_id=user_id,
                payload={
                    "pipeline": "x-to-demo",
                    "run_id": run_id,
                    "status": "run_completed",
                    "completed_phase_count": len(phase_metrics),
                    "next_phase_key": self._next_incomplete_phase(manifest),
                    "is_resume": False,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
        except Exception as exc:
            manifest["status"] = "failed"
            manifest["updated_at"] = datetime.now(UTC).isoformat()
            self._append_phase_metrics(manifest, phase_metrics=phase_metrics, is_resume=False)
            self._persist_manifest(run_dir=run_dir, manifest=manifest)
            self._publish_progress_event(
                user_id=user_id,
                payload={
                    "pipeline": "x-to-demo",
                    "run_id": run_id,
                    "status": "run_failed",
                    "completed_phase_count": len(
                        [record for record in manifest["phases"] if record["status"] == "completed"]
                    ),
                    "error": str(exc),
                    "is_resume": False,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            raise

        return self._build_run_result(run_dir=run_dir, manifest=manifest)

    def resume(
        self,
        *,
        run_id: str,
        user_id: int,
        from_phase: PhaseKey | None = None,
        stop_after_phase: PhaseKey | None = None,
        use_edited_artifacts: bool = True,
    ) -> PipelineRunResult:
        """Resume an existing run from the next incomplete (or specified) phase."""
        del use_edited_artifacts  # canonical artifacts are always used as resume input.

        run_dir = self._run_dir(run_id)
        manifest = self._load_manifest(run_dir)
        selected_model, selected_reasoning_effort = self._resolve_model_settings(
            model=str(manifest.get("model") or self.model),
            reasoning_effort=str(manifest.get("reasoning_effort") or "low"),
        )

        resolved_start = (
            self._validate_phase_key(from_phase)
            if from_phase
            else self._next_incomplete_phase(manifest)
        )
        if resolved_start is None:
            return self._build_run_result(run_dir=run_dir, manifest=manifest)

        resolved_stop_after = self._validate_phase_key(stop_after_phase or "code_spec")

        if self._PHASE_INDEX[resolved_stop_after] < self._PHASE_INDEX[resolved_start]:
            raise ValueError("stop_after_phase must be at or after from_phase")

        initial_input = self._build_resume_input(
            run_dir=run_dir,
            manifest=manifest,
            start_phase=resolved_start,
        )
        self._reset_phases_from(manifest=manifest, start_phase=resolved_start)
        manifest["status"] = "running"
        manifest["stop_after_phase"] = resolved_stop_after
        manifest["updated_at"] = datetime.now(UTC).isoformat()
        self._persist_manifest(run_dir=run_dir, manifest=manifest)

        self._publish_progress_event(
            user_id=user_id,
            payload={
                "pipeline": "x-to-demo",
                "run_id": run_id,
                "status": "run_started",
                "model": selected_model,
                "reasoning_effort": selected_reasoning_effort,
                "from_phase": resolved_start,
                "stop_after_phase": resolved_stop_after,
                "is_resume": True,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

        phase_metrics: list[PhaseCallMetrics] = []
        try:
            self._execute_phase_range(
                run_dir=run_dir,
                manifest=manifest,
                user_id=user_id,
                selected_model=selected_model,
                selected_reasoning_effort=selected_reasoning_effort,
                start_phase=resolved_start,
                stop_after_phase=resolved_stop_after,
                initial_input=initial_input,
                is_resume=True,
                phase_metrics=phase_metrics,
            )
            manifest["status"] = "completed" if resolved_stop_after == "code_spec" else "partial"
            manifest["updated_at"] = datetime.now(UTC).isoformat()
            self._append_phase_metrics(manifest, phase_metrics=phase_metrics, is_resume=True)
            self._persist_manifest(run_dir=run_dir, manifest=manifest)
            self._publish_progress_event(
                user_id=user_id,
                payload={
                    "pipeline": "x-to-demo",
                    "run_id": run_id,
                    "status": "run_completed",
                    "completed_phase_count": len(
                        [record for record in manifest["phases"] if record["status"] == "completed"]
                    ),
                    "next_phase_key": self._next_incomplete_phase(manifest),
                    "is_resume": True,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
        except Exception as exc:
            manifest["status"] = "failed"
            manifest["updated_at"] = datetime.now(UTC).isoformat()
            self._append_phase_metrics(manifest, phase_metrics=phase_metrics, is_resume=True)
            self._persist_manifest(run_dir=run_dir, manifest=manifest)
            self._publish_progress_event(
                user_id=user_id,
                payload={
                    "pipeline": "x-to-demo",
                    "run_id": run_id,
                    "status": "run_failed",
                    "error": str(exc),
                    "is_resume": True,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            raise

        return self._build_run_result(run_dir=run_dir, manifest=manifest)

    def get_run_manifest(self, *, run_id: str) -> dict[str, Any]:
        """Load persisted run manifest."""
        return self._load_manifest(self._run_dir(run_id))

    def get_run_result(self, *, run_id: str) -> PipelineRunResult:
        """Load current run state without executing additional phases."""
        run_dir = self._run_dir(run_id)
        manifest = self._load_manifest(run_dir)
        return self._build_run_result(run_dir=run_dir, manifest=manifest)

    def get_artifact(self, *, run_id: str, phase_key: PhaseKey) -> PipelineArtifact:
        """Load a specific persisted artifact."""
        run_dir = self._run_dir(run_id)
        manifest = self._load_manifest(run_dir)
        for artifact in self._load_artifacts(run_dir=run_dir, manifest=manifest):
            if artifact.phase_key == phase_key:
                return artifact
        raise FileNotFoundError(
            f"Artifact for phase '{phase_key}' was not found for run '{run_id}'"
        )

    def update_artifact(
        self,
        *,
        run_id: str,
        phase_key: PhaseKey,
        markdown: str | None,
        json_content: dict[str, Any] | None,
    ) -> PipelineArtifact:
        """Validate and persist edited artifact content, marking downstream phases stale."""
        if markdown is None and json_content is None:
            raise ValueError("Either markdown or json_content must be provided")

        phase = self._PHASES_BY_KEY[phase_key]
        run_dir = self._run_dir(run_id)
        manifest = self._load_manifest(run_dir)

        if json_content is not None:
            output_model = phase.output_model.model_validate(json_content)
        else:
            assert markdown is not None
            output_model = parse_markdown_to_model(markdown, phase.output_model)

        artifact = self._persist_phase_output(
            run_dir=run_dir,
            phase=phase,
            output_model=output_model,
        )
        self._mark_phase_completed(
            manifest=manifest,
            phase=phase,
            artifact=artifact,
            input_artifact_ref=self._previous_phase_key(phase_key),
            is_resume=True,
        )
        self._mark_downstream_stale(manifest=manifest, phase_key=phase_key)

        manifest["updated_at"] = datetime.now(UTC).isoformat()
        manifest["status"] = "partial" if self._next_incomplete_phase(manifest) else "completed"
        self._persist_manifest(run_dir=run_dir, manifest=manifest)
        return artifact

    def build_run_download_archive(self, *, run_id: str) -> bytes:
        """Build a zip archive containing all persisted artifacts and the manifest."""
        run_dir = self._run_dir(run_id)
        manifest_path = self._manifest_path(run_dir)
        if not manifest_path.exists():
            raise FileNotFoundError(f"Run '{run_id}' not found")

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(manifest_path, arcname="run-manifest.json")
            for phase in self._PHASES:
                json_path = run_dir / f"{phase.key}.json"
                md_path = run_dir / f"{phase.key}.md"
                if json_path.exists():
                    archive.write(json_path, arcname=json_path.name)
                if md_path.exists():
                    archive.write(md_path, arcname=md_path.name)
        return buffer.getvalue()

    def _validate_and_build_run_input(
        self,
        *,
        x_input: str,
        additional_context: str | None,
        feature_name_hint: str | None,
    ) -> PipelineRunInput:
        x_input_text = x_input.strip()
        if not x_input_text:
            raise ValueError("Input X cannot be empty")
        if len(x_input_text) > self.max_input_chars:
            raise ValueError(f"Input X exceeds max length ({self.max_input_chars} characters)")

        context = additional_context.strip() if additional_context else ""
        feature_hint = feature_name_hint.strip() if feature_name_hint else ""
        return PipelineRunInput(
            x_input=x_input_text,
            additional_context=context,
            feature_name_hint=feature_hint,
            feature_name=self._resolve_feature_name(
                feature_hint=feature_hint, x_input=x_input_text
            ),
        )

    @staticmethod
    def _resolve_feature_name(*, feature_hint: str, x_input: str) -> str:
        if feature_hint:
            return feature_hint[:120]
        fallback = x_input.splitlines()[0][:120].strip()
        fallback = re.sub(r"\s+", " ", fallback)
        return fallback or "Untitled Feature"

    def _resolve_model_settings(
        self,
        *,
        model: str | None,
        reasoning_effort: str | None,
    ) -> tuple[str, str]:
        selected_model = validate_model_name(model_name=model or self.model)
        if supports_reasoning(selected_model):
            selected_reasoning_effort = validate_reasoning_effort(
                model_name=selected_model,
                reasoning_effort=reasoning_effort
                or default_reasoning_effort(model_name=selected_model),
            )
        else:
            selected_reasoning_effort = "none"
        return selected_model, selected_reasoning_effort

    def _validate_phase_key(self, phase_key: str | None) -> PhaseKey:
        if phase_key is None or phase_key not in self._PHASES_BY_KEY:
            raise ValueError(
                "Unsupported phase key. Supported values: "
                + ", ".join(f"'{phase.key}'" for phase in self._PHASES)
            )
        return phase_key  # type: ignore[return-value]

    @staticmethod
    def _manifest_path(run_dir: Path) -> Path:
        return PipelineManifestManager.manifest_path(run_dir)

    def _run_dir(self, run_id: str) -> Path:
        return self.output_dir / run_id

    def _initialize_manifest(
        self,
        *,
        run_id: str,
        created_at: datetime,
        selected_model: str,
        selected_reasoning_effort: str,
        stop_after_phase: PhaseKey,
        conversation_id: str | None,
        run_input: PipelineRunInput,
    ) -> dict[str, Any]:
        return self._manifest_manager.initialize_manifest(
            run_id=run_id,
            created_at=created_at,
            selected_model=selected_model,
            selected_reasoning_effort=selected_reasoning_effort,
            stop_after_phase=stop_after_phase,
            conversation_id=conversation_id,
            run_input=run_input,
        )

    def _load_manifest(self, run_dir: Path) -> dict[str, Any]:
        return self._manifest_manager.load_manifest(run_dir)

    def _persist_manifest(self, *, run_dir: Path, manifest: dict[str, Any]) -> None:
        self._manifest_manager.persist_manifest(run_dir=run_dir, manifest=manifest)

    def _phase_record(self, manifest: dict[str, Any], phase_key: PhaseKey) -> dict[str, Any]:
        return self._manifest_manager.phase_record(manifest, phase_key)

    @staticmethod
    def _previous_phase_key(phase_key: PhaseKey) -> PhaseKey | None:
        phase_order = [phase.key for phase in PIPELINE_PHASES]
        idx = phase_order.index(phase_key)
        if idx == 0:
            return None
        return phase_order[idx - 1]

    def _mark_phase_completed(
        self,
        *,
        manifest: dict[str, Any],
        phase: PipelinePhaseDefinition,
        artifact: PipelineArtifact,
        input_artifact_ref: PhaseKey | None,
        is_resume: bool,
    ) -> None:
        self._manifest_manager.mark_phase_completed(
            manifest=manifest,
            phase=phase,
            artifact=artifact,
            input_artifact_ref=input_artifact_ref,
            is_resume=is_resume,
        )

    def _mark_phase_running(self, *, manifest: dict[str, Any], phase_key: PhaseKey) -> None:
        self._manifest_manager.mark_phase_running(manifest=manifest, phase_key=phase_key)

    def _mark_phase_failed(
        self, *, manifest: dict[str, Any], phase_key: PhaseKey, error: str
    ) -> None:
        self._manifest_manager.mark_phase_failed(
            manifest=manifest, phase_key=phase_key, error=error
        )

    def _mark_downstream_stale(self, *, manifest: dict[str, Any], phase_key: PhaseKey) -> None:
        self._manifest_manager.mark_downstream_stale(manifest=manifest, phase_key=phase_key)

    def _next_incomplete_phase(self, manifest: dict[str, Any]) -> PhaseKey | None:
        return self._manifest_manager.next_incomplete_phase(manifest)

    def _reset_phases_from(self, *, manifest: dict[str, Any], start_phase: PhaseKey) -> None:
        self._manifest_manager.reset_phases_from(manifest=manifest, start_phase=start_phase)

    def _build_resume_input(
        self,
        *,
        run_dir: Path,
        manifest: dict[str, Any],
        start_phase: PhaseKey,
    ) -> BaseModel:
        return self._manifest_manager.build_resume_input(
            run_dir=run_dir,
            manifest=manifest,
            start_phase=start_phase,
            read_json_payload=self._read_json_payload,
        )

    def _execute_phase_range(
        self,
        *,
        run_dir: Path,
        manifest: dict[str, Any],
        user_id: int,
        selected_model: str,
        selected_reasoning_effort: str,
        start_phase: PhaseKey,
        stop_after_phase: PhaseKey,
        initial_input: BaseModel,
        is_resume: bool,
        phase_metrics: list[PhaseCallMetrics],
    ) -> None:
        start_index = self._PHASE_INDEX[start_phase]
        stop_index = self._PHASE_INDEX[stop_after_phase]
        if stop_index < start_index:
            raise ValueError("stop_after_phase must be at or after start_phase")

        current_input: BaseModel = initial_input
        for index in range(start_index, stop_index + 1):
            phase = self._PHASES[index]
            if not isinstance(current_input, phase.input_model):
                raise RuntimeError(
                    f"Phase '{phase.key}' expected input model {phase.input_model.__name__}, "
                    f"received {type(current_input).__name__}"
                )

            self._mark_phase_running(manifest=manifest, phase_key=phase.key)
            manifest["updated_at"] = datetime.now(UTC).isoformat()
            self._persist_manifest(run_dir=run_dir, manifest=manifest)

            self._publish_progress_event(
                user_id=user_id,
                payload={
                    "pipeline": "x-to-demo",
                    "run_id": manifest["run_id"],
                    "status": "phase_started",
                    "phase_key": phase.key,
                    "phase_index": index + 1,
                    "is_resume": is_resume,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )

            try:
                output_model, metrics = self._run_structured_phase(
                    phase=phase,
                    phase_input=current_input,
                    model=selected_model,
                    reasoning_effort=selected_reasoning_effort,
                    conversation_id=manifest.get("conversation_id"),
                )
                phase_metrics.append(metrics)

                artifact = self._persist_phase_output(
                    run_dir=run_dir,
                    phase=phase,
                    output_model=output_model,
                )
                self._mark_phase_completed(
                    manifest=manifest,
                    phase=phase,
                    artifact=artifact,
                    input_artifact_ref=self._previous_phase_key(phase.key),
                    is_resume=is_resume,
                )
                manifest["updated_at"] = datetime.now(UTC).isoformat()
                self._persist_manifest(run_dir=run_dir, manifest=manifest)

                self._publish_progress_event(
                    user_id=user_id,
                    payload={
                        "pipeline": "x-to-demo",
                        "run_id": manifest["run_id"],
                        "status": "phase_completed",
                        "phase_key": phase.key,
                        "phase_index": index + 1,
                        "elapsed_seconds": round(metrics.elapsed_seconds, 2),
                        "model_used": metrics.model_used,
                        "response_status": metrics.status,
                        "artifact_version": artifact.content_hash,
                        "artifact_paths": {
                            "json": artifact.json_path,
                            "markdown": artifact.saved_path,
                        },
                        "is_resume": is_resume,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                )
                current_input = output_model
            except Exception as exc:
                self._mark_phase_failed(manifest=manifest, phase_key=phase.key, error=str(exc))
                manifest["updated_at"] = datetime.now(UTC).isoformat()
                self._persist_manifest(run_dir=run_dir, manifest=manifest)
                self._publish_progress_event(
                    user_id=user_id,
                    payload={
                        "pipeline": "x-to-demo",
                        "run_id": manifest["run_id"],
                        "status": "phase_failed",
                        "phase_key": phase.key,
                        "phase_index": index + 1,
                        "error": str(exc),
                        "is_resume": is_resume,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                )
                raise

    def _persist_phase_output(
        self,
        *,
        run_dir: Path,
        phase: PipelinePhaseDefinition,
        output_model: BaseModel,
    ) -> PipelineArtifact:
        return self._artifact_manager.persist_phase_output(
            run_dir=run_dir,
            phase=phase,
            output_model=output_model,
        )

    def _read_json_payload(
        self, run_dir: Path, phase_key: PhaseKey, json_path: str
    ) -> dict[str, Any]:
        return self._artifact_manager.read_json_payload(run_dir, phase_key, json_path)

    def _load_artifacts(self, *, run_dir: Path, manifest: dict[str, Any]) -> list[PipelineArtifact]:
        return self._artifact_manager.load_artifacts(run_dir=run_dir, manifest=manifest)

    def _build_run_result(self, *, run_dir: Path, manifest: dict[str, Any]) -> PipelineRunResult:
        artifacts = self._load_artifacts(run_dir=run_dir, manifest=manifest)
        code_spec_artifact = next(
            (artifact for artifact in artifacts if artifact.phase_key == "code_spec"), None
        )
        created_raw = str(manifest.get("created_at") or datetime.now(UTC).isoformat())
        created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))

        stop_after = manifest.get("stop_after_phase")
        if stop_after not in self._PHASES_BY_KEY:
            stop_after = "code_spec"

        return PipelineRunResult(
            run_id=str(manifest.get("run_id") or run_dir.name),
            created_at=created_at,
            model=str(manifest.get("model") or self.model),
            reasoning_effort=str(manifest.get("reasoning_effort") or "low"),
            stop_after_phase=stop_after,
            next_phase_key=self._next_incomplete_phase(manifest),
            artifacts=artifacts,
            final_code_spec=code_spec_artifact.markdown if code_spec_artifact else None,
            final_code_spec_path=code_spec_artifact.saved_path if code_spec_artifact else None,
            usage_totals={k: int(v) for k, v in dict(manifest.get("usage_totals") or {}).items()},
            cost_totals=self._coerce_cost_totals(manifest.get("cost_totals")),
        )

    @staticmethod
    def _coerce_cost_totals(raw: object) -> dict[str, float] | None:
        if raw is None:
            return None
        if not isinstance(raw, dict):
            return None
        return {str(key): float(value) for key, value in raw.items()}

    def _append_phase_metrics(
        self,
        manifest: dict[str, Any],
        *,
        phase_metrics: list[PhaseCallMetrics],
        is_resume: bool,
    ) -> None:
        manifest_phase_metrics = manifest.get("phase_metrics")
        if not isinstance(manifest_phase_metrics, list):
            manifest_phase_metrics = []
            manifest["phase_metrics"] = manifest_phase_metrics

        for metric in phase_metrics:
            manifest_phase_metrics.append(
                {
                    "phase_key": metric.phase_key,
                    "model_used": metric.model_used,
                    "status": metric.status,
                    "elapsed_seconds": round(metric.elapsed_seconds, 2),
                    "usage": metric.usage,
                    "cost": metric.cost,
                    "is_resume": is_resume,
                    "recorded_at": datetime.now(UTC).isoformat(),
                }
            )

        usage_totals = self._merge_usage(
            [entry.get("usage", {}) for entry in manifest_phase_metrics if isinstance(entry, dict)]
        )
        cost_totals = self._merge_costs(
            [
                entry.get("cost") if isinstance(entry, dict) else None
                for entry in manifest_phase_metrics
            ]
        )
        manifest["usage_totals"] = usage_totals
        manifest["cost_totals"] = cost_totals

    def _build_phase_prompts(
        self,
        *,
        phase: PipelinePhaseDefinition,
        phase_input: BaseModel,
    ) -> tuple[str, str]:
        return build_phase_prompts(phase=phase, phase_input=phase_input)

    @staticmethod
    def _schema_excerpt(schema_json: dict[str, Any]) -> str:
        return schema_excerpt_json(schema_json)

    @classmethod
    def _openai_compatible_schema(cls, schema_json: dict[str, Any]) -> dict[str, Any]:
        return openai_compatible_schema(schema_json)

    @classmethod
    def _enforce_no_additional_properties(cls, node: object) -> None:
        enforce_no_additional_properties(node)

    def _run_structured_phase(
        self,
        *,
        phase: PipelinePhaseDefinition,
        phase_input: BaseModel,
        model: str,
        reasoning_effort: str,
        conversation_id: str | None,
    ) -> tuple[BaseModel, PhaseCallMetrics]:
        return run_structured_phase(
            phase=phase,
            phase_input=phase_input,
            model=model,
            reasoning_effort=reasoning_effort,
            conversation_id=conversation_id,
            store_responses=self.store_responses,
            call_responses=self._call_structured_response,
            logger=logger,
        )

    def _call_structured_response(self, payload: dict[str, object], phase_key: str) -> object:
        return self._call_responses_with_progress_logs(
            payload=payload,
            phase_key=self._validate_phase_key(phase_key),
        )

    def _call_responses_with_progress_logs(
        self, *, payload: dict[str, object], phase_key: PhaseKey
    ) -> object:
        return call_responses_with_progress_logs(
            create_call=self.responses_client.responses.create,
            payload=payload,
            phase_key=phase_key,
            response_wait_log_interval_seconds=self.response_wait_log_interval_seconds,
            default_model=self.model,
            executor_cls=ThreadPoolExecutor,
            logger=logger,
        )

    def _create_conversation_id(self, *, run_id: str, user_id: int) -> str | None:
        return create_conversation_id(
            responses_client=self.responses_client,
            run_id=run_id,
            user_id=user_id,
        )

    def _publish_progress_event(self, *, user_id: int, payload: dict[str, Any]) -> None:
        publish_progress_event(
            user_id=user_id,
            payload=payload,
            logger=logger,
            publish_call=pubsub.publish,
            on_done=self._on_publish_progress_event_done,
        )

    @staticmethod
    def _on_publish_progress_event_done(task: asyncio.Task[int]) -> None:
        try:
            task.result()
        except Exception:
            logger.warning("Failed to publish X-to-Demo progress event", exc_info=True)

    @staticmethod
    def _extract_output_text(response: object) -> str:
        return extract_output_text(response)

    @staticmethod
    def _response_to_dict(response: object) -> dict[str, Any]:
        return response_to_dict(response)

    @classmethod
    def _extract_usage(cls, response: object) -> dict[str, int]:
        return extract_usage(response)

    @classmethod
    def _extract_model(cls, response: object) -> str | None:
        return extract_model(response)

    @classmethod
    def _extract_status(cls, response: object) -> str:
        return extract_status(response)

    @classmethod
    def _extract_structured_payload(cls, response: object) -> dict[str, Any]:
        return extract_structured_payload(response)

    @staticmethod
    def _parse_price(value: str) -> float | None:
        return parse_price(value)

    @staticmethod
    def _normalize_model_for_pricing(model_name: str, pricing_keys: list[str]) -> str | None:
        return normalize_model_for_pricing(model_name, pricing_keys)

    @classmethod
    def _load_pricing_table(cls, path: Path = PRICING_PATH) -> dict[str, dict[str, float | None]]:
        return load_pricing_table(path)

    @classmethod
    def _estimate_cost(cls, *, model_name: str, usage: dict[str, int]) -> dict[str, float] | None:
        return estimate_cost(model_name=model_name, usage=usage)

    @staticmethod
    def _merge_usage(usages: list[dict[str, int] | object]) -> dict[str, int]:
        return merge_usage(usages)

    @staticmethod
    def _merge_costs(costs: list[dict[str, float] | None]) -> dict[str, float] | None:
        return merge_costs(costs)

    @staticmethod
    def _relative_or_absolute(path: Path) -> str:
        return PipelineArtifactManager.relative_or_absolute(path)


def _build_openai_client(api_key: str) -> object:
    """Build OpenAI client lazily so tests can run without the package installed."""
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "openai package is not installed. Add dependency and reinstall API environment."
        ) from exc
    return OpenAI(api_key=api_key)


def get_x_to_demo_pipeline_service() -> XToDemoPipelineService:
    """Dependency provider for X-to-Demo pipeline service."""
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    output_dir = Path(settings.x_to_demo_output_dir)
    client = _build_openai_client(settings.openai_api_key)
    return XToDemoPipelineService(
        responses_client=client,
        model=settings.x_to_demo_model,
        output_dir=output_dir,
        store_responses=False,
        max_input_chars=settings.x_to_demo_max_input_chars,
        response_wait_log_interval_seconds=15.0,
    )
