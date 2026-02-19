"""Unit tests for X-to-Demo typed pipeline service."""

from __future__ import annotations

import json
import logging
from concurrent.futures import TimeoutError as FutureTimeoutError
from types import SimpleNamespace

import pytest

from app.services.x_to_demo_pipeline import XToDemoPipelineService


class _FakeResponse:
    def __init__(
        self,
        *,
        output_text: str,
        usage: dict[str, int],
        model: str = "gpt-5.1",
        status: str = "completed",
    ) -> None:
        self.output_text = output_text
        self.usage = usage
        self.model = model
        self.status = status


class _FakeResponsesAPI:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = responses
        self.requests: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        return self._responses.pop(0)


class _FakeClient:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self.responses = _FakeResponsesAPI(responses)


def _build_service(*, output_dir, responses: list[_FakeResponse]) -> XToDemoPipelineService:
    return XToDemoPipelineService(
        responses_client=_FakeClient(responses),
        model="gpt-5.1",
        output_dir=output_dir,
        store_responses=False,
        max_input_chars=60000,
        response_wait_log_interval_seconds=0.01,
    )


def _feature_spec_payload(feature_name: str = "Test Feature") -> dict[str, object]:
    return {
        "schema_version": "0.1",
        "feature_name": feature_name,
        "status": "draft",
        "source": {
            "x_source_type": "notes",
            "inputs": ["x_input", "additional_context"],
            "notes": "Synthetic payload for tests.",
        },
        "intent": {
            "problem": "Messy input causes ambiguous delivery intent.",
            "objective": "Create an SDD-ready behaviour spec.",
            "desired_outcome": "Consistent, testable feature handoff.",
            "target_persona": "Product manager",
        },
        "external_behavior": {
            "inputs": ["x_input", "additional_context"],
            "outputs": ["feature_spec_markdown", "feature_spec_json"],
            "states": ["draft", "review", "ready"],
            "errors": ["input_too_vague", "conflicting_constraints"],
        },
        "acceptance_criteria": [
            {
                "given": "Input X includes conflicting notes.",
                "when": "Phase 1 runs.",
                "then": [
                    "The feature spec labels conflicts explicitly.",
                    "Acceptance criteria remain testable.",
                ],
            }
        ],
        "invariants": ["Spec-first behaviour over implementation details."],
        "success_metrics": ["Required keys present in output JSON."],
        "versioning": {
            "version": "0.1.0",
            "changelog": ["Initial draft"],
            "updated_at_utc": "2026-02-12T12:00:00Z",
        },
    }


def _demo_spec_payload(feature_name: str = "Test Feature") -> dict[str, object]:
    return {
        "schema_version": "0.1",
        "feature_name": feature_name,
        "status": "draft",
        "source": {
            "x_source_type": "feature_spec",
            "inputs": ["feature_spec"],
            "notes": "Derived from phase 1.",
        },
        "demo_overview": "Minimal demo proving the moment of value.",
        "demo_scope": {
            "in_scope": ["Happy path flow", "Mocked extraction results"],
            "out_of_scope": ["Production data integrations"],
        },
        "demo_format": "Scripted prototype walkthrough",
        "core_flow_steps": [
            "Paste Input X",
            "Generate digest",
            "Inspect feature intent",
            "Run demo flow",
            "Confirm success signals",
        ],
        "success_signals": [
            "User sees a clear problem frame within one minute.",
            "Demo flow finishes without external services.",
        ],
        "example_copy": [
            "User: Turn these notes into a demo plan.",
            "System: Here is the feature intent and core demo flow.",
        ],
    }


def _code_spec_payload(feature_name: str = "Test Feature") -> dict[str, object]:
    return {
        "schema_version": "0.1",
        "feature_name": feature_name,
        "status": "draft",
        "source": {
            "x_source_type": "demo_spec",
            "inputs": ["demo_spec"],
            "notes": "Derived from phase 2.",
        },
        "demo_overview": "Runnable frontend-only demo from the demo spec.",
        "tech_stack": {
            "frontend": "Next.js",
            "backend": "FastAPI",
            "language": "TypeScript",
        },
        "project_changes": ["apps/web/components/XToDemoStudio.tsx"],
        "components": ["InputXEditor", "PhaseTimeline", "CodeSpecPanel"],
        "state_model": {"fields": ["xInput", "phaseStatus", "artifacts"]},
        "ai_seam": {
            "schemas": ["PhaseOutput"],
            "contracts": ["runPhase(input) -> output"],
            "mock_strategy": "Deterministic fixtures",
        },
        "acceptance_tests": [
            {
                "given": "Input X is provided.",
                "when": "The pipeline runs.",
                "then": [
                    "Artifacts are rendered for each phase.",
                    "Low-confidence states are surfaced for review.",
                ],
            }
        ],
        "non_goals": ["Production integrations", "Authentication redesign"],
    }


