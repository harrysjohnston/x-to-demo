"""Unit tests for X-to-Demo prompt construction helpers."""

from __future__ import annotations

from app.x_to_demo.pipeline.models import PIPELINE_PHASES, PipelineRunInput
from app.x_to_demo.pipeline.prompts import build_phase_prompts, openai_compatible_schema
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
        "No inert buttons: every interactive element must have defined behavior and automated test coverage."
        in developer_prompt
    )
    assert "they must be synthetic, generated via appropriate OpenAI APIs" in developer_prompt
    assert "Demo startup must not depend on live asset generation" in developer_prompt
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
    assert (
        "DemoSpec must include interaction_contracts covering every minimalist view"
        in developer_prompt
    )
    assert "SyntheticDemoInputs must include required_assets" in developer_prompt
    assert "Interaction contracts must be complete" in developer_prompt
    assert "not a presenter script." in developer_prompt
    assert (
        "Specify interactive walkthrough (auto-start on launch, retrigger path, cancellable controls)."
        in user_prompt
    )
    assert (
        "Provide synthetic seed data, default first-run inputs, and expected first-run outputs."
        in user_prompt
    )
    assert (
        "Include interaction_contracts for each minimalist view: enumerate every control"
        in user_prompt
    )
    assert "Populate synthetic_demo_inputs.required_assets" in user_prompt
    assert "Ensure screen_name matches DemoExperience.minimalist_views[*].name" in user_prompt
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
    assert "Walkthrough must be reliable: never get stuck" in developer_prompt
    assert (
        "WalkthroughImplementation must include an explicit state machine model" in developer_prompt
    )
    assert (
        "TestingStrategy must include a dedicated deterministic walkthrough test suite"
        in developer_prompt
    )
    assert (
        "TestingStrategy must include interaction_test_matrix where each DemoSpec control_id"
        in developer_prompt
    )
    assert "Validate every OpenAI request before sending" in developer_prompt
    assert "fail fast with a clear UI-visible error message" in developer_prompt
    assert "CodeSpec must include two-tier OpenAI tests" in developer_prompt
    assert "OpenAIIntegration must include request_validation" in developer_prompt
    assert "TestingStrategy must include openai_test_tiers" in developer_prompt
    assert (
        "CodeSpec must include asset_generation_plan mapping required asset modalities"
        in developer_prompt
    )
    assert "TestingStrategy must include synthetic_assets_validation" in developer_prompt
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
    assert "Include asset_generation_plan (API/model per modality" in user_prompt
    assert (
        "Include WalkthroughImplementation.state_machine_model with explicit states/transitions"
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
        "Include TestingStrategy.walkthrough_test_suite_requirements covering deterministic walkthrough step-through"
        in user_prompt
    )
    assert (
        "Include TestingStrategy.interaction_test_matrix mapping every control_id_ref"
        in user_prompt
    )
    assert "Include testing_strategy.synthetic_assets_validation" in user_prompt
    assert "Include OpenAIIntegration.request_validation" in user_prompt
    assert "Include TestingStrategy.openai_test_tiers" in user_prompt
    assert "Set interaction_test_matrix.rule to include" in user_prompt
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
    assert "openai_test_tiers" in required
    assert "verification_steps" in required
    assert "walkthrough_test_suite_requirements" in required
    assert "interaction_test_matrix" in required
    assert "synthetic_assets_validation" in required


def test_code_spec_schema_requires_walkthrough_state_machine_model() -> None:
    schema = CodeSpecArtifact.model_json_schema()
    walkthrough_ref = schema["properties"]["walkthrough_implementation"]["$ref"]
    walkthrough_name = walkthrough_ref.split("/")[-1]
    walkthrough_schema = schema["$defs"][walkthrough_name]
    required = set(walkthrough_schema.get("required", []))

    assert "highlight_mechanism" in required
    assert "step_definition_data_model" in required
    assert "auto_start_and_retrigger" in required
    assert "state_machine_model" in required


