"""Unit tests for X-to-Demo pipeline service LLM logging and token/cost tracking."""

from __future__ import annotations

import json
import logging
from concurrent.futures import TimeoutError as FutureTimeoutError
from types import SimpleNamespace

import pytest

from app.services.x_to_demo_pipeline import XToDemoPipelineService

_PHASE_KEYS = [
    "phase-1-input-to-feature-spec",
    "phase-2-feature-spec-to-demo-spec",
    "phase-3-demo-spec-to-code-spec",
]


class _FakeResponse:
    def __init__(
        self,
        *,
        output_text: str,
        usage: dict[str, int],
        model: str = "gpt-5",
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


def _phase_spec_payload(phase_key: str) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "0.1",
        "feature_name": "Test Feature",
        "status": "draft",
        "source": {
            "x_source_type": "notes",
            "inputs": ["x_input", "additional_context"],
            "notes": "Synthetic payload for tests.",
        },
    }
    if phase_key == "phase-1-input-to-feature-spec":
        payload.update(
            {
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
                "versioning": {"version": "0.1.0", "changelog": ["Initial draft"]},
            }
        )
        return payload

    if phase_key == "phase-2-feature-spec-to-demo-spec":
        payload.update(
            {
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
        )
        return payload

    if phase_key == "phase-3-demo-spec-to-code-spec":
        payload.update(
            {
                "demo_overview": "Runnable frontend-only demo from the demo spec.",
                "tech_stack": {"frontend": "Next.js", "language": "TypeScript"},
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
        )
        return payload

    raise ValueError(f"Unknown phase key: {phase_key}")


def _build_phase_markdown(phase_key: str) -> str:
    title = XToDemoPipelineService._PHASE_TITLES[phase_key]
    payload = _phase_spec_payload(phase_key)
    return (
        f"# {title}: Test Feature\n"
        "## Summary\n"
        "- Concise summary bullet.\n\n"
        "## Spec (JSON)\n"
        "```json\n"
        f"{json.dumps(payload, indent=2)}\n"
        "```\n\n"
        "## Details (Markdown)\n"
        "- Behaviour-first detail.\n\n"
        "## Open Questions\n"
        "- None.\n\n"
        "## Version\n"
        "v0.1 | status: draft | timestamp_utc: 2026-02-12T12:00:00Z\n"
    )


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

    service = XToDemoPipelineService(
        responses_client=_FakeClient(
            [
                _FakeResponse(
                    output_text="ok",
                    usage={"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
                )
            ]
        ),
        model="gpt-5.1",
        output_dir=tmp_path,
        store_responses=False,
        max_input_chars=60000,
        response_wait_log_interval_seconds=0.01,
    )

    with caplog.at_level(logging.INFO, logger="app.services.x_to_demo_pipeline"):
        response = service._call_responses_with_progress_logs(
            payload={"model": "gpt-5", "input": [], "store": False},
            phase_key="phase-test",
        )

    assert isinstance(response, _FakeResponse)
    progress_records = [
        record for record in caplog.records if record.message == "Awaiting OpenAI response"
    ]
    assert progress_records
    assert progress_records[0].elapsed_seconds == 0


def test_run_writes_manifest_with_usage_and_cost_totals(tmp_path) -> None:
    responses = [
        _FakeResponse(
            output_text=_build_phase_markdown(phase_key),
            usage={
                "input_tokens": 1000,
                "output_tokens": 200,
                "total_tokens": 1200,
                "cached_input_tokens": 100,
            },
        )
        for phase_key in _PHASE_KEYS
    ]
    service = _build_service(output_dir=tmp_path, responses=responses)

    result = service.run(
        x_input="This input is long enough for validation and runs all phases end-to-end.",
        additional_context="Keep scope narrow.",
        feature_name_hint="Test Feature",
        user_id=7,
    )

    assert result.usage_totals["input_tokens"] == 3000
    assert result.usage_totals["output_tokens"] == 600
    assert result.usage_totals["total_tokens"] == 3600
    assert result.cost_totals is not None
    assert result.cost_totals["total_cost"] > 0
    assert result.reasoning_effort == "low"

    requests = service.responses_client.responses.requests
    assert len(requests) == 3
    assert requests[0]["model"] == "gpt-5.1"
    assert requests[0]["reasoning"] == {"effort": "low"}

    manifest_path = tmp_path / result.run_id / "run-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["usage_totals"]["input_tokens"] == 3000
    assert manifest["cost_totals"]["total_cost"] > 0
    assert len(manifest["phase_metrics"]) == 3
    assert manifest["model"] == "gpt-5.1"
    assert manifest["reasoning_effort"] == "low"


def test_run_emits_phase_progress_events_in_backend_order(tmp_path, monkeypatch) -> None:
    responses = [
        _FakeResponse(
            output_text=_build_phase_markdown(phase_key),
            usage={"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
        )
        for phase_key in _PHASE_KEYS
    ]
    service = _build_service(output_dir=tmp_path, responses=responses)
    published: list[tuple[int, dict[str, object]]] = []

    def fake_publish_progress_event(*, user_id: int, payload: dict[str, object]) -> None:
        published.append((user_id, payload))

    monkeypatch.setattr(service, "_publish_progress_event", fake_publish_progress_event)

    result = service.run(
        x_input="This input is long enough for validation and runs all phases end-to-end.",
        additional_context=None,
        feature_name_hint=None,
        user_id=42,
    )

    statuses = [payload["status"] for _, payload in published]
    assert statuses == [
        "run_started",
        "phase_started",
        "phase_completed",
        "phase_started",
        "phase_completed",
        "phase_started",
        "phase_completed",
        "run_completed",
    ]

    phase_completed = [
        payload["phase_key"] for _, payload in published if payload["status"] == "phase_completed"
    ]
    assert phase_completed == [
        "phase-1-input-to-feature-spec",
        "phase-2-feature-spec-to-demo-spec",
        "phase-3-demo-spec-to-code-spec",
    ]
    assert all(user_id == 42 for user_id, _ in published)
    assert all(payload["run_id"] == result.run_id for _, payload in published)


def test_run_supports_gpt_52_reasoning_options(tmp_path) -> None:
    responses = [
        _FakeResponse(
            output_text=_build_phase_markdown(phase_key),
            usage={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
            model="gpt-5.2",
        )
        for phase_key in _PHASE_KEYS
    ]
    service = _build_service(output_dir=tmp_path, responses=responses)

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
                output_text=_build_phase_markdown("phase-1-input-to-feature-spec"),
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


def test_validate_phase_output_warns_on_banned_sections(caplog: pytest.LogCaptureFixture) -> None:
    markdown = _build_phase_markdown("phase-1-input-to-feature-spec").replace(
        "## Details (Markdown)",
        "## Stakeholder Personas\n- Not allowed.\n\n## Details (Markdown)",
    )

    with caplog.at_level(logging.WARNING):
        XToDemoPipelineService._validate_phase_output(
            phase_key="phase-1-input-to-feature-spec",
            markdown=markdown,
        )

    assert any("banned stakeholder-simulation content" in rec.message for rec in caplog.records)


def test_validate_phase_output_warns_on_missing_phase_keys(
    caplog: pytest.LogCaptureFixture,
) -> None:
    payload = _phase_spec_payload("phase-1-input-to-feature-spec")
    payload.pop("acceptance_criteria", None)
    title = XToDemoPipelineService._PHASE_TITLES["phase-1-input-to-feature-spec"]
    markdown = (
        f"# {title}: Test Feature\n"
        "## Summary\n"
        "- Summary.\n\n"
        "## Spec (JSON)\n"
        "```json\n"
        f"{json.dumps(payload, indent=2)}\n"
        "```\n\n"
        "## Details (Markdown)\n"
        "- Details.\n\n"
        "## Open Questions\n"
        "- None.\n\n"
        "## Version\n"
        "v0.1 | status: draft | timestamp_utc: 2026-02-12T12:00:00Z\n"
    )

    with caplog.at_level(logging.WARNING):
        XToDemoPipelineService._validate_phase_output(
            phase_key="phase-1-input-to-feature-spec",
            markdown=markdown,
        )

    assert any(
        "missing required phase keys" in rec.message and "acceptance_criteria" in rec.message
        for rec in caplog.records
    )


def test_validate_phase_output_phase3_accepts_nested_spec() -> None:
    """Phase-3 validation passes when phase keys are nested under 'spec' or 'code_spec'."""
    phase3_required = {
        "demo_overview": "Runnable demo from demo spec.",
        "tech_stack": {"frontend": "Next.js"},
        "project_changes": ["apps/web/App.tsx"],
        "components": ["Editor", "Preview"],
        "state_model": {"fields": ["input"]},
        "ai_seam": {"mock_strategy": "fixtures"},
        "acceptance_tests": [{"given": "input", "when": "run", "then": ["output"]}],
        "non_goals": ["Production"],
    }
    payload = {
        "schema_version": "0.1",
        "feature_name": "Nested Spec Feature",
        "status": "draft",
        "source": {"phase": "phase-2", "ambiguity": "none"},
        "spec": phase3_required,
    }
    title = XToDemoPipelineService._PHASE_TITLES["phase-3-demo-spec-to-code-spec"]
    markdown = (
        f"# {title}: Nested Spec Feature\n"
        "## Summary\n"
        "- Summary.\n\n"
        "## Spec (JSON)\n"
        "```json\n"
        f"{json.dumps(payload, indent=2)}\n"
        "```\n\n"
        "## Details (Markdown)\n"
        "- Details.\n\n"
        "## Open Questions\n"
        "- None.\n\n"
        "## Version\n"
        "v0.1 | status: draft | timestamp_utc: 2026-02-12T12:00:00Z\n"
    )
    XToDemoPipelineService._validate_phase_output(
        phase_key="phase-3-demo-spec-to-code-spec",
        markdown=markdown,
    )


def test_prompts_do_not_reference_stakeholder_simulation() -> None:
    phase_2_developer = XToDemoPipelineService._phase_2_developer_prompt()
    phase_3_developer = XToDemoPipelineService._phase_3_developer_prompt()
    phase_4_developer = XToDemoPipelineService._phase_4_developer_prompt()
    phase_2_user = XToDemoPipelineService._phase_2_user_prompt(
        x_input_text="Input X sample text",
        additional_context="Context",
        feature_name_hint="Feature",
    )
    phase_3_user = XToDemoPipelineService._phase_3_user_prompt(
        behavioural_spec="# Feature spec",
        feature_name_hint="Feature",
    )
    phase_4_user = XToDemoPipelineService._phase_4_user_prompt(
        demo_slice_spec="# Demo spec",
        feature_name_hint="Feature",
    )

    prompt_bundle = "\n".join(
        [
            phase_2_developer,
            phase_3_developer,
            phase_4_developer,
            phase_2_user,
            phase_3_user,
            phase_4_user,
        ]
    )
    assert "Stakeholder Personas" not in prompt_bundle
    assert "Dialogic Convergence" not in prompt_bundle
    assert "Simulate 3-5" not in prompt_bundle


def test_phase_4_prompt_requires_readme_quick_start() -> None:
    prompt = XToDemoPipelineService._phase_4_user_prompt(
        demo_slice_spec="# Demo Slice Spec",
        feature_name_hint="Quick Start Feature",
    )

    assert "README quick start section" in prompt
    assert "prerequisites, install, environment setup, run, test, and troubleshooting" in prompt


def test_normalize_phase_output_start_recovers_phase_2_heading_without_feature_name() -> None:
    markdown = (
        "Quick preamble from the model.\n"
        "# Phase 2: Feature Spec -> Demo Spec\n"
        "## Summary\n"
        "- Summary.\n\n"
        "## Spec (JSON)\n"
        "```json\n"
        f"{json.dumps(_phase_spec_payload('phase-2-feature-spec-to-demo-spec'), indent=2)}\n"
        "```\n\n"
        "## Details (Markdown)\n"
        "- Details.\n\n"
        "## Open Questions\n"
        "- None.\n\n"
        "## Version\n"
        "v0.1 | status: draft | timestamp_utc: 2026-02-12T12:00:00Z\n"
    )

    normalized = XToDemoPipelineService._normalize_phase_output_start(
        markdown=markdown,
        phase_key="phase-2-feature-spec-to-demo-spec",
    )

    assert normalized.startswith("# Phase 2: Feature Spec -> Demo Spec: Untitled Feature\n")
    XToDemoPipelineService._validate_phase_output(
        phase_key="phase-2-feature-spec-to-demo-spec",
        markdown=normalized,
    )
