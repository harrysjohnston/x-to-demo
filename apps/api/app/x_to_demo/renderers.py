"""Deterministic markdown renderers and parsers for x-to-demo artifacts."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from .schemas.code_spec import CodeSpecArtifact
from .schemas.demo_spec import DemoSpecArtifact
from .schemas.feature_spec import FeatureSpecArtifact

if TYPE_CHECKING:
    from pydantic import BaseModel

_CANONICAL_JSON_HEADING = "## Canonical JSON"


def _bullet_lines(values: list[str], *, empty_message: str = "None") -> list[str]:
    if not values:
        return [f"- {empty_message}"]
    return [f"- {value}" for value in values]


def _acceptance_lines(acceptance_criteria: list[dict[str, Any]]) -> list[str]:
    if not acceptance_criteria:
        return ["- None"]

    lines: list[str] = []
    for index, criterion in enumerate(acceptance_criteria, start=1):
        lines.append(f"### AC {index}")
        capability_ref = criterion.get("capability_ref")
        if isinstance(capability_ref, str) and capability_ref:
            lines.append(f"- Capability ref: {capability_ref}")
        lines.append(f"- Given: {criterion.get('given', '')}")
        lines.append(f"- When: {criterion.get('when', '')}")
        then_items = criterion.get("then", [])
        if isinstance(then_items, list) and then_items:
            lines.append("- Then:")
            for item in then_items:
                lines.append(f"  - {item}")
        else:
            lines.append("- Then: None")
        lines.append("")

    while lines and not lines[-1]:
        lines.pop()
    return lines


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def _source_lines(source: Any) -> list[str]:
    return [
        f"- Source type: {source.x_source_type}",
        "- Inputs:",
        *_bullet_lines(source.inputs),
        f"- Notes: {source.notes or 'None'}",
    ]


def _spec_generation_metadata_lines(metadata: Any) -> list[str]:
    return [
        "### Schema And Lifecycle",
        f"- Schema version: {metadata.schema_version}",
        f"- Status: {metadata.status}",
        "",
        "### Source",
        *_source_lines(metadata.source),
        "",
        "### Versioning",
        f"- Version: {metadata.versioning.version}",
        f"- Updated (UTC): {metadata.versioning.updated_at_utc}",
        "- Changelog:",
        *_bullet_lines(metadata.versioning.changelog),
    ]


def _text_or_embedded_data_lines(value: Any) -> list[str]:
    if isinstance(value, str):
        return [f"- {value}"]

    if isinstance(value, dict):
        summary = str(value.get("summary", ""))
        sample_records = value.get("sample_records", [])
    else:
        summary = str(getattr(value, "summary", ""))
        sample_records = list(getattr(value, "sample_records", []))

    return [
        f"- Summary: {summary}",
        "- Sample records:",
        *_bullet_lines(sample_records),
    ]


def _canonical_json_block(model: BaseModel) -> list[str]:
    return [
        _CANONICAL_JSON_HEADING,
        "```json",
        json.dumps(model.model_dump(mode="json"), indent=2, sort_keys=True),
        "```",
    ]


def render_feature_spec_markdown(artifact: FeatureSpecArtifact) -> str:
    lines = [
        f"# Phase 1: Input -> Feature Spec: {artifact.feature_name}",
        "",
        "## Summary",
        f"- Objective: {artifact.intent.objective}",
        f"- Outcome: {artifact.intent.desired_outcome}",
        "",
        "## Intent",
        f"- Problem: {artifact.intent.problem}",
        f"- Objective: {artifact.intent.objective}",
        f"- Desired outcome: {artifact.intent.desired_outcome}",
        f"- Target persona: {artifact.intent.target_persona}",
        "",
        "## External Behavior",
        "### Inputs",
        *_bullet_lines(artifact.external_behavior.inputs),
        "",
        "### Outputs",
        *_bullet_lines(artifact.external_behavior.outputs),
        "",
        "### States",
        *_bullet_lines(artifact.external_behavior.states),
        "",
        "### Errors",
        *_bullet_lines(artifact.external_behavior.errors),
        "",
        "## Innovation Focus",
        "### AI Headline Capabilities",
    ]

    for index, capability in enumerate(artifact.innovation_focus.ai_headline_capabilities, start=1):
        lines.extend(
            [
                f"#### Capability {index}: {capability.name}",
                f"- Input modalities: {', '.join(capability.input_modalities)}",
                f"- User value: {capability.user_value}",
                f"- Generated/optimized: {capability.what_is_generated_or_optimized}",
                f"- Why AI is required: {capability.why_ai_or_innovation_is_required}",
                f"- Inputs: ({capability.inputs.modality}) {capability.inputs.description}",
                f"- Outputs: ({capability.outputs.modality}) {capability.outputs.description}",
                f"- Demo proof: {capability.demo_proof}",
                "",
            ]
        )

    assumptions = artifact.innovation_focus.assumptions_and_constraints
    guardrails = artifact.innovation_focus.guardrails_summary
    tooling = artifact.innovation_focus.tooling_need_assessment

    lines.extend(
        [
            "### Assumptions And Constraints",
            f"- Text output by default: {_yes_no(assumptions.text_output_by_default)}",
            (
                "- No external tools unless necessary: "
                f"{_yes_no(assumptions.no_external_tools_unless_necessary)}"
            ),
            f"- Minimalist UI: {_yes_no(assumptions.minimalist_ui)}",
            f"- System theme support: {_yes_no(assumptions.system_theme_support)}",
            f"- Notes: {assumptions.notes}",
            "",
            "### Guardrails Summary",
            f"- Off-topic short-circuit: {guardrails.off_topic_short_circuit}",
            (f"- Unsafe/disallowed short-circuit: {guardrails.unsafe_or_disallowed_short_circuit}"),
            f"- Allowed summary: {guardrails.allowed_summary}",
            f"- Refused summary: {guardrails.refused_summary}",
            "",
            "### Tooling Need Assessment",
            f"- Needs tools: {_yes_no(tooling.needs_tools)}",
            f"- Why tools needed: {tooling.why_tools_needed}",
            "",
            "## Acceptance Criteria",
            *_acceptance_lines(
                [criterion.model_dump(mode="json") for criterion in artifact.acceptance_criteria]
            ),
            "",
            "## Excluded Plumbing",
            *_bullet_lines(artifact.excluded_plumbing),
            "",
            "## Invariants",
            *_bullet_lines(artifact.invariants),
            "",
            "## Success Metrics",
            *_bullet_lines(artifact.success_metrics),
            "",
            "## Spec Generation Metadata",
            *_spec_generation_metadata_lines(artifact.spec_generation_metadata),
            "",
            *_canonical_json_block(artifact),
        ]
    )
    return "\n".join(lines).strip() + "\n"


def render_demo_spec_markdown(artifact: DemoSpecArtifact) -> str:
    lines = [
        f"# Phase 2: Feature Spec -> Demo Spec: {artifact.feature_name}",
        "",
        "## Summary",
        f"- Overview: {artifact.demo_overview}",
        f"- Format: {artifact.demo_format}",
        "",
        "## Demo Overview",
        artifact.demo_overview,
        "",
        "## Demo Scope",
        "### In Scope",
        *_bullet_lines(artifact.demo_scope.in_scope),
        "",
        "### Out of Scope",
        *_bullet_lines(artifact.demo_scope.out_of_scope),
        "",
        "## Demo Format",
        f"- {artifact.demo_format}",
        "",
        "## Headline Demo Items",
    ]

    for index, item in enumerate(artifact.headline_demo_items, start=1):
        lines.extend(
            [
                f"### Item {index}: {item.capability_ref}",
                f"- Interaction mode: {item.interaction_mode}",
                f"- User story: {item.user_story_in_demo}",
                f"- AI moment: {item.ai_moment}",
                f"- Success looks like: {item.success_looks_like}",
                "",
            ]
        )

    lines.extend(
        [
            "## Interaction Requirements",
            f"- Requires voice: {_yes_no(artifact.interaction_requirements.requires_voice)}",
            (
                "- Requires tool loop: "
                f"{_yes_no(artifact.interaction_requirements.requires_tool_loop)}"
            ),
            "",
            "## AI Pipeline Delineation",
            "### AI Components",
            *_bullet_lines(artifact.ai_pipeline_delineation.ai_components),
            "",
            "### Non-AI Components",
            *_bullet_lines(artifact.ai_pipeline_delineation.non_ai_components),
            "",
            (
                "### Where Innovation Lives\n"
                f"- {artifact.ai_pipeline_delineation.where_innovation_lives}"
            ),
            "",
            "## Demo Experience",
            "### Minimalist Views",
        ]
    )

    for index, view in enumerate(artifact.demo_experience.minimalist_views, start=1):
        lines.extend(
            [
                f"#### View {index}: {view.name}",
                f"- Purpose: {view.purpose}",
                f"- Primary component: {view.primary_component}",
                "- Visible elements:",
                *_bullet_lines(view.visible_elements),
                "- Hidden/omitted elements:",
                *_bullet_lines(view.hidden_or_omitted_elements),
                "",
            ]
        )

    smartphone_frame = artifact.demo_experience.device_target.smartphone_frame
    frame_width = smartphone_frame.width if smartphone_frame.width is not None else "N/A"
    frame_height = smartphone_frame.height if smartphone_frame.height is not None else "N/A"

    lines.extend(
        [
            "### Theme Support",
            (
                "- System dark/light support: "
                f"{_yes_no(artifact.demo_experience.theme_support.system_dark_light)}"
            ),
            "",
            "### Device Target",
            (f"- Mobile-like: {_yes_no(artifact.demo_experience.device_target.is_mobile_like)}"),
            f"- Smartphone frame enabled: {_yes_no(smartphone_frame.enabled)}",
            f"- Smartphone frame width: {frame_width}",
            f"- Smartphone frame height: {frame_height}",
            f"- Smartphone bezel style: {smartphone_frame.bezel_style or 'N/A'}",
            "",
            "## Interactive Walkthrough",
            (
                "- Auto start on launch: "
                f"{_yes_no(artifact.interactive_walkthrough.auto_start_on_launch)}"
            ),
            f"- Retrigger mechanism: {artifact.interactive_walkthrough.retrigger_mechanism}",
            "### Controls",
            f"- Next: {_yes_no(artifact.interactive_walkthrough.controls.next)}",
            f"- Back: {_yes_no(artifact.interactive_walkthrough.controls.back)}",
            f"- Cancel: {_yes_no(artifact.interactive_walkthrough.controls.cancel)}",
            "",
            "### Steps",
        ]
    )

    for index, step in enumerate(artifact.interactive_walkthrough.steps, start=1):
        lines.extend(
            [
                f"#### Step {index}: {step.title}",
                f"- ID: {step.id}",
                f"- UI target: {step.ui_target}",
                f"- Explanation: {step.explanation}",
                f"- What AI does here: {step.what_ai_does_here}",
                f"- Success criteria: {step.success_criteria}",
                "",
            ]
        )

    lines.extend(
        [
            "## Synthetic Demo Inputs",
            "### Seed Dataset",
            *_text_or_embedded_data_lines(artifact.synthetic_demo_inputs.seed_dataset),
            "",
            "### Default First Run Inputs",
            "- Ordered inputs:",
            *_bullet_lines(artifact.synthetic_demo_inputs.default_first_run_inputs.ordered_inputs),
            (
                "- Trigger action: "
                f"{artifact.synthetic_demo_inputs.default_first_run_inputs.trigger_action}"
            ),
            "",
            f"### Why This Data\n- {artifact.synthetic_demo_inputs.why_this_data}",
            "",
            (
                "### Safety And Realism Notes\n"
                f"- {artifact.synthetic_demo_inputs.safety_and_realism_notes}"
            ),
            "",
            "### Expected Outputs",
            *_text_or_embedded_data_lines(artifact.synthetic_demo_inputs.expected_outputs),
            "",
            "### Required Synthetic Assets",
        ]
    )

    if not artifact.synthetic_demo_inputs.required_assets:
        lines.extend(
            [
                "- None",
                "",
            ]
        )
    else:
        for index, asset in enumerate(artifact.synthetic_demo_inputs.required_assets, start=1):
            lines.extend(
                [
                    f"#### Asset {index}: {asset.asset_id}",
                    f"- Type: {asset.asset_type}",
                    f"- Purpose: {asset.purpose}",
                    "- Where used in headline flows:",
                    *_bullet_lines(asset.where_used_in_headline_flows),
                    f"- Expected format: {asset.expected_format}",
                    f"- Size constraints: {asset.size_constraints}",
                    (f"- Must be labeled synthetic: {_yes_no(asset.must_be_labeled_synthetic)}"),
                    f"- Synthetic label text: {asset.synthetic_label_text}",
                    "",
                ]
            )

    lines.extend(
        [
            "## Consistency Trace",
            "### Phase 1 Headline Capability Refs",
            *_bullet_lines(artifact.consistency_trace.phase1_headline_capability_refs),
            "",
            f"- Stable identifier rule: {artifact.consistency_trace.stable_identifier_rule}",
            (
                "- Walkthrough alignment summary: "
                f"{artifact.consistency_trace.walkthrough_alignment_summary}"
            ),
            "",
            "## Tooling Decision Trace",
            f"- Phase 1 needs tools: {_yes_no(artifact.tooling_decision_trace.phase1_needs_tools)}",
            (
                "- Phase 1 why tools needed: "
                f"{artifact.tooling_decision_trace.phase1_why_tools_needed}"
            ),
            (
                "- Must remain consistent: "
                f"{_yes_no(artifact.tooling_decision_trace.must_remain_consistent)}"
            ),
            f"- Consistency notes: {artifact.tooling_decision_trace.consistency_notes}",
            "",
            "## Tooling Plan If Needed",
            f"- Mode: {artifact.tooling_plan_if_needed.mode}",
            f"- Rationale: {artifact.tooling_plan_if_needed.rationale}",
            f"- Synthetic data source: {artifact.tooling_plan_if_needed.synthetic_data_source}",
            (
                "- UI visible tool-call log: "
                f"{_yes_no(artifact.tooling_plan_if_needed.ui_visible_tool_call_log)}"
            ),
            "- Tool definitions:",
            *_bullet_lines(artifact.tooling_plan_if_needed.tool_definitions),
            "",
            "## Core Flow Steps",
            *_bullet_lines(artifact.core_flow_steps),
            "",
            "## Success Signals",
            *_bullet_lines(artifact.success_signals),
            "",
            "## Example Copy",
            *_bullet_lines(artifact.example_copy),
            "",
            "## Spec Generation Metadata",
            *_spec_generation_metadata_lines(artifact.spec_generation_metadata),
            "",
            *_canonical_json_block(artifact),
        ]
    )
    return "\n".join(lines).strip() + "\n"


def render_code_spec_markdown(artifact: CodeSpecArtifact) -> str:
    lines = [
        f"# Phase 3: Demo Spec -> Code Spec: {artifact.feature_name}",
        "",
        "## Summary",
        f"- Overview: {artifact.demo_overview}",
        f"- Frontend: {artifact.tech_stack.frontend}",
        f"- Language: {artifact.tech_stack.language}",
        "",
        "## Demo Overview",
        artifact.demo_overview,
        "",
        "## Tech Stack",
        f"- Frontend: {artifact.tech_stack.frontend}",
        f"- Backend: {artifact.tech_stack.backend or 'N/A'}",
        f"- Language: {artifact.tech_stack.language}",
        "### Frontend Constraints",
        *_bullet_lines(artifact.tech_stack.frontend_constraints),
        "",
        "### Backend Constraints",
        *_bullet_lines(artifact.tech_stack.backend_constraints),
        "",
        "### Language Constraints",
        *_bullet_lines(artifact.tech_stack.language_constraints),
        "",
        "## OpenAI Integration",
        "### Selected APIs",
        *_bullet_lines(artifact.openai_integration.selected_apis),
        "",
        f"- Why selected: {artifact.openai_integration.why_selected}",
        "### Decision Rationale",
        (
            "- Primary interaction mode: "
            f"{artifact.openai_integration.decision_rationale.primary_interaction_mode}"
        ),
        (
            "- Latency requirements: "
            f"{artifact.openai_integration.decision_rationale.latency_requirements}"
        ),
        f"- Statefulness: {artifact.openai_integration.decision_rationale.statefulness}",
        "",
        "### API Usage By Headline Item",
    ]

    for index, item in enumerate(artifact.openai_integration.api_usage_by_headline_item, start=1):
        lines.extend(
            [
                f"#### Mapping {index}: {item.headline_item_ref}",
                f"- Selected API: {item.selected_api}",
                f"- Why this API: {item.why_this_api_for_this_item}",
                f"- What breaks if swapped: {item.what_would_break_if_swapped}",
                "",
            ]
        )

    lines.extend(
        [
            (
                "- Covers requires_voice: "
                f"{_yes_no(artifact.openai_integration.covers_requires_voice)}"
            ),
            (
                "- Covers requires_tool_loop: "
                f"{_yes_no(artifact.openai_integration.covers_requires_tool_loop)}"
            ),
            "",
            "### Models",
            f"- Primary: {artifact.openai_integration.models.primary}",
            "- Fallbacks:",
            *_bullet_lines(artifact.openai_integration.models.fallbacks),
            "",
            "### Response Handling",
            (
                "- Structured outputs: "
                f"{artifact.openai_integration.response_handling.structured_outputs}"
            ),
            (
                "- Parsing and validation: "
                f"{artifact.openai_integration.response_handling.parsing_and_validation}"
            ),
            (f"- Post processing: {artifact.openai_integration.response_handling.post_processing}"),
            "",
            "## Project Changes",
            *_bullet_lines(artifact.project_changes),
            "",
            "## Components",
            *_bullet_lines(artifact.components),
            "",
            "## State Model",
            *_bullet_lines(artifact.state_model.fields),
            "",
            "## AI Seam",
            "### Prompt Pack",
            f"- System prompt: {artifact.ai_seam.prompt_pack.system_prompt}",
            f"- Developer prompt: {artifact.ai_seam.prompt_pack.developer_prompt}",
            f"- User prompt template: {artifact.ai_seam.prompt_pack.user_prompt_template}",
            "- Headline item prompts:",
            *_bullet_lines(artifact.ai_seam.prompt_pack.headline_item_prompts),
            "",
            "### Schemas",
            *_bullet_lines(artifact.ai_seam.schemas),
            "",
            "### Contracts",
            *_bullet_lines(artifact.ai_seam.contracts),
            "",
            "### Guardrails",
            "- Input filters:",
            *_bullet_lines(artifact.ai_seam.guardrails.input_filters),
            f"- Refusal policy: {artifact.ai_seam.guardrails.refusal_policy}",
            (f"- Short-circuit behavior: {artifact.ai_seam.guardrails.short_circuit_behavior}"),
            "",
        ]
    )

    if artifact.ai_seam.tooling is None:
        lines.extend(
            [
                "### Tooling",
                "- None",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "### Tooling",
                "- Tool definitions:",
                *_bullet_lines(artifact.ai_seam.tooling.tool_definitions),
                f"- Synthetic data source: {artifact.ai_seam.tooling.synthetic_data_source}",
                (
                    "- UI visible tool calls/results: "
                    f"{_yes_no(artifact.ai_seam.tooling.ui_visible_tool_calls_and_results)}"
                ),
                "",
            ]
        )

    lines.extend(
        [
            f"### Mock Strategy\n- {artifact.ai_seam.mock_strategy}",
            "",
            "## Walkthrough Implementation",
            f"- Highlight mechanism: {artifact.walkthrough_implementation.highlight_mechanism}",
            (
                "- Step definition data model: "
                f"{artifact.walkthrough_implementation.step_definition_data_model}"
            ),
            (
                "- Auto start and retrigger: "
                f"{artifact.walkthrough_implementation.auto_start_and_retrigger}"
            ),
            "",
            "## Synthetic Data Implementation",
            f"- Data location: {artifact.synthetic_data_implementation.data_location}",
            f"- Load on startup: {artifact.synthetic_data_implementation.load_on_startup}",
            (
                "- Auto populate first run: "
                f"{artifact.synthetic_data_implementation.auto_populate_first_run}"
            ),
            (
                "- Reset and rerun control: "
                f"{artifact.synthetic_data_implementation.reset_and_rerun_control}"
            ),
            (
                "- Determinism guidance: "
                f"{artifact.synthetic_data_implementation.determinism_guidance}"
            ),
            "",
            "## Asset Generation Plan",
            (
                "- When assets are required: "
                f"{artifact.asset_generation_plan.when_assets_are_required}"
            ),
            f"- Repo storage location: {artifact.asset_generation_plan.repo_storage_location}",
            f"- Naming convention: {artifact.asset_generation_plan.naming_convention}",
            (
                "- App load/reference behavior: "
                f"{artifact.asset_generation_plan.how_app_loads_and_references_assets}"
            ),
            (
                "- Synthetic labeling in app: "
                f"{artifact.asset_generation_plan.explicit_synthetic_labeling_in_app}"
            ),
            (
                "- No live generation on startup: "
                f"{_yes_no(artifact.asset_generation_plan.no_live_generation_on_startup)}"
            ),
            "### API And Model By Asset Type",
        ]
    )

    for index, choice in enumerate(
        artifact.asset_generation_plan.api_and_model_by_asset_type, start=1
    ):
        lines.extend(
            [
                f"#### Choice {index}: {choice.asset_type}",
                f"- API surface: {choice.openai_api_surface}",
                f"- Model: {choice.model}",
                f"- Rationale: {choice.why_this_choice}",
                "",
            ]
        )

    lines.extend(
        [
            "### Generation Commands Or Scripts",
            *_bullet_lines(artifact.asset_generation_plan.generation_commands_or_scripts),
            "",
            "### Guardrails",
            (
                "- No real person likeness: "
                f"{_yes_no(artifact.asset_generation_plan.guardrails.no_real_person_likeness)}"
            ),
            (
                "- No copyrighted brand assets: "
                f"{_yes_no(artifact.asset_generation_plan.guardrails.no_copyrighted_brand_assets)}"
            ),
            f"- No PII: {_yes_no(artifact.asset_generation_plan.guardrails.no_pii)}",
            (
                "- Content safety notes: "
                f"{artifact.asset_generation_plan.guardrails.content_safety_notes}"
            ),
            "",
            "## Consistency Trace",
            "### Phase 2 Headline Capability Refs",
            *_bullet_lines(artifact.consistency_trace.phase2_headline_capability_refs),
            "",
            f"- Stable identifier rule: {artifact.consistency_trace.stable_identifier_rule}",
            "",
            "### Headline Item Implementation",
        ]
    )

    for index, item in enumerate(artifact.consistency_trace.headline_item_implementation, start=1):
        lines.extend(
            [
                f"#### Item {index}: {item.capability_ref}",
                "- Prompt pack elements:",
                *_bullet_lines(item.prompt_pack_elements),
                "- Walkthrough step IDs:",
                *_bullet_lines(item.walkthrough_step_ids),
                "- Test targets:",
                *_bullet_lines(item.test_targets),
                "",
            ]
        )

    lines.extend(
        [
            "## Tooling Plan",
            f"- Mode: {artifact.tooling_plan.mode}",
            f"- Phase 1 needs tools: {_yes_no(artifact.tooling_plan.phase1_needs_tools)}",
            f"- Consistency statement: {artifact.tooling_plan.consistency_statement}",
            "- Tool interfaces:",
            *_bullet_lines(artifact.tooling_plan.tool_interfaces),
            f"- Synthetic data source: {artifact.tooling_plan.synthetic_data_source}",
            f"- UI visible tool log behavior: {artifact.tooling_plan.ui_visible_tool_log_behavior}",
            f"- Mocking strategy: {artifact.tooling_plan.mocking_strategy}",
            "",
            "## Testing Strategy",
            f"- Unit test requirements: {artifact.testing_strategy.unit_test_requirements}",
            "### Test Plan By Module",
            (
                "- AI request/response handling: "
                f"{artifact.testing_strategy.test_plan_by_module.ai_request_response_handling}"
            ),
            (
                "- Guardrails short-circuit behavior: "
                f"{artifact.testing_strategy.test_plan_by_module.guardrails_short_circuit_behavior}"
            ),
            (
                "- State transitions for core flows: "
                f"{artifact.testing_strategy.test_plan_by_module.state_transitions_for_core_flows}"
            ),
            (
                "- Walkthrough mapping/targets: "
                f"{artifact.testing_strategy.test_plan_by_module.walkthrough_step_mapping_and_highlight_targeting}"
            ),
            (
                "- Tooling mocks or no-tools: "
                f"{artifact.testing_strategy.test_plan_by_module.tooling_mocks_or_no_tools}"
            ),
            "",
            "### Test Targets",
            *_bullet_lines(artifact.testing_strategy.test_targets),
            "",
            (f"- Acceptance scope rules: {artifact.testing_strategy.acceptance_tests_scope_rules}"),
            f"- Mocking instructions: {artifact.testing_strategy.mocking_instructions}",
            (
                "- Synthetic assets validation: "
                f"{artifact.testing_strategy.synthetic_assets_validation}"
            ),
            "### Verification Steps",
            *_bullet_lines(artifact.testing_strategy.verification_steps),
            "",
            "## UI Constraints",
            "### Minimalist Layout Rules",
            *_bullet_lines(artifact.ui_constraints.minimalist_layout_rules),
            "",
            f"- System theme support: {_yes_no(artifact.ui_constraints.system_theme_support)}",
            f"- Smartphone frame rule: {artifact.ui_constraints.smartphone_frame_rule}",
            "",
            "## Acceptance Tests",
            *_acceptance_lines(
                [criterion.model_dump(mode="json") for criterion in artifact.acceptance_tests]
            ),
            "",
            "## Non Goals",
            *_bullet_lines(artifact.non_goals),
            "",
            "## Spec Generation Metadata",
            *_spec_generation_metadata_lines(artifact.spec_generation_metadata),
            "",
            *_canonical_json_block(artifact),
        ]
    )
    return "\n".join(lines).strip() + "\n"


def render_markdown(model: BaseModel) -> str:
    """Render deterministic markdown for a supported artifact model."""
    if isinstance(model, FeatureSpecArtifact):
        return render_feature_spec_markdown(model)
    if isinstance(model, DemoSpecArtifact):
        return render_demo_spec_markdown(model)
    if isinstance(model, CodeSpecArtifact):
        return render_code_spec_markdown(model)
    raise TypeError(f"Unsupported artifact model: {type(model).__name__}")


def extract_canonical_json(markdown: str) -> dict[str, Any]:
    """Extract canonical JSON payload embedded in markdown."""
    canonical_section = re.search(
        rf"{re.escape(_CANONICAL_JSON_HEADING)}\s*```json\s*(.*?)\s*```",
        markdown,
        flags=re.IGNORECASE | re.DOTALL,
    )
    raw_block = canonical_section.group(1) if canonical_section else None

    if raw_block is None:
        blocks = re.findall(r"```json\s*(.*?)\s*```", markdown, flags=re.IGNORECASE | re.DOTALL)
        if not blocks:
            raise ValueError("No JSON code block found in markdown")
        raw_block = blocks[-1]

    try:
        payload = json.loads(raw_block)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON block in markdown: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Canonical JSON block must decode to an object")
    return payload


def parse_markdown_to_model(markdown: str, model_type: type[BaseModel]) -> BaseModel:
    """Parse markdown to a model using the embedded canonical JSON block."""
    payload = extract_canonical_json(markdown)
    return model_type.model_validate(payload)
