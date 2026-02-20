"""Manifest persistence and phase-state transitions for X-to-Demo runs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from .models import (
    PIPELINE_PHASES,
    PhaseKey,
    PipelineArtifact,
    PipelinePhaseDefinition,
    PipelineRunInput,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from pydantic import BaseModel


class PipelineManifestManager:
    """Encapsulates run manifest lifecycle and phase bookkeeping."""

    def __init__(self, phases: tuple[PipelinePhaseDefinition, ...] = PIPELINE_PHASES) -> None:
        self._phases = phases
        self._phases_by_key: dict[PhaseKey, PipelinePhaseDefinition] = {
            phase.key: phase for phase in phases
        }
        self._phase_index: dict[PhaseKey, int] = {
            phase.key: index for index, phase in enumerate(phases)
        }

    @property
    def phases(self) -> tuple[PipelinePhaseDefinition, ...]:
        return self._phases

    @property
    def phases_by_key(self) -> dict[PhaseKey, PipelinePhaseDefinition]:
        return self._phases_by_key

    @property
    def phase_index(self) -> dict[PhaseKey, int]:
        return self._phase_index

    @staticmethod
    def manifest_path(run_dir: Path) -> Path:
        return run_dir / "run-manifest.json"

    def initialize_manifest(
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
        phase_records: list[dict[str, Any]] = []
        for index, phase in enumerate(self._phases):
            phase_records.append(
                {
                    "phase_key": phase.key,
                    "title": phase.title,
                    "order": index,
                    "status": "pending",
                    "input_artifact_ref": self.previous_phase_key(phase.key),
                    "output_json_path": None,
                    "output_xml_path": None,
                    "output_md_path": None,
                    "content_hash": None,
                    "error": None,
                    "completed_at": None,
                    "is_resume": False,
                }
            )

        created_iso = created_at.isoformat()
        return {
            "run_id": run_id,
            "created_at": created_iso,
            "updated_at": created_iso,
            "status": "running",
            "model": selected_model,
            "reasoning_effort": selected_reasoning_effort,
            "stop_after_phase": stop_after_phase,
            "conversation_id": conversation_id,
            "input": run_input.model_dump(mode="json"),
            "phase_metrics": [],
            "usage_totals": {},
            "cost_totals": None,
            "phases": phase_records,
        }

    def load_manifest(self, run_dir: Path) -> dict[str, Any]:
        manifest_path = self.manifest_path(run_dir)
        if not manifest_path.exists():
            raise FileNotFoundError(f"Run '{run_dir.name}' not found")
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise RuntimeError("Run manifest is invalid")
        return data

    def persist_manifest(self, *, run_dir: Path, manifest: dict[str, Any]) -> None:
        self.manifest_path(run_dir).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def phase_record(self, manifest: dict[str, Any], phase_key: PhaseKey) -> dict[str, Any]:
        phases = manifest.get("phases", [])
        for record in phases:
            if isinstance(record, dict) and record.get("phase_key") == phase_key:
                return record
        raise RuntimeError(f"Manifest missing phase record for '{phase_key}'")

    def previous_phase_key(self, phase_key: PhaseKey) -> PhaseKey | None:
        idx = self._phase_index[phase_key]
        if idx == 0:
            return None
        return self._phases[idx - 1].key

    def mark_phase_completed(
        self,
        *,
        manifest: dict[str, Any],
        phase: PipelinePhaseDefinition,
        artifact: PipelineArtifact,
        input_artifact_ref: PhaseKey | None,
        is_resume: bool,
    ) -> None:
        record = self.phase_record(manifest, phase.key)
        record["status"] = "completed"
        record["input_artifact_ref"] = input_artifact_ref
        record["output_json_path"] = artifact.json_path
        record["output_xml_path"] = artifact.xml_path
        record["output_md_path"] = artifact.saved_path
        record["content_hash"] = artifact.content_hash
        record["error"] = None
        record["completed_at"] = datetime.now(UTC).isoformat()
        record["is_resume"] = is_resume

    def mark_phase_running(self, *, manifest: dict[str, Any], phase_key: PhaseKey) -> None:
        record = self.phase_record(manifest, phase_key)
        record["status"] = "running"
        record["error"] = None
        record["completed_at"] = None

    def mark_phase_failed(
        self, *, manifest: dict[str, Any], phase_key: PhaseKey, error: str
    ) -> None:
        record = self.phase_record(manifest, phase_key)
        record["status"] = "failed"
        record["error"] = error
        record["completed_at"] = datetime.now(UTC).isoformat()

    def mark_downstream_stale(self, *, manifest: dict[str, Any], phase_key: PhaseKey) -> None:
        edited_index = self._phase_index[phase_key]
        for phase in self._phases[edited_index + 1 :]:
            record = self.phase_record(manifest, phase.key)
            if record.get("status") in {"completed", "pending", "stale", "failed"}:
                record["status"] = "stale"
                record["error"] = "Upstream artifact changed; phase requires resume"

    def next_incomplete_phase(self, manifest: dict[str, Any]) -> PhaseKey | None:
        for phase in self._phases:
            record = self.phase_record(manifest, phase.key)
            status = str(record.get("status") or "pending")
            if status != "completed":
                return phase.key
        return None

    def reset_phases_from(self, *, manifest: dict[str, Any], start_phase: PhaseKey) -> None:
        start_index = self._phase_index[start_phase]
        for phase in self._phases[start_index:]:
            record = self.phase_record(manifest, phase.key)
            record["status"] = "pending"
            record["output_json_path"] = None
            record["output_xml_path"] = None
            record["output_md_path"] = None
            record["content_hash"] = None
            record["error"] = None
            record["completed_at"] = None

    def build_resume_input(
        self,
        *,
        run_dir: Path,
        manifest: dict[str, Any],
        start_phase: PhaseKey,
        read_json_payload: Callable[[Path, PhaseKey, str], dict[str, Any]],
    ) -> BaseModel:
        if start_phase == "feature_spec":
            run_input_payload = manifest.get("input")
            if not isinstance(run_input_payload, dict):
                raise RuntimeError("Manifest input payload is missing or invalid")
            return PipelineRunInput.model_validate(run_input_payload)

        previous_phase_key = self.previous_phase_key(start_phase)
        if previous_phase_key is None:
            raise RuntimeError("Cannot resolve resume input for first phase")

        previous_phase = self._phases_by_key[previous_phase_key]
        record = self.phase_record(manifest, previous_phase_key)
        if record.get("status") != "completed":
            raise ValueError(
                f"Cannot resume from '{start_phase}' because prior phase '{previous_phase_key}' is not completed"
            )

        json_path = record.get("output_json_path")
        if not isinstance(json_path, str) or not json_path:
            raise RuntimeError(
                f"Manifest missing JSON output path for phase '{previous_phase_key}'"
            )

        payload = read_json_payload(run_dir, previous_phase_key, json_path)
        return previous_phase.output_model.model_validate(payload)