def test_openai_compatible_schema_keeps_code_spec_nested_objects_strict() -> None:
    normalized = openai_compatible_schema(CodeSpecArtifact.model_json_schema())
    openai_name = normalized["properties"]["openai_integration"]["$ref"].split("/")[-1]
    openai_schema = normalized["$defs"][openai_name]
    assert openai_schema["additionalProperties"] is False
    assert "request_validation" in set(openai_schema["required"])

    request_validation_name = openai_schema["properties"]["request_validation"]["$ref"].split("/")[
        -1
    ]
    request_validation_schema = normalized["$defs"][request_validation_name]
    assert request_validation_schema["additionalProperties"] is False
    assert set(request_validation_schema["required"]) == {
        "debug_logging_policy",
        "fail_fast_behavior",
        "preflight_checks",
        "ui_error_state_contract",
    }

    walkthrough_name = normalized["properties"]["walkthrough_implementation"]["$ref"].split("/")[-1]
    walkthrough_schema = normalized["$defs"][walkthrough_name]

    assert walkthrough_schema["additionalProperties"] is False
    assert set(walkthrough_schema["required"]) == {
        "highlight_mechanism",
        "step_definition_data_model",
        "auto_start_and_retrigger",
        "state_machine_model",
    }

    testing_name = normalized["properties"]["testing_strategy"]["$ref"].split("/")[-1]
    testing_schema = normalized["$defs"][testing_name]
    assert testing_schema["additionalProperties"] is False
    assert "openai_test_tiers" in set(testing_schema["required"])
    assert "walkthrough_test_suite_requirements" in set(testing_schema["required"])
    assert "interaction_test_matrix" in set(testing_schema["required"])
    assert "synthetic_assets_validation" in set(testing_schema["required"])

    asset_plan_name = normalized["properties"]["asset_generation_plan"]["$ref"].split("/")[-1]
    asset_plan_schema = normalized["$defs"][asset_plan_name]
    assert asset_plan_schema["additionalProperties"] is False
    assert set(asset_plan_schema["required"]) == {
        "api_and_model_by_asset_type",
        "explicit_synthetic_labeling_in_app",
        "generation_commands_or_scripts",
        "guardrails",
        "how_app_loads_and_references_assets",
        "naming_convention",
        "no_live_generation_on_startup",
        "repo_storage_location",
        "when_assets_are_required",
    }
    assert asset_plan_schema["properties"]["no_live_generation_on_startup"]["const"] is True

    guardrails_name = asset_plan_schema["properties"]["guardrails"]["$ref"].split("/")[-1]
    guardrails_schema = normalized["$defs"][guardrails_name]
    assert guardrails_schema["additionalProperties"] is False
    assert set(guardrails_schema["required"]) == {
        "content_safety_notes",
        "no_copyrighted_brand_assets",
        "no_pii",
        "no_real_person_likeness",
    }
    assert guardrails_schema["properties"]["no_real_person_likeness"]["const"] is True
    assert guardrails_schema["properties"]["no_copyrighted_brand_assets"]["const"] is True
    assert guardrails_schema["properties"]["no_pii"]["const"] is True

    openai_tiers_name = testing_schema["properties"]["openai_test_tiers"]["$ref"].split("/")[-1]
    openai_tiers_schema = normalized["$defs"][openai_tiers_name]
    assert openai_tiers_schema["additionalProperties"] is False
    assert set(openai_tiers_schema["required"]) == {"live_smoke", "mocked"}

    mocked_tier_name = openai_tiers_schema["properties"]["mocked"]["$ref"].split("/")[-1]
    mocked_tier_schema = normalized["$defs"][mocked_tier_name]
    assert mocked_tier_schema["additionalProperties"] is False
    assert set(mocked_tier_schema["required"]) == {
        "always_run_by_default",
        "coverage_requirements",
        "mocking_strategy",
    }
    assert mocked_tier_schema["properties"]["always_run_by_default"]["const"] is True

    live_tier_name = openai_tiers_schema["properties"]["live_smoke"]["$ref"].split("/")[-1]
    live_tier_schema = normalized["$defs"][live_tier_name]
    assert live_tier_schema["additionalProperties"] is False
    assert set(live_tier_schema["required"]) == {
        "commands_or_how_to_run",
        "cost_and_safety_constraints",
        "opt_in",
        "run_condition",
        "skip_behavior",
        "what_it_verifies",
    }
    assert live_tier_schema["properties"]["opt_in"]["const"] is True

    matrix_name = testing_schema["properties"]["interaction_test_matrix"]["$ref"].split("/")[-1]
    matrix_schema = normalized["$defs"][matrix_name]
    assert matrix_schema["additionalProperties"] is False
    assert set(matrix_schema["required"]) == {"execution_notes", "matrix", "rule"}

    item_name = matrix_schema["properties"]["matrix"]["items"]["$ref"].split("/")[-1]
    item_schema = normalized["$defs"][item_name]
    assert item_schema["additionalProperties"] is False
    assert set(item_schema["required"]) == {
        "control_id_ref",
        "loading_state_expectation",
        "when_disabled_expectation",
        "when_enabled_expectation",
    }


def test_feature_spec_schema_requires_unsupported_input_type_short_circuit() -> None:
    schema = FeatureSpecArtifact.model_json_schema()
    innovation_focus_ref = schema["properties"]["innovation_focus"]["$ref"].split("/")[-1]
    innovation_focus_schema = schema["$defs"][innovation_focus_ref]
    guardrails_ref = innovation_focus_schema["properties"]["guardrails_summary"]["$ref"].split("/")[
        -1
    ]
    guardrails_schema = schema["$defs"][guardrails_ref]

    assert "unsupported_input_type_short_circuit" in guardrails_schema["properties"]


