"""Unit tests for X-to-Demo prompt construction helpers."""

from __future__ import annotations

from app.x_to_demo.pipeline.models import PIPELINE_PHASES, PipelineRunInput
from app.x_to_demo.pipeline.prompts import build_phase_prompts
from app.x_to_demo.schemas.code_spec import CodeSpecArtifact
from app.x_to_demo.schemas.demo_spec import DemoSpecArtifact
from app.x_to_demo.schemas.feature_spec import FeatureSpecArtifact


def _phase(key: str):
    return next(phase for phase in PIPELINE_PHASES if phase.key == key)


def _dummy_input() -> PipelineRunInput:
    return PipelineRunInput(
        x_input="Input X sample",
        additional_context="Keep scope focused.",
        feature_name_hint="Focused Demo",
        feature_name="Focused Demo",
    )


def test_build_phase_prompts_includes_global_hard_rules() -> None:
    developer_prompt, user_prompt = build_phase_prompts(
        phase=_phase("feature_spec"),
        phase_input=_dummy_input(),
    )

    assert "Constrain scope to one to three headline items only." in developer_prompt
    assert "Walkthrough means an in-app interactive UI tour" in developer_prompt
    assert (
        "Do not add fields, wrappers, markdown, or prose outside schema fields." in developer_prompt
    )
    assert "Priority checklist (must satisfy all):" in user_prompt
    assert "Anti-drift reminders:" in user_prompt


def test_build_phase_prompts_includes_phase_specific_checklist_for_demo_spec() -> None:
    developer_prompt, user_prompt = build_phase_prompts(
        phase=_phase("demo_spec"),
        phase_input=_dummy_input(),
    )

    assert (
        "Map each headline capability into a concise demo item with a clear AI moment."
        in developer_prompt
    )
    assert "not a presenter script." in developer_prompt
    assert (
        "Specify interactive walkthrough (auto-start on launch, retrigger path, cancellable controls)."
        in user_prompt
    )
    assert (
        "Provide synthetic seed data, default first-run inputs, and expected first-run outputs."
        in user_prompt
    )
    assert "Provide consistency trace to phase-1 headline capability identifiers." in user_prompt
    assert "Keep tooling decision consistent with phase 1." in user_prompt
    assert "Confirm system theme support and device framing" in user_prompt


def test_build_phase_prompts_enforces_openai_api_selection_for_code_spec() -> None:
    developer_prompt, user_prompt = build_phase_prompts(
        phase=_phase("code_spec"),
        phase_input=_dummy_input(),
    )

    assert "Select at least one OpenAI API from responses, realtime, agents" in developer_prompt
    assert "API decision guide:" in developer_prompt
    assert "Responses API: choose for request/response interactions" in developer_prompt
    assert "Realtime API: choose when the demo includes live audio" in developer_prompt
    assert "Agents SDK: choose when multi-step tool loops" in developer_prompt
    assert (
        "Must map each headline demo item to selected API(s) and justify each mapping."
        in developer_prompt
    )
    assert "Choose OpenAI API(s) and initial prompts aligned to headline items." in user_prompt
    assert "If any headline item is voice, include Realtime." in user_prompt
    assert (
        "If any headline item requires iterative tool-use/planning, include Agents." in user_prompt
    )
    assert "Otherwise default to Responses." in user_prompt
    assert "Map each headline item to selected API(s) and justify the mapping." in user_prompt
    assert (
        "Specify synthetic data implementation for deterministic first launch and reruns."
        in user_prompt
    )
    assert (
        "Keep tooling plan consistent with earlier phases and explain tool-call visibility in UI."
        in user_prompt
    )
    assert (
        "Require a testing strategy with module-by-module plan, deterministic mocks" in user_prompt
    )
    assert (
        "Do not use vague test language; provide concrete targets, mocks, and verification steps."
        in user_prompt
    )


def test_code_spec_schema_requires_explicit_testing_strategy_fields() -> None:
    schema = CodeSpecArtifact.model_json_schema()
    testing_ref = schema["properties"]["testing_strategy"]["$ref"]
    testing_name = testing_ref.split("/")[-1]
    testing_schema = schema["$defs"][testing_name]
    required = set(testing_schema.get("required", []))

    assert "unit_test_requirements" in required
    assert "test_plan_by_module" in required
    assert "test_targets" in required
    assert "acceptance_tests_scope_rules" in required
    assert "mocking_instructions" in required
    assert "verification_steps" in required


def test_demo_spec_schema_requires_synthetic_inputs_and_trace_fields() -> None:
    schema = DemoSpecArtifact.model_json_schema()
    required = set(schema.get("required", []))

    assert "synthetic_demo_inputs" in required
    assert "consistency_trace" in required
    assert "tooling_decision_trace" in required
    assert "interaction_requirements" in required

    headline_ref = schema["properties"]["headline_demo_items"]["items"]["$ref"].split("/")[-1]
    headline_props = schema["$defs"][headline_ref]["properties"]
    assert "interaction_mode" in headline_props


def test_code_spec_schema_requires_synthetic_data_and_tooling_trace_fields() -> None:
    schema = CodeSpecArtifact.model_json_schema()
    required = set(schema.get("required", []))

    assert "synthetic_data_implementation" in required
    assert "consistency_trace" in required
    assert "tooling_plan" in required

    openai_ref = schema["properties"]["openai_integration"]["$ref"].split("/")[-1]
    openai_required = set(schema["$defs"][openai_ref].get("required", []))
    assert "decision_rationale" in openai_required
    assert "api_usage_by_headline_item" in openai_required
    assert "covers_requires_voice" in openai_required
    assert "covers_requires_tool_loop" in openai_required


def test_all_artifact_schemas_separate_spec_generation_metadata() -> None:
    for model in (FeatureSpecArtifact, DemoSpecArtifact, CodeSpecArtifact):
        schema = model.model_json_schema()
        required = set(schema.get("required", []))
        properties = schema.get("properties", {})

        assert "spec_generation_metadata" in required
        assert "schema_version" not in properties
        assert "status" not in properties
        assert "source" not in properties
        assert "versioning" not in properties
