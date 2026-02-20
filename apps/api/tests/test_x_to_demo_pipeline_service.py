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
        "feature_name": feature_name,
        "spec_generation_metadata": {
            "schema_version": "0.2",
            "status": "draft",
            "source": {
                "x_source_type": "notes",
                "inputs": ["x_input", "additional_context"],
                "notes": "Synthetic payload for tests.",
            },
            "versioning": {
                "version": "0.1.0",
                "changelog": ["Initial draft"],
                "updated_at_utc": "2026-02-12T12:00:00Z",
            },
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
        "innovation_focus": {
            "ai_headline_capabilities": [
                {
                    "name": "intent_summarization",
                    "input_modalities": ["text"],
                    "user_value": "Fast conversion of noisy input into a clear product intent.",
                    "what_is_generated_or_optimized": "A concise intent summary with structured focus.",
                    "why_ai_or_innovation_is_required": "Semantic consolidation is not deterministic enough for fixed rules.",
                    "inputs": {
                        "modality": "text",
                        "description": "Raw notes and context supplied by the user.",
                    },
                    "outputs": {
                        "modality": "text",
                        "description": "Structured intent-focused summary for downstream phases.",
                    },
                    "demo_proof": "Demo shows coherent intent extraction from ambiguous notes.",
                }
            ],
            "assumptions_and_constraints": {
                "text_output_by_default": True,
                "no_external_tools_unless_necessary": True,
                "minimalist_ui": True,
                "system_theme_support": True,
                "notes": "Focus on one headline AI behavior.",
            },
            "guardrails_summary": {
                "off_topic_short_circuit": "Reject unrelated requests and restate scope.",
                "unsafe_or_disallowed_short_circuit": "Refuse disallowed content and return safe fallback.",
                "allowed_summary": "Feature-planning and demo-spec generation requests are allowed.",
                "refused_summary": "Unsafe/off-topic requests are refused with short explanation.",
            },
            "tooling_need_assessment": {
                "needs_tools": False,
                "why_tools_needed": "not needed",
            },
        },
        "acceptance_criteria": [
            {
                "capability_ref": "intent_summarization",
                "given": "Input X includes conflicting notes.",
                "when": "Phase 1 runs.",
                "then": [
                    "The feature spec labels conflicts explicitly.",
                    "Acceptance criteria remain testable.",
                ],
            }
        ],
        "excluded_plumbing": ["auth", "billing", "observability"],
        "invariants": ["Spec-first behaviour over implementation details."],
        "success_metrics": ["Required keys present in output JSON."],
    }


