"""X-to-Demo orchestration service implemented with OpenAI Responses API."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from textwrap import dedent
from typing import Any, ClassVar
from uuid import uuid4

from app.config import settings
from app.pubsub import pubsub
from app.schemas import SSEEvent
from app.services.model_capabilities import (
    default_reasoning_effort,
    supports_reasoning,
    validate_model_name,
    validate_reasoning_effort,
)

logger = logging.getLogger(__name__)
PRICING_PATH = Path(__file__).resolve().parents[2] / "openai_model_pricing.md"
_PRICING_CACHE: dict[str, dict[str, float | None]] | None = None


@dataclass(frozen=True)
class PipelineArtifact:
    """Single phase output generated during a pipeline run."""

    phase_key: str
    title: str
    markdown: str
    saved_path: str


@dataclass(frozen=True)
class PipelineRunResult:
    """Aggregate result for one completed pipeline run."""

    run_id: str
    created_at: datetime
    model: str
    reasoning_effort: str
    artifacts: list[PipelineArtifact]
    final_code_spec: str
    final_code_spec_path: str
    usage_totals: dict[str, int]
    cost_totals: dict[str, float] | None


@dataclass(frozen=True)
class PhaseCallMetrics:
    """Token/cost metadata collected for a single phase call."""

    phase_key: str
    model_used: str
    usage: dict[str, int]
    cost: dict[str, float] | None
    elapsed_seconds: float
    status: str


class XToDemoPipelineService:
    """Runs the three-phase X-to-Demo pipeline with chained prompts."""

    _PHASE_TITLES: ClassVar[dict[str, str]] = {
        "phase-1-input-to-feature-spec": "Phase 1: Input -> SDD Feature Spec",
        "phase-2-feature-spec-to-demo-spec": "Phase 2: Feature Spec -> Demo Spec",
        "phase-3-demo-spec-to-code-spec": "Phase 3: Demo Spec -> Code Spec",
    }
    _COMMON_SPEC_KEYS: ClassVar[tuple[str, ...]] = (
        "schema_version",
        "feature_name",
        "status",
        "source",
    )
    _PHASE_SPEC_REQUIRED_KEYS: ClassVar[dict[str, tuple[str, ...]]] = {
        "phase-1-input-to-feature-spec": (
            "intent",
            "external_behavior",
            "acceptance_criteria",
            "invariants",
            "success_metrics",
            "versioning",
        ),
        "phase-2-feature-spec-to-demo-spec": (
            "demo_overview",
            "demo_scope",
            "demo_format",
            "core_flow_steps",
            "success_signals",
            "example_copy",
        ),
        "phase-3-demo-spec-to-code-spec": (
            "demo_overview",
            "tech_stack",
            "project_changes",
            "components",
            "state_model",
            "ai_seam",
            "acceptance_tests",
            "non_goals",
        ),
    }
    _REQUIRED_WRAPPER_HEADINGS: ClassVar[tuple[str, ...]] = (
        "## Summary",
        "## Spec (JSON)",
        "## Details (Markdown)",
        "## Version",
    )
    # Optional: "## Open Questions" — plan says "only if applicable"; model may omit when none.
    _BANNED_OUTPUT_PATTERNS: ClassVar[tuple[re.Pattern[str], ...]] = (
        re.compile(r"^\s*##\s+Stakeholder Personas\b", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^\s*##\s+Dialogic Convergence\b", re.IGNORECASE | re.MULTILINE),
        re.compile(
            r"simulate\s+3\s*(?:-|to)\s*5[\w\s-]*stakeholders?",
            re.IGNORECASE,
        ),
    )

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

    def run(
        self,
        *,
        x_input: str,
        additional_context: str | None,
        feature_name_hint: str | None,
        user_id: int,
        model: str | None = None,
        reasoning_effort: str | None = None,
    ) -> PipelineRunResult:
        """Execute all pipeline phases and persist artifacts."""
        x_input_text = x_input.strip()
        if not x_input_text:
            raise ValueError("Input X cannot be empty")
        if len(x_input_text) > self.max_input_chars:
            raise ValueError(f"Input X exceeds max length ({self.max_input_chars} characters)")

        context = additional_context.strip() if additional_context else ""
        feature_hint = feature_name_hint.strip() if feature_name_hint else ""
        selected_model = validate_model_name(model_name=model or self.model)
        if supports_reasoning(selected_model):
            selected_reasoning_effort = validate_reasoning_effort(
                model_name=selected_model,
                reasoning_effort=reasoning_effort
                or default_reasoning_effort(model_name=selected_model),
            )
        else:
            selected_reasoning_effort = "none"

        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + f"-{uuid4().hex[:8]}"
        created_at = datetime.now(UTC)
        logger.info(
            "Starting X-to-Demo pipeline run",
            extra={
                "run_id": run_id,
                "user_id": user_id,
                "model": selected_model,
                "reasoning_effort": selected_reasoning_effort,
                "input_chars": len(x_input_text),
            },
        )

        run_dir = self.output_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        conversation_id = self._create_conversation_id(run_id=run_id, user_id=user_id)

        phase_metrics: list[PhaseCallMetrics] = []
        self._publish_progress_event(
            user_id=user_id,
            payload={
                "pipeline": "x-to-demo",
                "run_id": run_id,
                "status": "run_started",
                "model": selected_model,
                "reasoning_effort": selected_reasoning_effort,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

        def run_phase_with_progress(
            *,
            phase_key: str,
            phase_index: int,
            developer_prompt: str,
            user_prompt: str,
        ) -> tuple[str, PhaseCallMetrics]:
            self._publish_progress_event(
                user_id=user_id,
                payload={
                    "pipeline": "x-to-demo",
                    "run_id": run_id,
                    "status": "phase_started",
                    "phase_key": phase_key,
                    "phase_index": phase_index,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            try:
                output, metrics = self._run_phase(
                    phase_key=phase_key,
                    conversation_id=conversation_id,
                    developer_prompt=developer_prompt,
                    user_prompt=user_prompt,
                    model=selected_model,
                    reasoning_effort=selected_reasoning_effort,
                )
                output = self._normalize_phase_output_start(markdown=output, phase_key=phase_key)
                output = self._ensure_version_heading(output)
                self._validate_phase_output(phase_key=phase_key, markdown=output)
            except Exception as exc:
                self._publish_progress_event(
                    user_id=user_id,
                    payload={
                        "pipeline": "x-to-demo",
                        "run_id": run_id,
                        "status": "phase_failed",
                        "phase_key": phase_key,
                        "phase_index": phase_index,
                        "error": str(exc),
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                )
                raise

            self._publish_progress_event(
                user_id=user_id,
                payload={
                    "pipeline": "x-to-demo",
                    "run_id": run_id,
                    "status": "phase_completed",
                    "phase_key": phase_key,
                    "phase_index": phase_index,
                    "elapsed_seconds": round(metrics.elapsed_seconds, 2),
                    "model_used": metrics.model_used,
                    "response_status": metrics.status,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            return output, metrics

        try:
            feature_spec, feature_spec_metrics = run_phase_with_progress(
                phase_key="phase-1-input-to-feature-spec",
                phase_index=1,
                developer_prompt=self._phase_2_developer_prompt(),
                user_prompt=self._phase_2_user_prompt(
                    x_input_text=x_input_text,
                    additional_context=context,
                    feature_name_hint=feature_hint,
                ),
            )
            phase_metrics.append(feature_spec_metrics)
            demo_spec, demo_spec_metrics = run_phase_with_progress(
                phase_key="phase-2-feature-spec-to-demo-spec",
                phase_index=2,
                developer_prompt=self._phase_3_developer_prompt(),
                user_prompt=self._phase_3_user_prompt(
                    behavioural_spec=feature_spec,
                    feature_name_hint=feature_hint,
                ),
            )
            phase_metrics.append(demo_spec_metrics)
            code_spec, code_spec_metrics = run_phase_with_progress(
                phase_key="phase-3-demo-spec-to-code-spec",
                phase_index=3,
                developer_prompt=self._phase_4_developer_prompt(),
                user_prompt=self._phase_4_user_prompt(
                    demo_slice_spec=demo_spec,
                    feature_name_hint=feature_hint,
                ),
            )
            phase_metrics.append(code_spec_metrics)
            usage_totals = self._merge_usage([metrics.usage for metrics in phase_metrics])
            cost_totals = self._merge_costs([metrics.cost for metrics in phase_metrics])

            phase_records = [
                (
                    "phase-1-input-to-feature-spec",
                    self._PHASE_TITLES["phase-1-input-to-feature-spec"],
                    feature_spec,
                ),
                (
                    "phase-2-feature-spec-to-demo-spec",
                    self._PHASE_TITLES["phase-2-feature-spec-to-demo-spec"],
                    demo_spec,
                ),
                (
                    "phase-3-demo-spec-to-code-spec",
                    self._PHASE_TITLES["phase-3-demo-spec-to-code-spec"],
                    code_spec,
                ),
            ]

            artifacts: list[PipelineArtifact] = []
            for index, (phase_key, title, markdown) in enumerate(phase_records, start=1):
                filename = f"{index:02d}-{phase_key}.md"
                saved_path = self._save_markdown(
                    run_dir=run_dir, filename=filename, markdown=markdown
                )
                artifacts.append(
                    PipelineArtifact(
                        phase_key=phase_key,
                        title=title,
                        markdown=markdown,
                        saved_path=saved_path,
                    )
                )

            manifest_path = run_dir / "run-manifest.json"
            manifest_payload = {
                "run_id": run_id,
                "created_at": created_at.isoformat(),
                "model": selected_model,
                "reasoning_effort": selected_reasoning_effort,
                "conversation_id": conversation_id,
                "feature_name_hint": feature_hint or None,
                "usage_totals": usage_totals,
                "cost_totals": cost_totals,
                "phase_metrics": [
                    {
                        "phase_key": metrics.phase_key,
                        "model_used": metrics.model_used,
                        "status": metrics.status,
                        "elapsed_seconds": round(metrics.elapsed_seconds, 2),
                        "usage": metrics.usage,
                        "cost": metrics.cost,
                    }
                    for metrics in phase_metrics
                ],
                "artifacts": [
                    {
                        "phase_key": artifact.phase_key,
                        "title": artifact.title,
                        "saved_path": artifact.saved_path,
                    }
                    for artifact in artifacts
                ],
            }
            manifest_path.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")
            logger.info(
                "Completed X-to-Demo pipeline run",
                extra={
                    "run_id": run_id,
                    "model": selected_model,
                    "reasoning_effort": selected_reasoning_effort,
                    "input_tokens": usage_totals.get("input_tokens", 0),
                    "output_tokens": usage_totals.get("output_tokens", 0),
                    "total_tokens": usage_totals.get("total_tokens", 0),
                    "total_cost_usd": (
                        round(float(cost_totals["total_cost"]), 6)
                        if cost_totals and cost_totals.get("total_cost") is not None
                        else None
                    ),
                },
            )
            self._publish_progress_event(
                user_id=user_id,
                payload={
                    "pipeline": "x-to-demo",
                    "run_id": run_id,
                    "status": "run_completed",
                    "completed_phase_count": len(phase_metrics),
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )

            final_code_spec = artifacts[-1].markdown
            final_code_spec_path = artifacts[-1].saved_path
            return PipelineRunResult(
                run_id=run_id,
                created_at=created_at,
                model=selected_model,
                reasoning_effort=selected_reasoning_effort,
                artifacts=artifacts,
                final_code_spec=final_code_spec,
                final_code_spec_path=final_code_spec_path,
                usage_totals=usage_totals,
                cost_totals=cost_totals,
            )
        except Exception as exc:
            self._publish_progress_event(
                user_id=user_id,
                payload={
                    "pipeline": "x-to-demo",
                    "run_id": run_id,
                    "status": "run_failed",
                    "completed_phase_count": len(phase_metrics),
                    "error": str(exc),
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            raise

    def _run_phase(
        self,
        *,
        phase_key: str,
        conversation_id: str | None,
        developer_prompt: str,
        user_prompt: str,
        model: str,
        reasoning_effort: str,
    ) -> tuple[str, PhaseCallMetrics]:
        logger.info(
            "Starting X-to-Demo phase",
            extra={
                "phase_key": phase_key,
                "model": model,
                "reasoning_effort": reasoning_effort,
            },
        )
        started_at = datetime.now(UTC)
        payload: dict[str, object] = {
            "model": model,
            "store": self.store_responses,
            "input": [
                {"role": "developer", "content": developer_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if supports_reasoning(model):
            payload["reasoning"] = {"effort": reasoning_effort}
        if conversation_id:
            payload["conversation"] = conversation_id

        response = self._call_responses_with_progress_logs(payload=payload, phase_key=phase_key)
        output_text = self._extract_output_text(response)
        if not output_text:
            raise RuntimeError("Responses API returned an empty output")
        usage = self._extract_usage(response)
        model_used = self._extract_model(response) or model
        cost = self._estimate_cost(model_name=model_used, usage=usage) if usage else None
        status = self._extract_status(response)
        elapsed_seconds = max(
            (datetime.now(UTC) - started_at).total_seconds(),
            0.0,
        )

        if cost and cost.get("total_cost") is not None:
            logger.info(
                "OpenAI phase call cost",
                extra={
                    "phase_key": phase_key,
                    "model": model_used,
                    "elapsed_seconds": round(elapsed_seconds, 2),
                    "total_cost_usd": round(float(cost["total_cost"]), 6),
                    "input_cost_usd": round(float(cost.get("input_cost", 0.0)), 6),
                    "cached_input_cost_usd": round(float(cost.get("cached_input_cost", 0.0)), 6),
                    "output_cost_usd": round(float(cost.get("output_cost", 0.0)), 6),
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "reasoning_tokens": usage.get("reasoning_tokens", 0),
                    "cached_input_tokens": usage.get("cached_input_tokens", 0),
                },
            )
        else:
            logger.info(
                "OpenAI phase call cost unavailable",
                extra={
                    "phase_key": phase_key,
                    "model": model_used,
                    "elapsed_seconds": round(elapsed_seconds, 2),
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "reasoning_tokens": usage.get("reasoning_tokens", 0),
                    "cached_input_tokens": usage.get("cached_input_tokens", 0),
                },
            )
        logger.info(
            "Completed X-to-Demo phase",
            extra={
                "phase_key": phase_key,
                "model": model_used,
                "status": status,
                "elapsed_seconds": round(elapsed_seconds, 2),
            },
        )
        return output_text, PhaseCallMetrics(
            phase_key=phase_key,
            model_used=model_used,
            usage=usage,
            cost=cost,
            elapsed_seconds=elapsed_seconds,
            status=status,
        )

    def _call_responses_with_progress_logs(
        self, *, payload: dict[str, object], phase_key: str
    ) -> object:
        start_time = datetime.now(UTC)
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.responses_client.responses.create, **payload)
            elapsed_seconds = 0.0
            while True:
                try:
                    return future.result(timeout=self.response_wait_log_interval_seconds)
                except FutureTimeoutError:
                    elapsed_seconds += self.response_wait_log_interval_seconds
                    logger.info(
                        "Awaiting OpenAI response",
                        extra={
                            "phase_key": phase_key,
                            "model": str(payload.get("model", self.model)),
                            "elapsed_seconds": int(elapsed_seconds),
                            "started_at": start_time.isoformat(),
                        },
                    )

    def _create_conversation_id(self, *, run_id: str, user_id: int) -> str | None:
        conversations_api = getattr(self.responses_client, "conversations", None)
        if conversations_api is None:
            return None

        try:
            conversation = conversations_api.create(
                metadata={
                    "pipeline": "x-to-demo",
                    "run_id": run_id,
                    "user_id": str(user_id),
                }
            )
        except Exception:
            return None

        if isinstance(conversation, dict):
            raw_id = conversation.get("id")
        else:
            raw_id = getattr(conversation, "id", None)
        return str(raw_id) if raw_id else None

    def _publish_progress_event(self, *, user_id: int, payload: dict[str, Any]) -> None:
        event = SSEEvent(event="x_to_demo_run_progress", data=payload)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                asyncio.run(pubsub.publish(event, user_id=user_id))
            except Exception:
                logger.warning(
                    "Failed to publish X-to-Demo progress event",
                    extra={"event_name": event.event, "run_id": payload.get("run_id")},
                    exc_info=True,
                )
            return

        try:
            publish_task = loop.create_task(pubsub.publish(event, user_id=user_id))
            publish_task.add_done_callback(self._on_publish_progress_event_done)
        except Exception:
            logger.warning(
                "Failed to schedule X-to-Demo progress event",
                extra={"event_name": event.event, "run_id": payload.get("run_id")},
                exc_info=True,
            )

    @staticmethod
    def _on_publish_progress_event_done(task: asyncio.Task[int]) -> None:
        try:
            task.result()
        except Exception:
            logger.warning("Failed to publish X-to-Demo progress event", exc_info=True)

    @staticmethod
    def _extract_output_text(response: object) -> str:
        """Extract output text from polymorphic Responses API payloads."""
        direct_output_text = getattr(response, "output_text", None)
        if isinstance(direct_output_text, str) and direct_output_text.strip():
            return direct_output_text.strip()

        payload = response
        if hasattr(response, "model_dump"):
            payload = response.model_dump()

        if not isinstance(payload, dict):
            return ""

        output_text = payload.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        chunks: list[str] = []
        output_items = payload.get("output", [])
        if not isinstance(output_items, list):
            return ""

        for item in output_items:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "message":
                continue
            content = item.get("content", [])
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                block_text = block.get("text")
                if isinstance(block_text, str) and block_text.strip():
                    chunks.append(block_text.strip())

        return "\n\n".join(chunks).strip()

    @staticmethod
    def _response_to_dict(response: object) -> dict[str, Any]:
        if isinstance(response, dict):
            return response
        if hasattr(response, "model_dump"):
            return response.model_dump()
        if hasattr(response, "to_dict"):
            return response.to_dict()
        if hasattr(response, "json"):
            try:
                payload = json.loads(response.json())
                return payload if isinstance(payload, dict) else {}
            except Exception:
                return {}
        return {}

    @classmethod
    def _extract_usage(cls, response: object) -> dict[str, int]:
        usage = getattr(response, "usage", None)
        if usage is None:
            usage = cls._response_to_dict(response).get("usage")
        if usage is None:
            return {}

        if isinstance(usage, dict):
            details = usage.get("input_tokens_details") or {}
            cached = details.get("cached_tokens")
            if cached is None:
                cached = usage.get("cached_input_tokens")
            return {
                "input_tokens": int(usage.get("input_tokens", 0) or 0),
                "output_tokens": int(usage.get("output_tokens", 0) or 0),
                "total_tokens": int(usage.get("total_tokens", 0) or 0),
                "reasoning_tokens": int(usage.get("reasoning_tokens", 0) or 0),
                "cached_input_tokens": int(cached or 0),
            }

        details = getattr(usage, "input_tokens_details", None)
        cached = getattr(details, "cached_tokens", None) if details else None
        if cached is None:
            cached = getattr(usage, "cached_input_tokens", None)
        return {
            "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
            "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
            "reasoning_tokens": int(getattr(usage, "reasoning_tokens", 0) or 0),
            "cached_input_tokens": int(cached or 0),
        }

    @classmethod
    def _extract_model(cls, response: object) -> str | None:
        model_used = getattr(response, "model", None)
        if isinstance(model_used, str) and model_used:
            return model_used
        payload_model = cls._response_to_dict(response).get("model")
        return payload_model if isinstance(payload_model, str) and payload_model else None

    @classmethod
    def _extract_status(cls, response: object) -> str:
        status = getattr(response, "status", None)
        if isinstance(status, str) and status:
            return status
        payload_status = cls._response_to_dict(response).get("status")
        if isinstance(payload_status, str) and payload_status:
            return payload_status
        return "completed"

    @staticmethod
    def _parse_price(value: str) -> float | None:
        stripped = value.strip()
        if not stripped or stripped == "-":
            return None
        if stripped.startswith("$"):
            stripped = stripped[1:]
        try:
            return float(stripped)
        except ValueError:
            return None

    @staticmethod
    def _normalize_model_for_pricing(model_name: str, pricing_keys: list[str]) -> str | None:
        model_lower = model_name.lower()
        key_map = {key.lower(): key for key in pricing_keys}
        if model_lower in key_map:
            return key_map[model_lower]
        best: str | None = None
        for key in pricing_keys:
            lowered = key.lower()
            if not model_lower.startswith(lowered):
                continue
            if len(model_lower) > len(lowered):
                next_char = model_lower[len(lowered)]
                if next_char not in ("-", ":", "@"):
                    continue
            if best is None or len(key) > len(best):
                best = key
        return best

    @classmethod
    def _load_pricing_table(cls, path: Path = PRICING_PATH) -> dict[str, dict[str, float | None]]:
        global _PRICING_CACHE
        if _PRICING_CACHE is not None:
            return _PRICING_CACHE

        pricing: dict[str, dict[str, float | None]] = {}
        if not path.exists():
            _PRICING_CACHE = pricing
            return pricing

        lines = path.read_text(encoding="utf-8").splitlines()
        header_index: int | None = None
        for index, line in enumerate(lines):
            if line.strip() == "|Model|Input|Cached input|Output|":
                header_index = index
                break
        if header_index is None:
            _PRICING_CACHE = pricing
            return pricing

        for line in lines[header_index + 2 :]:
            if not line.strip().startswith("|"):
                break
            parts = [part.strip() for part in line.strip().strip("|").split("|")]
            if len(parts) != 4:
                continue
            model, input_price, cached_price, output_price = parts
            pricing[model] = {
                "input": cls._parse_price(input_price),
                "cached_input": cls._parse_price(cached_price),
                "output": cls._parse_price(output_price),
            }

        _PRICING_CACHE = pricing
        return pricing

    @classmethod
    def _estimate_cost(cls, *, model_name: str, usage: dict[str, int]) -> dict[str, float] | None:
        pricing = cls._load_pricing_table()
        pricing_key = cls._normalize_model_for_pricing(model_name, list(pricing.keys()))
        if not pricing_key:
            return None
        rates = pricing.get(pricing_key)
        if not rates:
            return None

        input_rate = rates.get("input")
        output_rate = rates.get("output")
        cached_rate = rates.get("cached_input") or input_rate
        if input_rate is None or output_rate is None or cached_rate is None:
            return None

        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)
        cached_tokens = int(usage.get("cached_input_tokens", 0) or 0)
        uncached_tokens = max(input_tokens - cached_tokens, 0)

        input_cost = (uncached_tokens / 1_000_000) * input_rate
        cached_cost = (cached_tokens / 1_000_000) * cached_rate
        output_cost = (output_tokens / 1_000_000) * output_rate
        total_cost = input_cost + cached_cost + output_cost
        return {
            "input_cost": input_cost,
            "cached_input_cost": cached_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
        }

    @staticmethod
    def _merge_usage(usages: list[dict[str, int]]) -> dict[str, int]:
        merged: dict[str, int] = {}
        for usage in usages:
            for key, value in usage.items():
                merged[key] = merged.get(key, 0) + int(value)
        return merged

    @staticmethod
    def _merge_costs(costs: list[dict[str, float] | None]) -> dict[str, float] | None:
        merged: dict[str, float] = {}
        any_cost = False
        for cost in costs:
            if cost is None:
                continue
            any_cost = True
            for key, value in cost.items():
                merged[key] = merged.get(key, 0.0) + float(value)
        return merged if any_cost else None

    def _save_markdown(self, *, run_dir: Path, filename: str, markdown: str) -> str:
        path = run_dir / filename
        path.write_text(markdown.strip() + "\n", encoding="utf-8")
        return self._relative_or_absolute(path)

    @staticmethod
    def _relative_or_absolute(path: Path) -> str:
        cwd = Path.cwd()
        try:
            return str(path.relative_to(cwd))
        except ValueError:
            return str(path)

    @classmethod
    def _normalize_phase_output_start(cls, *, markdown: str, phase_key: str) -> str:
        """Trim preamble and normalize close heading variants to the required phase heading."""
        phase_title = cls._PHASE_TITLES.get(phase_key)
        if phase_title is None:
            return markdown
        expected_prefix = f"# {phase_title}:"
        lines = markdown.splitlines()
        title_prefix = f"# {phase_title}"

        # Ideal case: trim any preamble and keep from the exact required heading onward.
        for i, line in enumerate(lines):
            if line.strip().startswith(expected_prefix):
                return "\n".join(lines[i:]) if i > 0 else markdown

        # Recovery case: model wrote the phase title without the exact `: <Feature Name>` shape.
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped.startswith(title_prefix):
                continue
            remainder = stripped[len(title_prefix) :].strip()
            feature_name = remainder[1:].strip() if remainder.startswith((":", "-")) else ""
            if not feature_name:
                feature_name = "Untitled Feature"
            normalized_heading = f"{expected_prefix} {feature_name}"
            normalized_lines = lines[i:]
            normalized_lines[0] = normalized_heading
            return "\n".join(normalized_lines)
        return markdown

    @staticmethod
    def _ensure_version_heading(markdown: str) -> str:
        """If markdown lacks '## Version', append a minimal section so validation passes."""
        if "## Version" in markdown:
            return markdown
        ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        return markdown.rstrip() + "\n\n## Version\n\nv0.1, draft, " + ts + "\n"

    @classmethod
    def _validate_phase_output(cls, *, phase_key: str, markdown: str) -> None:
        phase_title = cls._PHASE_TITLES.get(phase_key)
        if phase_title is None:
            logger.warning("Unknown phase key '%s'", phase_key)
            return

        first_line = next((line.strip() for line in markdown.splitlines() if line.strip()), "")
        expected_prefix = f"# {phase_title}:"
        if not first_line.startswith(expected_prefix):
            logger.warning(
                "%s output must begin with '%s <Feature Name>'",
                phase_key,
                expected_prefix,
            )

        for heading in cls._REQUIRED_WRAPPER_HEADINGS:
            if heading not in markdown:
                logger.warning("%s output missing required heading '%s'", phase_key, heading)

        for pattern in cls._BANNED_OUTPUT_PATTERNS:
            if pattern.search(markdown):
                logger.warning(
                    "%s output includes banned stakeholder-simulation content",
                    phase_key,
                )

        spec_payload = cls._extract_spec_payload(markdown=markdown, phase_key=phase_key)
        if spec_payload is None:
            logger.warning(
                "%s: could not extract spec payload; skipping spec key checks", phase_key
            )
            return

        missing_common = [key for key in cls._COMMON_SPEC_KEYS if key not in spec_payload]
        if missing_common:
            missing_text = ", ".join(missing_common)
            logger.warning(
                "%s JSON spec missing required top-level keys: %s",
                phase_key,
                missing_text,
            )

        source = spec_payload.get("source")
        if not isinstance(source, dict):
            logger.warning("%s JSON spec key 'source' must be an object", phase_key)

        status = spec_payload.get("status")
        if status not in {"draft", "review", "ready"}:
            logger.warning(
                "%s JSON spec key 'status' must be one of: draft, review, ready",
                phase_key,
            )

        required_phase_keys = cls._PHASE_SPEC_REQUIRED_KEYS.get(phase_key, ())
        missing_phase_keys = [key for key in required_phase_keys if key not in spec_payload]
        if missing_phase_keys:
            missing_text = ", ".join(missing_phase_keys)
            logger.warning(
                "%s JSON spec missing required phase keys: %s",
                phase_key,
                missing_text,
            )

    @classmethod
    def _normalize_phase3_spec_payload(cls, payload: dict[str, Any]) -> dict[str, Any]:
        """Promote phase-3 required keys from a nested object to top level if present."""
        required = cls._PHASE_SPEC_REQUIRED_KEYS.get("phase-3-demo-spec-to-code-spec", ())
        missing = [k for k in required if k not in payload]
        if not missing:
            return payload
        for key in ("spec", "code_spec", "code_spec_section"):
            nested = payload.get(key)
            if isinstance(nested, dict) and all(k in nested for k in missing):
                for k in missing:
                    payload[k] = nested[k]
                break
        return payload

    @classmethod
    def _extract_spec_payload(cls, *, markdown: str, phase_key: str) -> dict[str, Any] | None:
        all_json_blocks = re.findall(
            r"```json\s*(.*?)\s*```",
            markdown,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not all_json_blocks:
            logger.warning(
                "%s output has no fenced json code block; cannot extract spec payload",
                phase_key,
            )
            return None
        if len(all_json_blocks) != 1:
            logger.warning(
                "%s output must contain exactly one fenced json code block (found %d); using first",
                phase_key,
                len(all_json_blocks),
            )

        section_match = re.search(r"^## Spec \(JSON\)\s*$", markdown, flags=re.MULTILINE)
        if section_match is None:
            logger.warning("%s output missing '## Spec (JSON)' section", phase_key)
            raw_block = all_json_blocks[0]
        else:
            tail = markdown[section_match.end() :]
            next_section_match = re.search(r"^##\s+", tail, flags=re.MULTILINE)
            spec_section = tail[: next_section_match.start()] if next_section_match else tail
            section_json_blocks = re.findall(
                r"```json\s*(.*?)\s*```",
                spec_section,
                flags=re.IGNORECASE | re.DOTALL,
            )
            if len(section_json_blocks) != 1:
                logger.warning(
                    "%s '## Spec (JSON)' section must contain exactly one json block (found %d); using first available",
                    phase_key,
                    len(section_json_blocks),
                )
            raw_block = section_json_blocks[0] if section_json_blocks else all_json_blocks[0]

        try:
            payload = json.loads(raw_block)
        except json.JSONDecodeError as exc:
            logger.warning("%s JSON spec block is not valid JSON: %s", phase_key, exc)
            return None
        if not isinstance(payload, dict):
            logger.warning("%s JSON spec block must decode to an object", phase_key)
            return None

        # Phase 3: accept nested spec (e.g. under "spec" or "code_spec") by promoting to top level
        if phase_key == "phase-3-demo-spec-to-code-spec":
            payload = cls._normalize_phase3_spec_payload(payload)
        return payload

    @staticmethod
    def _phase_1_developer_prompt() -> str:
        return dedent(
            """
            You are Phase 1 of the X-to-Demo pipeline: Input Digest & Problem Frame.
            Objective: convert raw Input X into a concise, problem-first framing that downstream
            phases can treat as the source of truth for intent, constraints, and unknowns.

            Principles (SDD-ready mindset):
            - Intent before implementation: define why this exists and what outcome is desired,
              before any talk of how to build it.
            - Behavioral clarity: write falsifiable statements (inputs/constraints/unknowns),
              not vague narrative.
            - Specs are the source of truth: distinguish what is stated in Input X vs inferred
              vs assumed.
            - Structured, machine-interpretable format: follow the wrapper headings + JSON
              contract exactly.
            - Explicit constraints & invariants: record "MUST / MUST NOT" rules and boundaries.
            - Testability by construction: open questions should be answerable with specific
              follow-ups (not "it depends" hand-waving).
            - Metrics & measurable outcomes: when possible, name 1-3 measurable indicators of
              success; otherwise turn missing metrics into explicit open questions.
            - Separation of experience, policy, implementation: keep (a) user-visible behaviour,
              (b) business rules, and (c) implementation assumptions clearly distinct.

            Hard rules:
            - Input X may be any type (transcript, PRD, notes, tickets, email, docs, unknown).
            - Preserve uncertainty and conflicts; never pretend unknowns are facts.
            - Do not simulate stakeholders, personas, or convergence rounds.
            - Do not design solution architecture, user flows, or UI details.
            - Keep output concrete, machine-checkable, and compact.
            """
        ).strip()

    @staticmethod
    def _phase_1_user_prompt(
        *, x_input_text: str, additional_context: str, feature_name_hint: str
    ) -> str:
        feature_hint_line = feature_name_hint or "None provided. Infer from Input X."
        context_block = additional_context if additional_context else "None provided."
        return dedent(
            f"""
            Produce the required Phase 1 artifact from the following inputs.

            ## Feature naming hint (optional)
            {feature_hint_line}

            ## Input X (raw material)
            ```text
            {x_input_text}
            ```

            ## Optional context
            ```text
            {context_block}
            ```

            Output format (exact section order):
            # Phase 1: Input Digest & Problem Frame: <Feature Name or Unknown>
            ## Summary
            ## Spec (JSON)
            ## Details (Markdown)
            ## Open Questions
            ## Version

            The `## Spec (JSON)` section must contain exactly one fenced `json` block and no
            other JSON block anywhere else in the markdown.

            Required JSON keys:
            - schema_version (string, use "0.1")
            - feature_name (string or null; use the hint if provided, but treat it as a hint)
            - status (draft|review|ready)
            - source (object with x_source_type, inputs, notes)
              - x_source_type: one of transcript|prd|notes|ticket|email|docs|unknown
              - inputs: array of strings (include "x_input"; include "additional_context" if provided)
              - notes: explain any major ambiguity, contradictions, and how you interpreted the input
            - primary_problem (object)
              - statement: "Users cannot <do X> when <context>, causing <impact>."
              - why_it_matters: user impact + business impact (time/cost/risk), in plain language
              - who_is_struggling: array of roles (strings). If unsure, include but add an assumption.
            - secondary_problems (array of 0-5 objects)
              - statement
              - why_it_matters
              - who_is_struggling (optional)
            - affected_roles (array of strings)
            - assumptions (array of strings; prefix with "ASSUMPTION (confidence: low|medium|high): ...")
            - constraints (array of strings; prefer "MUST / MUST NOT" phrasing)
            - open_questions (array of strings; prefix blockers with "BLOCKER:")

            Additional requirements:
            - Keep `status` as "draft" unless the input explicitly indicates otherwise.
            - If the feature naming hint conflicts with Input X, keep `feature_name` as the best
              guess but record the conflict in `source.notes` and add an open question.
            - In `## Summary`, include: inferred feature name, primary problem, top constraints, and
              the 3 most important open questions (max 10 bullets total).
            - In `## Details (Markdown)`, include short subsections:
              - Evidence (1-5 verbatim excerpts from Input X, short)
              - Interpretations (what you inferred vs what was explicit)
              - Success metrics (hypotheses; measurable if possible)
              - Experience vs policy vs implementation notes (bulleted, compact)
              - Constraints & invariants (human-readable)
              - Risks / failure modes (what could go wrong if assumptions are false)
            - Explicitly list ambiguity, contradiction, and missing information.
            - In `## Version`, use: `v0.1 | status: <status> | timestamp_utc: <ISO-8601>`
            """
        ).strip()

    @staticmethod
    def _phase_2_developer_prompt() -> str:
        return dedent(
            """
            You are Phase 1 of the X-to-Demo pipeline: Input -> SDD Feature Spec.
            Objective: produce one SDD-ready feature spec that becomes the source of truth for
            intent + observable behaviour + testability.

            Note: Phase 1 and Phase 2 are merged in this pipeline version (digest/problem frame
            + feature spec in one artifact).

            Principles to follow (SDD-ready feature spec):
            - Intent before implementation: clearly state the user outcome, business objective,
              and the problem being solved before any "how".
            - Behavioral clarity over narrative ambiguity: define observable behaviours with
              explicit inputs/outputs, preconditions/postconditions, and error states.
            - Spec as the source of truth: separate what is explicit in Input X vs inferred
              vs assumed; do not invent requirements.
            - Structured, machine-interpretable format: comply with wrapper headings + JSON
              contract exactly.
            - Explicit constraints & invariants: write rules in "MUST / MUST NOT" terms.
            - Iterative, living document: capture key decisions and assumptions in versioning and
              keep open questions explicit so the spec can evolve without rewriting history.
            - Shared cross-functional artifact: keep language readable to product/design/engineering.
            - Testability by construction: acceptance criteria must be directly convertible into
              tests without interpretation; avoid subjective adjectives.
            - Metrics & measurable outcomes: define what "done" means beyond "it works".
            - Separation of experience, policy, and implementation: keep user-visible behaviour,
              business rules, and implementation assumptions distinct.

            Hard rules:
            - No stakeholder simulation, personas, or convergence rounds.
            - Behaviour over implementation: no architecture, internal module layout, or visual
              design detail unless essential to make behaviour testable in the demo.
            - Do not introduce new product ideas. Use only Input X + optional context, plus clearly
              labelled assumptions.
            - Preserve unresolved ambiguity as explicit Open Questions.
            - If implementation and spec conflict, spec wins.
            """
        ).strip()

    @staticmethod
    def _phase_2_user_prompt(
        *,
        x_input_text: str,
        additional_context: str,
        feature_name_hint: str,
    ) -> str:
        feature_hint_line = feature_name_hint or "None provided. Infer from Input X."
        context_block = additional_context if additional_context else "None provided."
        return dedent(
            f"""
            Build Phase 1 output using:

            ## Feature naming hint
            {feature_hint_line}

            ## Raw Input X (for traceability)
            ```text
            {x_input_text}
            ```

            ## Optional context
            ```text
            {context_block}
            ```

            Output format:
            # Phase 1: Input -> SDD Feature Spec: <Feature Name>
            ## Summary
            ## Spec (JSON)
            ## Details (Markdown)
            ## Open Questions
            ## Version

            The `## Spec (JSON)` section must contain exactly one fenced `json` block and no
            other JSON block anywhere else in the markdown.

            Required JSON keys:
            - schema_version (string, use "0.1")
            - feature_name (string; use hint if plausible, otherwise infer and note conflict)
            - status (draft|review|ready; default to "draft")
            - source (object with x_source_type, inputs, notes)
              - x_source_type: transcript|prd|notes|ticket|email|docs|unknown
              - inputs: array of strings (include "x_input"; include "additional_context" if provided)
              - notes: list contradictions, missing info, and key assumptions
            - intent (object: problem, objective, desired_outcome, target_persona)
              - problem: plain-language statement of what is broken today
              - objective: what the feature is trying to achieve (business + user)
              - desired_outcome: what changes for the user when it works
              - target_persona: primary role (string); you may add secondary_personas (array)
            - external_behavior (object: inputs, outputs, states, errors)
              - inputs: include validation rules and preconditions (strings or small objects)
              - outputs: include postconditions / observable effects
              - states: named states and what they mean
              - errors: named, actionable, testable error states
            - acceptance_criteria (array of Given/When/Then objects: given, when, then[])
              - Include: happy path, at least 2 failure paths, and at least 1 edge case.
              - Ensure every "then" clause is objectively observable.
            - invariants (array of strings; "MUST / MUST NOT" rules that always hold)
            - success_metrics (array of strings; measurable where possible; include at least 1
              user metric + 1 business metric + 1 quality metric)
            - versioning (object with version, changelog; start at version "0.1.0")
              - changelog should include key spec decisions and assumptions (not just dates)

            Additional requirements:
            - This phase merges "problem framing" and "feature spec" into a single artifact:
              do a brief digest first (problem, affected roles, assumptions, constraints, unknowns),
              then express the end-to-end behaviour spec.
            - Keep the spec demo-appropriate: include only what is necessary to demonstrate the
              moment-of-value; explicitly defer non-demo scope into Open Questions or notes.
            - Avoid architecture. If you must reference interfaces, express them as external
              contracts (inputs/outputs) not internal components.
            - Separate in `## Details (Markdown)`:
              - Evidence & interpretations (what was explicit vs inferred)
              - Experience (user-visible behaviour)
              - Policy (business rules, constraints)
              - Implementation assumptions (only what is needed for a demo)
            - In `## Summary`, include max 10 bullets: intent, moment-of-value, top behaviours,
              top constraints, top risks.
            - In `## Open Questions`, list questions as either "BLOCKER:" or "NON-BLOCKER:".
            - In `## Version`, use: `v0.1 | status: <status> | timestamp_utc: <ISO-8601>`
            """
        ).strip()

    @staticmethod
    def _phase_3_developer_prompt() -> str:
        return dedent(
            """
            You are Phase 2 of the X-to-Demo pipeline: Feature Spec -> Demo Spec.

            Role: product designer creating a demo specification from a behavioural feature spec.
            Objective: transform the spec into a simple, minimal demo plan that clearly demonstrates
            the core intended behaviour of the feature — not its full production scope.

            Principles to follow:
            - Focus on clarity over completeness.
            - Show the happy path that best exemplifies the feature's value.
            - Prefer mocked data and scripted interactions over real integrations.
            - Optimise for explainability: a viewer should immediately understand what the feature
              does and why it matters.
            - Do not replicate the structure or wording of the original spec. Abstract the intent.

            What to extract from the spec:
            - The primary user intent the feature serves.
            - The minimum set of behaviours required to demonstrate that intent.
            - Any critical constraints or boundaries that shape the interaction.
            - The moment of value where the feature “clicks” for the user.

            Hard rules:
            - No stakeholder simulation, personas, or convergence rounds.
            - Do not introduce new product ideas, requirements, or scope not grounded in the spec.
            - Keep the demo intentionally small: 5-7 core flow steps.
            - Default to mocked data and scripted interactions unless the spec explicitly requires
              otherwise.
            - Avoid technical implementation detail (APIs, databases, libraries, architectures).
            - Explicitly separate in-scope vs out-of-scope.
            - Do your reasoning privately; output only the required sections and JSON.
            """
        ).strip()

    @staticmethod
    def _phase_3_user_prompt(*, behavioural_spec: str, feature_name_hint: str) -> str:
        feature_hint_line = feature_name_hint or "Infer from behavioural feature spec."
        return dedent(
            f"""
            Produce Phase 2 Demo Spec from this behavioural spec.

            ## Feature naming hint
            {feature_hint_line}

            ## Behavioural Feature Spec
            ```markdown
            {behavioural_spec}
            ```

            Guidance:
            - This is a demo slice, not an MVP. Choose one narrow flow that proves the feature works.
            - Keep the core flow to 5-7 steps and aim for a single, obvious moment-of-value.
            - Assume all data is mocked unless the spec explicitly says otherwise.
            - Avoid edge cases, variants, and deep configuration; capture them in out-of-scope.
            - Avoid technical implementation details; describe observable behaviour and copy only.

            Output format:
            The first line of your response must be exactly:
            # Phase 2: Feature Spec -> Demo Spec: <Feature Name>
            (with a concrete feature name; no preamble or other text before this line.)
            Then the following sections:
            ## Summary
            ## Spec (JSON)
            ## Details (Markdown)
            ## Open Questions
            ## Version

            The `## Spec (JSON)` section must contain exactly one fenced `json` block and no
            other JSON block anywhere else in the markdown.

            Required JSON keys:
            - schema_version (string, use "0.1")
            - feature_name (string)
            - status (draft|review|ready; default to "draft")
            - source (object; cite that input came from Phase 1 behavioural spec)
            - demo_overview (string; short paragraph describing what the demo shows and what
              problem it proves can be solved)
            - demo_scope (object with in_scope, out_of_scope arrays; be explicit about what is and
              is not shown)
            - demo_format (string; how the demo is presented: scripted walkthrough, prototype
              screens, clickable flow, mocked responses, etc.)
            - core_flow_steps (array of 5-7 steps; each step should map to a key capability being
              demonstrated, from entry to outcome)
            - success_signals (array; observable conditions that must be true for the demo to be
              considered successful)
            - example_copy (array; minimal, representative user + system copy to make behaviour
              concrete; avoid edge cases or variants)

            Additional requirements:
            - Keep core flow to 5-7 steps (no more, no less unless the spec is truly tiny).
            - Prioritise one moment-of-value and a clear happy path.
            - Keep language neutral and stakeholder-friendly.
            """
        ).strip()

    @staticmethod
    def _phase_4_developer_prompt() -> str:
        return dedent(
            """
            You are Phase 3 of the X-to-Demo pipeline: Demo Spec -> Code Spec.
            You are a spec transformer. Translate the demo slice spec into an implementation-ready
            "coding agent build spec" that a coding agent can execute to produce a runnable prototype.

            Primary goal:
            - Deliver a minimal, executable demo that proves the demo slice's moment-of-value.

            Hard rules:
            - No stakeholder simulation, personas, or convergence rounds.
            - Do not ask clarifying questions. If something is unclear, make the smallest reasonable
              assumption and label it clearly as an assumption.
            - Preserve any provided copy verbatim (unless explicitly asked to rewrite it).
            - Convert vague vibes into concrete requirements and acceptance checks.
            - Bias toward minimal executable implementation.
            - Treat AI as a first-class dependency: mocked in implementation, but with explicit contracts.
            - Assume frontend-only demo with mocked/in-memory state by default.
            - Include low-confidence and human review checkpoints.
            - Treat documentation as definition-of-done.
            - Be explicit enough for a literal coding agent to execute without clarification.
            - Do not expand product scope beyond the demo slice.
            - Keep logic deterministic unless the demo explicitly requires randomness.
            - If diagrams are provided, translate them into a state machine or routing plan.
            - If brand rules conflict with accessibility, note the conflict and propose the closest
              accessible alternative.

            Implementation defaults (unless the demo spec says otherwise):
            - Target this repo's stack: Next.js/React (apps/web) for UI, mocked/in-memory state.
            - Only introduce backend work (apps/api) if strictly required by the demo slice.
            """
        ).strip()

    @staticmethod
    def _phase_4_user_prompt(*, demo_slice_spec: str, feature_name_hint: str) -> str:
        feature_hint_line = feature_name_hint or "Infer from demo slice spec."
        return dedent(
            f"""
            Produce the final Phase 3 artifact: a Code Spec / Coding Prompt derived from the demo spec.
            This must be detailed enough for a coding agent to implement a runnable prototype without
            any follow-up questions.

            ## Feature naming hint
            {feature_hint_line}

            ## Demo Slice Spec
            ```markdown
            {demo_slice_spec}
            ```

            Output format:
            # Phase 3: Demo Spec -> Code Spec: <Feature Name>
            ## Summary
            ## Spec (JSON)
            ## Details (Markdown)
            ## Open Questions
            ## Version

            The `## Spec (JSON)` section must contain exactly one fenced `json` block and no
            other JSON block anywhere else in the markdown.

            Required JSON keys:
            - schema_version (string, use "0.1")
            - feature_name (string)
            - status (draft|review|ready; default to "draft")
            - source (object; cite that input came from Phase 2 demo spec + note any ambiguity)
            - demo_overview (string; keep short and consistent with the demo slice)
            - tech_stack (object; if not specified, choose a reasonable default and label it as a choice)
            - project_changes (array; concrete list of files/modules to add/update with brief intent)
            - components (array; concrete UI/modules to build with responsibilities)
            - state_model (object; minimal state shape + enums + validation rules)
            - ai_seam (object with schemas, contracts, mock_strategy; always present even if “mock only”)
            - acceptance_tests (array of objects: given, when, then[])
            - non_goals (array; mirror demo out-of-scope + any explicit build exclusions)

            Additional requirements:
            - Acceptance tests must be derivable from the demo slice core flow steps and success signals.
            - Include at least one recovery path (error, empty state, or user correction).
            - If the spec includes AI confidence, extraction, or classification, include a low-confidence
              handling + human review path.
            - Documentation deliverables must include a README quick start section with
              prerequisites, install, environment setup, run, test, and troubleshooting steps.

            Build spec requirements (in `## Details (Markdown)`):
            - Write a single “coding agent build spec” with the following sections in this order,
              using `###` headings:
              1. Project goal
              2. Non-goals
              3. Assumptions
              4. User journey
              5. Screen/step requirements
              6. State and data model
              7. Mock data
              8. Mock services / business logic
              9. UI/brand requirements
              10. Implementation plan
              11. Acceptance test checklist
            - For each screen/step, include: name, purpose, inputs (defaults), outputs, scripted copy
              (verbatim if provided), success checks (testable), edge cases (back/edit/skip), and UI components.
            - Keep code blocks short (no code blocks longer than ~30 lines); prefer pseudo-types and concise examples.
            """
        ).strip()


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
        store_responses=settings.x_to_demo_store_responses,
        max_input_chars=settings.x_to_demo_max_input_chars,
        response_wait_log_interval_seconds=settings.x_to_demo_response_wait_log_interval_seconds,
    )