def test_demo_spec_schema_requires_synthetic_inputs_and_trace_fields() -> None:
    schema = DemoSpecArtifact.model_json_schema()
    required = set(schema.get("required", []))

    assert "synthetic_demo_inputs" in required
    assert "runtime_input_and_guardrails" in schema["properties"]
    assert "consistency_trace" in required
    assert "tooling_decision_trace" in required
    assert "interaction_requirements" in required
    assert "interaction_contracts" in required

    headline_ref = schema["properties"]["headline_demo_items"]["items"]["$ref"].split("/")[-1]
    headline_props = schema["$defs"][headline_ref]["properties"]
    assert "interaction_mode" in headline_props

    interaction_contracts_ref = schema["properties"]["interaction_contracts"]["items"]["$ref"]
    contracts_name = interaction_contracts_ref.split("/")[-1]
    contracts_schema = schema["$defs"][contracts_name]
    assert set(contracts_schema["required"]) == {"controls", "notes", "screen_name"}

    control_ref = contracts_schema["properties"]["controls"]["items"]["$ref"].split("/")[-1]
    control_schema = schema["$defs"][control_ref]
    assert set(control_schema["required"]) == {
        "control_id",
        "control_type",
        "enablement_rules",
        "expected_behavior",
        "label_or_icon_description",
        "loading_state",
        "observable_state_or_ui_change",
    }

    synthetic_inputs_name = schema["properties"]["synthetic_demo_inputs"]["$ref"].split("/")[-1]
    synthetic_inputs_schema = schema["$defs"][synthetic_inputs_name]
    assert "required_assets" in set(synthetic_inputs_schema.get("required", []))
    assert "default_first_run_inputs" not in synthetic_inputs_schema["properties"]
    assert "input_presets" in synthetic_inputs_schema["properties"]
    assert "default_selected_preset_id" in synthetic_inputs_schema["properties"]
    assert "preset_application_behavior" in synthetic_inputs_schema["properties"]
    assert "preset_execution_behavior" in synthetic_inputs_schema["properties"]

    asset_name = synthetic_inputs_schema["properties"]["required_assets"]["items"]["$ref"].split(
        "/"
    )[-1]
    required_asset_schema = schema["$defs"][asset_name]
    assert set(required_asset_schema["required"]) == {
        "asset_id",
        "asset_type",
        "expected_format",
        "must_be_labeled_synthetic",
        "purpose",
        "size_constraints",
        "synthetic_label_text",
        "where_used_in_headline_flows",
    }
    assert required_asset_schema["properties"]["must_be_labeled_synthetic"]["const"] is True

    runtime_guardrails_name = schema["properties"]["runtime_input_and_guardrails"]["$ref"].split(
        "/"
    )[-1]
    runtime_guardrails_schema = schema["$defs"][runtime_guardrails_name]
    assert "accepts_runtime_inputs" in runtime_guardrails_schema["properties"]
    assert "cancel_flow_behavior" in runtime_guardrails_schema["properties"]
    assert "guardrails_pipeline_summary" in runtime_guardrails_schema["properties"]
    assert "input_capture_summary" in runtime_guardrails_schema["properties"]
    assert "presets_go_through_same_guardrails" in runtime_guardrails_schema["properties"]
    assert "relevance_check_summary" in runtime_guardrails_schema["properties"]
    assert "safety_check_summary" in runtime_guardrails_schema["properties"]
    assert "supported_input_modalities" in runtime_guardrails_schema["properties"]
    assert "user_visible_outcomes_on_reject" in runtime_guardrails_schema["properties"]
    assert runtime_guardrails_schema["properties"]["accepts_runtime_inputs"]["const"] is True
    assert (
        runtime_guardrails_schema["properties"]["presets_go_through_same_guardrails"]["const"]
        is True
    )


def test_code_spec_schema_requires_synthetic_data_and_tooling_trace_fields() -> None:
    schema = CodeSpecArtifact.model_json_schema()
    required = set(schema.get("required", []))

    assert "agent_skills_to_apply" in schema["properties"]
    assert "synthetic_data_implementation" in required
    assert "asset_generation_plan" in required
    assert "consistency_trace" in required
    assert "tooling_plan" in required

    openai_ref = schema["properties"]["openai_integration"]["$ref"].split("/")[-1]
    openai_required = set(schema["$defs"][openai_ref].get("required", []))
    assert "decision_rationale" in openai_required
    assert "api_usage_by_headline_item" in openai_required
    assert "covers_requires_voice" in openai_required
    assert "covers_requires_tool_loop" in openai_required
    assert "request_validation" in openai_required

    ai_seam_ref = schema["properties"]["ai_seam"]["$ref"].split("/")[-1]
    ai_seam_schema = schema["$defs"][ai_seam_ref]
    guardrails_ref = ai_seam_schema["properties"]["guardrails"]["$ref"].split("/")[-1]
    guardrails_schema = schema["$defs"][guardrails_ref]
    assert "runtime_guardrails_plan" in guardrails_schema["properties"]

    testing_ref = schema["properties"]["testing_strategy"]["$ref"].split("/")[-1]
    testing_schema = schema["$defs"][testing_ref]
    assert "preset_inputs_integration_coverage" in testing_schema["properties"]


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