def test_extract_usage_handles_object_payload() -> None:
    usage_obj = SimpleNamespace(
        input_tokens=120,
        output_tokens=30,
        total_tokens=150,
        reasoning_tokens=7,
        input_tokens_details=SimpleNamespace(cached_tokens=20),
    )
    response = SimpleNamespace(usage=usage_obj)

    usage = XToDemoPipelineService._extract_usage(response)

    assert usage == {
        "input_tokens": 120,
        "output_tokens": 30,
        "total_tokens": 150,
        "reasoning_tokens": 7,
        "cached_input_tokens": 20,
    }


def test_openai_compatible_schema_sets_additional_properties_false_recursively() -> None:
    raw_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "nested": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer"},
                },
            },
            "choices": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"label": {"type": "string"}},
                },
            },
        },
        "$defs": {
            "meta": {
                "type": "object",
                "properties": {"ok": {"type": "boolean"}},
            }
        },
    }

    normalized = XToDemoPipelineService._openai_compatible_schema(raw_schema)
    assert normalized["additionalProperties"] is False
    assert normalized["properties"]["nested"]["additionalProperties"] is False
    assert normalized["properties"]["choices"]["items"]["additionalProperties"] is False
    assert normalized["$defs"]["meta"]["additionalProperties"] is False

    # OpenAI Responses API requires: required must include every key in properties
    assert set(normalized["required"]) == {"name", "nested", "choices"}
    assert set(normalized["properties"]["nested"]["required"]) == {"count"}
    assert set(normalized["properties"]["choices"]["items"]["required"]) == {"label"}
    assert set(normalized["$defs"]["meta"]["required"]) == {"ok"}


def test_openai_compatible_schema_strips_keywords_from_refs() -> None:
    """$ref cannot have sibling keywords like description."""
    raw_schema = {
        "type": "object",
        "properties": {
            "source": {
                "$ref": "#/$defs/SourceInfo",
                "description": "Source and provenance metadata.",
            },
        },
        "required": ["source"],
        "$defs": {
            "SourceInfo": {
                "type": "object",
                "properties": {"x": {"type": "string"}},
                "required": ["x"],
            }
        },
    }
    normalized = XToDemoPipelineService._openai_compatible_schema(raw_schema)
    assert normalized["properties"]["source"] == {"$ref": "#/$defs/SourceInfo"}
    assert "description" not in normalized["properties"]["source"]