def _demo_spec_payload(feature_name: str = "Test Feature") -> dict[str, object]:
    return {
        "feature_name": feature_name,
        "spec_generation_metadata": {
            "schema_version": "0.2",
            "status": "draft",
            "source": {
                "x_source_type": "feature_spec",
                "inputs": ["feature_spec"],
                "notes": "Derived from phase 1.",
            },
            "versioning": {
                "version": "0.1.0",
                "changelog": ["Initial draft"],
                "updated_at_utc": "2026-02-12T12:00:00Z",
            },
        },
        "demo_overview": "Minimal demo proving the moment of value.",
        "demo_scope": {
            "in_scope": ["Happy path flow", "Mocked extraction results"],
            "out_of_scope": ["Production data integrations"],
        },
        "demo_format": "Scripted prototype walkthrough",
        "headline_demo_items": [
            {
                "capability_ref": "intent_summarization",
                "interaction_mode": "text_chat",
                "user_story_in_demo": "User pastes messy notes and receives a coherent intent summary.",
                "ai_moment": "Model call parses and restructures ambiguous notes into a focused plan.",
                "success_looks_like": "Clear structured output appears in one action.",
            }
        ],
        "interaction_requirements": {
            "requires_voice": False,
            "requires_tool_loop": False,
        },
        "ai_pipeline_delineation": {
            "ai_components": ["Intent summarization call"],
            "non_ai_components": ["Input editor", "Results panel", "Walkthrough UI"],
            "where_innovation_lives": "Semantic synthesis and structured intent extraction.",
        },
        "demo_experience": {
            "minimalist_views": [
                {
                    "name": "Input",
                    "purpose": "Capture the raw notes.",
                    "primary_component": "InputXEditor",
                    "visible_elements": ["textarea", "run button"],
                    "hidden_or_omitted_elements": ["auth panel", "admin controls"],
                },
                {
                    "name": "Output",
                    "purpose": "Show AI-generated structured summary.",
                    "primary_component": "SummaryPanel",
                    "visible_elements": ["summary card", "evidence list"],
                    "hidden_or_omitted_elements": ["analytics widgets"],
                },
            ],
            "theme_support": {"system_dark_light": True},
            "device_target": {
                "is_mobile_like": False,
                "smartphone_frame": {
                    "enabled": False,
                    "width": None,
                    "height": None,
                    "bezel_style": None,
                },
            },
        },
        "interactive_walkthrough": {
            "auto_start_on_launch": True,
            "retrigger_mechanism": "Help button in the header.",
            "controls": {"next": True, "back": True, "cancel": True},
            "steps": [
                {
                    "id": "step-input",
                    "title": "Provide Input X",
                    "ui_target": "input-editor",
                    "explanation": "Paste raw notes into the input editor.",
                    "what_ai_does_here": "No model call yet; this prepares model-ready context.",
                    "success_criteria": "Input field contains sample synthetic content.",
                },
                {
                    "id": "step-generate",
                    "title": "Generate summary",
                    "ui_target": "run-button",
                    "explanation": "Trigger the AI summary generation flow.",
                    "what_ai_does_here": "Model generates structured intent summary.",
                    "success_criteria": "Summary panel renders structured output sections.",
                },
            ],
        },
        "synthetic_demo_inputs": {
            "seed_dataset": {
                "summary": "Seed note examples for deterministic first run.",
                "sample_records": [
                    "Need an app demo from this noisy stakeholder thread.",
                    "Keep scope tight and highlight AI value.",
                ],
            },
            "default_first_run_inputs": {
                "ordered_inputs": [
                    "Need a concise feature intent from mixed notes.",
                    "Show only one headline capability.",
                ],
                "trigger_action": "Auto-populate editor and invoke run on first launch.",
            },
            "why_this_data": "Covers the single headline summarization capability deterministically.",
            "safety_and_realism_notes": "Synthetic and non-PII, but representative of real planning notes.",
            "expected_outputs": {
                "summary": "Expected sections rendered by first-run output.",
                "sample_records": [
                    "Problem: ambiguous planning notes",
                    "Objective: produce a concise structured intent",
                ],
            },
        },
        "consistency_trace": {
            "phase1_headline_capability_refs": ["intent_summarization"],
            "stable_identifier_rule": "Reuse exact capability_ref strings from phase 1.",
            "walkthrough_alignment_summary": "Walkthrough steps map directly to the same capability.",
        },
        "tooling_decision_trace": {
            "phase1_needs_tools": False,
            "phase1_why_tools_needed": "not needed",
            "must_remain_consistent": True,
            "consistency_notes": "No tools are introduced in phase 2.",
        },
        "tooling_plan_if_needed": {
            "mode": "no_tools",
            "rationale": "not needed",
            "tool_definitions": [],
            "synthetic_data_source": "not used",
            "ui_visible_tool_call_log": False,
        },
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
        "feature_name": feature_name,
        "spec_generation_metadata": {
            "schema_version": "0.2",
            "status": "draft",
            "source": {
                "x_source_type": "demo_spec",
                "inputs": ["demo_spec"],
                "notes": "Derived from phase 2.",
            },
            "versioning": {
                "version": "0.1.0",
                "changelog": ["Initial draft"],
                "updated_at_utc": "2026-02-12T12:00:00Z",
            },
        },
        "demo_overview": "Runnable frontend-only demo from the demo spec.",
        "tech_stack": {
            "frontend": "Browser-first web UI compatibility constraints.",
            "backend": "Optional thin API boundary for model calls.",
            "language": "TypeScript-compatible frontend implementation constraints.",
            "frontend_constraints": ["Browser runtime", "Minimal layout", "System theme support"],
            "backend_constraints": [
                "Stateless request/response contract",
                "No production integrations",
            ],
            "language_constraints": ["Typed interfaces for structured outputs"],
        },
        "openai_integration": {
            "selected_apis": ["responses"],
            "why_selected": "Single-turn structured outputs satisfy the focused demo flow.",
            "decision_rationale": {
                "primary_interaction_mode": "text",
                "latency_requirements": "normal",
                "statefulness": "session-state",
            },
            "api_usage_by_headline_item": [
                {
                    "headline_item_ref": "intent_summarization",
                    "selected_api": "responses",
                    "why_this_api_for_this_item": "Request/response structured output is sufficient for this item.",
                    "what_would_break_if_swapped": "Replacing with realtime or agents adds unnecessary complexity.",
                }
            ],
            "covers_requires_voice": True,
            "covers_requires_tool_loop": True,
            "models": {
                "primary": "gpt-5.1",
                "fallbacks": ["gpt-5-mini"],
            },
            "response_handling": {
                "structured_outputs": "Use strict schema-backed JSON output mode.",
                "parsing_and_validation": "Validate response payloads against phase schemas.",
                "post_processing": "Normalize field ordering before UI rendering.",
            },
        },
        "runtime_configuration": {
            "env_var_name": "OPENAI_API_KEY",
            "env_file_name": ".env",
            "env_example_file": "config/env.example",
            "env_example_required": True,
            "load_strategy": (
                "Read OPENAI_API_KEY from process environment first; in local development load "
                ".env values before startup; never commit real keys."
            ),
            "missing_key_fail_fast_behavior": (
                "If OPENAI_API_KEY is missing, block run actions and show a visible error banner "
                "with setup guidance until the key is configured."
            ),
        },
        "readme_requirements": {
            "setup_steps": [
                "Copy config/env.example to .env in the project root.",
                "Set OPENAI_API_KEY in .env before starting services.",
                "Run pnpm dev:full and open the web app.",
            ],
            "env_file_instructions": (
                "Place .env at repository root, keep config/env.example committed, and only set "
                "real OPENAI_API_KEY values in local .env."
            ),
            "local_run_instructions": (
                "Start services with pnpm dev:full, then open http://localhost:3000 to run the demo."
            ),
            "troubleshooting": [
                "If the key is missing, the UI shows a blocking configuration error and disables run.",
                "If env values are not loaded, verify .env exists at repo root and restart services.",
            ],
        },
        "project_changes": ["apps/web/components/XToDemoStudio.tsx"],
        "components": ["InputXEditor", "PhaseTimeline", "CodeSpecPanel"],
        "state_model": {"fields": ["xInput", "phaseStatus", "artifacts"]},
        "ai_seam": {
            "prompt_pack": {
                "system_prompt": "You are a focused planning assistant.",
                "developer_prompt": "Follow strict schema and constraints.",
                "user_prompt_template": "Summarize Input X into structured output.",
                "headline_item_prompts": ["Summarize messy notes into concise intent sections."],
            },
            "schemas": ["PhaseOutput"],
            "contracts": ["runPhase(input) -> output"],
            "guardrails": {
                "input_filters": ["reject_empty_input"],
                "refusal_policy": "Refuse unsafe or off-topic requests.",
                "short_circuit_behavior": "Return concise refusal object on disallowed input.",
            },
            "mock_strategy": "Deterministic fixtures",
        },
        "walkthrough_implementation": {
            "highlight_mechanism": "Step-target CSS highlight overlays tied to stable element ids.",
            "step_definition_data_model": "Static list of step objects keyed by walkthrough step id.",
            "auto_start_and_retrigger": "Auto-start on first load and retrigger via help action.",
        },
        "synthetic_data_implementation": {
            "data_location": "Local fixture module under app data folder.",
            "load_on_startup": "Load seed dataset at app init before first render.",
            "auto_populate_first_run": "Prefill input and trigger run once on initial launch.",
            "reset_and_rerun_control": "Reset button restores seed input and reruns flow.",
            "determinism_guidance": "Use fixed fixtures and deterministic response snapshots.",
        },
        "consistency_trace": {
            "phase2_headline_capability_refs": ["intent_summarization"],
            "headline_item_implementation": [
                {
                    "capability_ref": "intent_summarization",
                    "prompt_pack_elements": ["headline_item_prompts[0]"],
                    "walkthrough_step_ids": ["step-input", "step-generate"],
                    "test_targets": ["summary generation", "walkthrough alignment"],
                }
            ],
            "stable_identifier_rule": "Reuse identical capability_ref values from prior phases.",
        },
        "tooling_plan": {
            "mode": "no_tools",
            "phase1_needs_tools": False,
            "consistency_statement": "No tools are introduced after phase 1 no-tools decision.",
            "tool_interfaces": [],
            "synthetic_data_source": "not used",
            "ui_visible_tool_log_behavior": "No tool log rendered when tools are absent.",
            "mocking_strategy": "Mock OpenAI responses only; no tool mocks required.",
        },
        "testing_strategy": {
            "unit_test_requirements": (
                "Comprehensive unit tests are mandatory, written alongside implementation, "
                "run continuously during build, and failures block completion."
            ),
            "test_plan_by_module": {
                "ai_request_response_handling": "Validate structured output parsing and schema enforcement.",
                "guardrails_short_circuit_behavior": "Verify refusal paths for disallowed input.",
                "state_transitions_for_core_flows": "Assert state transitions through input->generate->render flow.",
                "walkthrough_step_mapping_and_highlight_targeting": "Ensure step ids map to expected UI targets.",
                "tooling_mocks_or_no_tools": "Assert no-tools behavior and OpenAI-only mocking.",
            },
            "test_targets": [
                "AI response parser",
                "walkthrough controller",
                "state transition reducer",
            ],
            "acceptance_tests_scope_rules": (
                "Acceptance tests are limited to the one headline capability and exclude plumbing criteria."
            ),
            "mocking_instructions": (
                "Mock OpenAI calls with deterministic fixtures; keep snapshots stable for key rendered sections."
            ),
            "verification_steps": [
                "Run unit test command for changed modules.",
                "Confirm all tests pass with no flaky reruns.",
                "Verify targeted tests cover AI parsing, walkthrough, and state transitions.",
            ],
        },
        "ui_constraints": {
            "minimalist_layout_rules": [
                "Single primary action per view",
                "No non-essential panels",
            ],
            "system_theme_support": True,
            "smartphone_frame_rule": "Enable smartphone frame only when demo_experience.device_target.is_mobile_like is true.",
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


def test_openai_compatible_schema_handles_deep_nesting_and_ref_arrays() -> None:
    raw_schema = {
        "type": "object",
        "properties": {
            "tree": {
                "type": "object",
                "properties": {
                    "level_2": {
                        "type": "object",
                        "properties": {
                            "level_3": {
                                "type": "array",
                                "items": {
                                    "$ref": "#/$defs/Leaf",
                                    "description": "Leaf items in a nested array",
                                },
                            }
                        },
                    }
                },
            }
        },
        "$defs": {
            "Leaf": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "meta": {
                        "type": "object",
                        "properties": {"score": {"type": "number"}},
                    },
                },
            }
        },
    }

    normalized = XToDemoPipelineService._openai_compatible_schema(raw_schema)
    assert normalized["additionalProperties"] is False
    assert set(normalized["required"]) == {"tree"}
    assert normalized["properties"]["tree"]["additionalProperties"] is False
    assert set(normalized["properties"]["tree"]["required"]) == {"level_2"}
    assert (
        normalized["properties"]["tree"]["properties"]["level_2"]["additionalProperties"] is False
    )
    assert set(normalized["properties"]["tree"]["properties"]["level_2"]["required"]) == {"level_3"}

    level_3_items = normalized["properties"]["tree"]["properties"]["level_2"]["properties"][
        "level_3"
    ]["items"]
    assert level_3_items == {"$ref": "#/$defs/Leaf"}
    assert normalized["$defs"]["Leaf"]["additionalProperties"] is False
    assert set(normalized["$defs"]["Leaf"]["required"]) == {"name", "meta"}
    assert normalized["$defs"]["Leaf"]["properties"]["meta"]["additionalProperties"] is False
    assert set(normalized["$defs"]["Leaf"]["properties"]["meta"]["required"]) == {"score"}


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