def test_wait_logging_reports_progress_at_intervals(monkeypatch, caplog, tmp_path) -> None:
    class _FakeFuture:
        def __init__(self, response: _FakeResponse) -> None:
            self._response = response
            self._calls = 0

        def result(self, *, timeout: float):
            self._calls += 1
            assert timeout > 0
            if self._calls == 1:
                raise FutureTimeoutError()
            return self._response

    class _FakeExecutor:
        def __init__(self, *, max_workers: int) -> None:
            self.max_workers = max_workers

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn, **kwargs):
            return _FakeFuture(fn(**kwargs))

    monkeypatch.setattr(
        "app.services.x_to_demo_pipeline.ThreadPoolExecutor",
        _FakeExecutor,
    )

    service = _build_service(
        output_dir=tmp_path,
        responses=[
            _FakeResponse(
                output_text=json.dumps(_feature_spec_payload()),
                usage={"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
            )
        ],
    )

    with caplog.at_level(logging.INFO, logger="app.services.x_to_demo_pipeline"):
        response = service._call_responses_with_progress_logs(
            payload={"model": "gpt-5", "input": [], "store": False},
            phase_key="feature_spec",
        )

    assert isinstance(response, _FakeResponse)
    progress_records = [
        record for record in caplog.records if record.message == "Awaiting OpenAI response"
    ]
    assert progress_records
    assert progress_records[0].elapsed_seconds == 0


def test_run_writes_manifest_with_json_and_markdown_artifacts(tmp_path) -> None:
    responses = [
        _FakeResponse(
            output_text=json.dumps(_feature_spec_payload()),
            usage={
                "input_tokens": 1000,
                "output_tokens": 200,
                "total_tokens": 1200,
                "cached_input_tokens": 100,
            },
        ),
        _FakeResponse(
            output_text=json.dumps(_demo_spec_payload()),
            usage={
                "input_tokens": 900,
                "output_tokens": 220,
                "total_tokens": 1120,
                "cached_input_tokens": 90,
            },
        ),
        _FakeResponse(
            output_text=json.dumps(_code_spec_payload()),
            usage={
                "input_tokens": 800,
                "output_tokens": 260,
                "total_tokens": 1060,
                "cached_input_tokens": 80,
            },
        ),
    ]
    service = _build_service(output_dir=tmp_path, responses=responses)

    result = service.run(
        x_input="This input is long enough for validation and runs all phases end-to-end.",
        additional_context="Keep scope narrow.",
        feature_name_hint="Test Feature",
        user_id=7,
    )

    assert result.stop_after_phase == "code_spec"
    assert result.next_phase_key is None
    assert len(result.artifacts) == 3
    assert result.final_code_spec is not None
    assert result.final_code_spec_path is not None

    run_dir = tmp_path / result.run_id
    assert (run_dir / "feature_spec.json").exists()
    assert (run_dir / "feature_spec.md").exists()
    assert (run_dir / "demo_spec.json").exists()
    assert (run_dir / "demo_spec.md").exists()
    assert (run_dir / "code_spec.json").exists()
    assert (run_dir / "code_spec.md").exists()

    manifest = json.loads((run_dir / "run-manifest.json").read_text(encoding="utf-8"))
    assert manifest["usage_totals"]["input_tokens"] == 2700
    assert manifest["cost_totals"]["total_cost"] > 0
    assert len(manifest["phase_metrics"]) == 3
    assert manifest["stop_after_phase"] == "code_spec"


def test_run_supports_partial_execution_and_resume(tmp_path) -> None:
    service = _build_service(
        output_dir=tmp_path,
        responses=[
            _FakeResponse(
                output_text=json.dumps(_feature_spec_payload()),
                usage={"input_tokens": 10, "output_tokens": 3, "total_tokens": 13},
            ),
            _FakeResponse(
                output_text=json.dumps(_demo_spec_payload()),
                usage={"input_tokens": 11, "output_tokens": 4, "total_tokens": 15},
            ),
            _FakeResponse(
                output_text=json.dumps(_code_spec_payload()),
                usage={"input_tokens": 12, "output_tokens": 5, "total_tokens": 17},
            ),
        ],
    )

    partial = service.run(
        x_input="This input is long enough for validation and runs all phases end-to-end.",
        additional_context=None,
        feature_name_hint="Test Feature",
        user_id=7,
        stop_after_phase="demo_spec",
    )

    assert partial.stop_after_phase == "demo_spec"
    assert partial.next_phase_key == "code_spec"
    assert partial.final_code_spec is None
    assert len(partial.artifacts) == 2

    resumed = service.resume(run_id=partial.run_id, user_id=7)

    assert resumed.next_phase_key is None
    assert resumed.final_code_spec is not None
    assert len(resumed.artifacts) == 3


def test_update_artifact_marks_downstream_phase_stale(tmp_path) -> None:
    service = _build_service(
        output_dir=tmp_path,
        responses=[
            _FakeResponse(
                output_text=json.dumps(_feature_spec_payload()),
                usage={"input_tokens": 10, "output_tokens": 3, "total_tokens": 13},
            ),
            _FakeResponse(
                output_text=json.dumps(_demo_spec_payload()),
                usage={"input_tokens": 11, "output_tokens": 4, "total_tokens": 15},
            ),
            _FakeResponse(
                output_text=json.dumps(_code_spec_payload()),
                usage={"input_tokens": 12, "output_tokens": 5, "total_tokens": 17},
            ),
        ],
    )

    initial = service.run(
        x_input="This input is long enough for validation and runs all phases end-to-end.",
        additional_context=None,
        feature_name_hint="Test Feature",
        user_id=7,
    )

    updated_demo = _demo_spec_payload()
    updated_demo["demo_overview"] = "Edited overview"
    artifact = service.update_artifact(
        run_id=initial.run_id,
        phase_key="demo_spec",
        markdown=None,
        json_content=updated_demo,
    )

    assert artifact.phase_key == "demo_spec"
    assert artifact.json_content["demo_overview"] == "Edited overview"

    manifest = service.get_run_manifest(run_id=initial.run_id)
    phase_status = {phase["phase_key"]: phase["status"] for phase in manifest["phases"]}
    assert phase_status["demo_spec"] == "completed"
    assert phase_status["code_spec"] == "stale"


def test_run_supports_gpt_52_reasoning_options(tmp_path) -> None:
    service = _build_service(
        output_dir=tmp_path,
        responses=[
            _FakeResponse(
                output_text=json.dumps(_feature_spec_payload()),
                usage={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
                model="gpt-5.2",
            ),
            _FakeResponse(
                output_text=json.dumps(_demo_spec_payload()),
                usage={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
                model="gpt-5.2",
            ),
            _FakeResponse(
                output_text=json.dumps(_code_spec_payload()),
                usage={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
                model="gpt-5.2",
            ),
        ],
    )

    result = service.run(
        x_input="This input is long enough for validation and runs all phases end-to-end.",
        additional_context=None,
        feature_name_hint=None,
        user_id=11,
        model="gpt-5.2",
        reasoning_effort="xhigh",
    )

    assert result.model == "gpt-5.2"
    assert result.reasoning_effort == "xhigh"
    assert service.responses_client.responses.requests[0]["reasoning"] == {"effort": "xhigh"}


def test_run_rejects_invalid_reasoning_for_selected_model(tmp_path) -> None:
    service = _build_service(
        output_dir=tmp_path,
        responses=[
            _FakeResponse(
                output_text=json.dumps(_feature_spec_payload()),
                usage={"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
            )
        ]
        * 3,
    )

    with pytest.raises(
        ValueError,
        match=r"Unsupported reasoning effort 'minimal' for model 'gpt-5\.2'",
    ):
        service.run(
            x_input=("This input is long enough for validation and runs all phases end-to-end."),
            additional_context=None,
            feature_name_hint=None,
            user_id=5,
            model="gpt-5.2",
            reasoning_effort="minimal",
        )
