"""Code spec schema for phase 3 (demo spec -> code spec)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .common import AcceptanceCriterion, ArtifactBase


class StrictSchemaModel(BaseModel):
    """Schema model with strict unknown-field handling for structured outputs."""

    model_config = ConfigDict(extra="forbid")


class TechStack(StrictSchemaModel):
    """High-level stack decisions for the implementation."""

    frontend: str = Field(
        description=(
            "Frontend compatibility summary as constraints (for example browser/runtime "
            "requirements), not a mandated framework."
        )
    )
    backend: str | None = Field(
        default=None,
        description=(
            "Backend compatibility summary when relevant, expressed as constraints rather "
            "than a required implementation choice."
        ),
    )
    language: str = Field(
        description=("Language/runtime compatibility summary as constraints, not a mandatory pick.")
    )
    frontend_constraints: list[str] = Field(
        min_length=1,
        description="Concrete frontend compatibility requirements the implementation must satisfy.",
    )
    backend_constraints: list[str] = Field(
        default_factory=list,
        description="Backend compatibility requirements when backend behavior is needed.",
    )
    language_constraints: list[str] = Field(
        min_length=1,
        description="Language/runtime compatibility requirements.",
    )


class StateModel(StrictSchemaModel):
    """Top-level state fields surfaced by the implementation."""

    fields: list[str] = Field(
        default_factory=list,
        description="Key state fields to model explicitly.",
    )


class OpenAIModelSelection(StrictSchemaModel):
    """OpenAI model selection and fallback policy."""

    primary: str = Field(description="Primary model identifier for the main AI moment.")
    fallbacks: list[str] = Field(
        default_factory=list,
        description="Ordered fallback model identifiers.",
    )


class OpenAIResponseHandling(StrictSchemaModel):
    """Response parsing and post-processing strategy."""

    structured_outputs: str = Field(
        description="How structured outputs are requested and constrained."
    )
    parsing_and_validation: str = Field(
        description="How responses are parsed and validated against schemas."
    )
    post_processing: str = Field(
        description="How parsed outputs are normalized before UI/state consumption."
    )


class OpenAIDecisionRationale(StrictSchemaModel):
    """Selection rationale dimensions used for API choice."""

    primary_interaction_mode: Literal["text", "multimodal", "voice", "tool-loop"] = Field(
        description="Primary interaction mode that drives API selection."
    )
    latency_requirements: Literal["low", "normal"] = Field(
        description="Latency requirement category for the demo interaction."
    )
    statefulness: Literal["stateless", "session-state", "long-lived"] = Field(
        description="Statefulness requirement for the runtime interaction model."
    )


class APIUsageByHeadlineItem(StrictSchemaModel):
    """Per-headline-item API mapping and swap-risk rationale."""

    headline_item_ref: str = Field(
        description="Reference to a stable headline item identifier from earlier phases."
    )
    selected_api: Literal["responses", "realtime", "agents"] = Field(
        description="Chosen API for this specific headline item."
    )
    why_this_api_for_this_item: str = Field(
        description="Short reasoning for why this API best fits this headline item."
    )
    what_would_break_if_swapped: str = Field(
        description="What would degrade or fail if a different API were used."
    )


class OpenAIIntegration(StrictSchemaModel):
    """OpenAI API and model integration plan."""

    selected_apis: list[Literal["responses", "realtime", "agents"]] = Field(
        min_length=1,
        description="OpenAI API surfaces selected for this implementation.",
    )
    why_selected: str = Field(
        description="Rationale for selected APIs based on headline demo requirements."
    )
    decision_rationale: OpenAIDecisionRationale = Field(
        description="Explicit interaction/latency/state rationale for API decisions."
    )
    api_usage_by_headline_item: list[APIUsageByHeadlineItem] = Field(
        min_length=1,
        max_length=3,
        description="Required mapping from headline items to selected APIs with per-item reasoning.",
    )
    covers_requires_voice: bool = Field(
        description=(
            "Acknowledgement that selected_apis correctly cover DemoSpec.interaction_requirements.requires_voice."
        )
    )
    covers_requires_tool_loop: bool = Field(
        description=(
            "Acknowledgement that selected_apis correctly cover DemoSpec.interaction_requirements.requires_tool_loop."
        )
    )
    models: OpenAIModelSelection = Field(description="Primary/fallback model strategy.")
    response_handling: OpenAIResponseHandling = Field(
        description="Structured output parsing and post-processing plan."
    )


class PromptPack(StrictSchemaModel):
    """Prompt templates aligned to headline demo items."""

    system_prompt: str = Field(description="Base system prompt template.")
    developer_prompt: str = Field(description="Base developer prompt template.")
    user_prompt_template: str = Field(description="User prompt template shape.")
    headline_item_prompts: list[str] = Field(
        min_length=1,
        description="Initial prompt variants mapped to headline demo/capability items.",
    )


class AISeamGuardrails(StrictSchemaModel):
    """Input filtering and refusal behavior at the AI seam."""

    input_filters: list[str] = Field(
        min_length=1,
        description="Basic input filters enforced before model calls.",
    )
    refusal_policy: str = Field(description="Refusal policy and message behavior.")
    short_circuit_behavior: str = Field(
        description="Short-circuit behavior for disallowed or off-topic requests."
    )


class AISeamTooling(StrictSchemaModel):
    """Tooling details when external tools are required."""

    tool_definitions: list[str] = Field(
        min_length=1,
        description="Tool definitions used by the AI layer.",
    )
    synthetic_data_source: str = Field(
        description="Synthetic data source used to keep the demo self-contained."
    )
    ui_visible_tool_calls_and_results: Literal[True] = Field(
        description="Must be true: UI displays tool calls and returned results."
    )


class AISeam(StrictSchemaModel):
    """Model/tooling contract boundary in the implementation."""

    prompt_pack: PromptPack = Field(
        description="Initial system/developer/user prompt pack per headline item."
    )
    schemas: list[str] = Field(
        min_length=1,
        description="Schema contracts used at the AI seam.",
    )
    contracts: list[str] = Field(
        default_factory=list,
        description="Function/protocol contracts for AI-driven components.",
    )
    guardrails: AISeamGuardrails = Field(
        description="Input filters, refusal policy, and short-circuit behavior."
    )
    tooling: AISeamTooling | None = Field(
        default=None,
        description=(
            "Tooling plan only when tools are required, including synthetic data source "
            "and UI-visible tool call/results."
        ),
    )
    mock_strategy: str = Field(description="How AI dependencies are mocked in local/dev flows.")


class WalkthroughImplementation(StrictSchemaModel):
    """Implementation details for the in-app walkthrough."""

    highlight_mechanism: str = Field(
        description="How target UI elements are highlighted for each walkthrough step."
    )
    step_definition_data_model: str = Field(
        description="Data model used to define and sequence walkthrough steps."
    )
    auto_start_and_retrigger: str = Field(
        description="How walkthrough auto-start and retrigger behavior is implemented."
    )
    state_machine_model: str = Field(
        description=(
            "Explicit walkthrough state machine: states, allowed transitions, guards, and "
            "transition effects. Must cover auto-start, next, back, cancel, finish, and "
            "retrigger behavior, including invalid transition handling and safe step-index bounds."
        )
    )


class InteractionTestMatrixItem(StrictSchemaModel):
    """Per-control deterministic interaction test expectations."""

    control_id_ref: str = Field(
        description="Reference to DemoSpec interaction_contracts.controls[*].control_id."
    )
    when_enabled_expectation: str = Field(
        description=(
            "What the automated test asserts when this control is enabled, including an "
            "observable UI/state change."
        )
    )
    when_disabled_expectation: str = Field(
        description=(
            "What the automated test asserts when this control is disabled, including the "
            "disabled explanation/affordance."
        )
    )
    loading_state_expectation: str = Field(
        description="What the test asserts about loading behavior, or 'not applicable'."
    )


class InteractionTestMatrix(StrictSchemaModel):
    """No-inert-controls deterministic test matrix contract."""

    rule: str = Field(
        pattern=".*Every button clicked triggers an observable state/UI change OR is explicitly disabled with explanation.*",
        description=(
            "Must include the rule: 'Every button clicked triggers an observable state/UI "
            "change OR is explicitly disabled with explanation.'"
        ),
    )
    matrix: list[InteractionTestMatrixItem] = Field(
        min_length=1,
        description="Per-control test expectations mapped by control_id.",
    )
    execution_notes: str = Field(
        description="How these tests run deterministically (fixtures/mocks) and where they live."
    )


class TestingStrategy(StrictSchemaModel):
    """Testing requirements for deterministic demo delivery."""

    class TestPlanByModule(StrictSchemaModel):
        """Module-level coverage plan for mandatory test targets."""

        ai_request_response_handling: str = Field(
            description="Coverage plan for structured output parsing and validation."
        )
        guardrails_short_circuit_behavior: str = Field(
            description="Coverage plan for refusal/short-circuit guardrail behavior."
        )
        state_transitions_for_core_flows: str = Field(
            description="Coverage plan for primary state transitions."
        )
        walkthrough_step_mapping_and_highlight_targeting: str = Field(
            description="Coverage plan for walkthrough step mapping and highlight targets."
        )
        tooling_mocks_or_no_tools: str = Field(
            description="Coverage plan for tool mocking, or explicit no-tools behavior."
        )

    unit_test_requirements: str = Field(
        description=(
            "Mandatory unit-test policy: comprehensive coverage, tests written alongside "
            "implementation, tests executed continuously during build, and failing tests block completion."
        )
    )
    test_plan_by_module: TestPlanByModule = Field(
        description=(
            "Required per-module test plan coverage for core AI, guardrails, state, walkthrough, "
            "and tooling/no-tools behavior."
        )
    )
    test_targets: list[str] = Field(
        min_length=1,
        description="Primary modules/flows that must be covered by tests.",
    )
    acceptance_tests_scope_rules: str = Field(
        description=(
            "Rules that acceptance coverage stays limited to the 1-3 headline demo items and "
            "forbids acceptance criteria for excluded plumbing."
        )
    )
    mocking_instructions: str = Field(
        description=(
            "How to mock OpenAI calls and optional tools using deterministic synthetic fixtures "
            "and snapshot-style expectations where useful."
        )
    )
    verification_steps: list[str] = Field(
        min_length=1,
        description=(
            "Verifiable checklist including test commands, expected pass condition, and qualitative "
            "minimum test expectations."
        ),
    )
    walkthrough_test_suite_requirements: str = Field(
        description=(
            "Dedicated deterministic walkthrough suite requirements: auto-start on launch; next/back; "
            "cancel at any time; finish; retrigger; safe step-index bounds; highlight target "
            "resolution; and per-step validation that intended UI components are present/visible "
            "(and enabled when applicable) when shown."
        )
    )
    interaction_test_matrix: InteractionTestMatrix = Field(
        description=(
            "Required interaction test matrix ensuring no inert controls. Must cover enabled "
            "behavior, disabled explanation behavior, and loading-state behavior per control."
        )
    )


class UIConstraints(StrictSchemaModel):
    """Minimalist UI and device framing constraints."""

    minimalist_layout_rules: list[str] = Field(
        min_length=1,
        description="Rules that keep the UI minimal and focused on headline moments.",
    )
    system_theme_support: Literal[True] = Field(
        description="Must be true: support system dark/light theme."
    )
    smartphone_frame_rule: str = Field(
        description=(
            "Conditional rule: smartphone frame only when "
            "DemoSpec.device_target.is_mobile_like is true."
        )
    )


class SyntheticDataImplementation(StrictSchemaModel):
    """Implementation plan for deterministic synthetic demo data usage."""

    data_location: str = Field(description="Where synthetic seed data lives in the repository.")
    load_on_startup: str = Field(
        description="How synthetic data is loaded deterministically on startup."
    )
    auto_populate_first_run: str = Field(
        description="How first-run inputs are auto-populated and initial run is triggered."
    )
    reset_and_rerun_control: str = Field(
        description="How users reset to seed data and rerun identical demo behavior."
    )
    determinism_guidance: str = Field(
        description="Deterministic parameter guidance or expected structure/snapshot fallback."
    )


class HeadlineItemImplementation(StrictSchemaModel):
    """Per-headline capability implementation and verification mapping."""

    capability_ref: str = Field(
        description="Stable headline capability identifier carried from prior phases."
    )
    prompt_pack_elements: list[str] = Field(
        min_length=1,
        description="Prompt-pack elements used to implement this capability.",
    )
    walkthrough_step_ids: list[str] = Field(
        min_length=1,
        description="Walkthrough step identifiers that demonstrate this capability.",
    )
    test_targets: list[str] = Field(
        min_length=1,
        description="Test targets that verify this capability implementation.",
    )


class ConsistencyTrace(StrictSchemaModel):
    """Cross-phase consistency trace for phase-2 to phase-3 mapping."""

    phase2_headline_capability_refs: list[str] = Field(
        min_length=1,
        max_length=3,
        description="Stable headline capability identifiers inherited from demo spec.",
    )
    headline_item_implementation: list[HeadlineItemImplementation] = Field(
        min_length=1,
        max_length=3,
        description="Per-headline mapping for prompt, walkthrough, and tests.",
    )
    stable_identifier_rule: str = Field(
        description="Rule that preserves identifier consistency across all artifacts."
    )


class ToolingPlan(StrictSchemaModel):
    """Required tooling strategy consistent with phase-1 tooling decision."""

    mode: Literal["no_tools", "tools_with_synthetic_data"] = Field(
        description="Explicitly choose no tools or tools backed by synthetic data."
    )
    phase1_needs_tools: bool = Field(
        description="Phase-1 tooling decision copied forward for consistency checks."
    )
    consistency_statement: str = Field(
        description="How this tooling plan remains consistent with phase-1 and phase-2 decisions."
    )
    tool_interfaces: list[str] = Field(
        default_factory=list,
        description="Tool interfaces required when mode is tools_with_synthetic_data.",
    )
    synthetic_data_source: str = Field(
        description="Synthetic data source for tools, or 'not used' when mode is no_tools."
    )
    ui_visible_tool_log_behavior: str = Field(
        description="How tool calls/results are shown in the demo UI."
    )
    mocking_strategy: str = Field(
        description="How tools are mocked in tests, or no-tools mocking note when tools are absent."
    )


class CodeSpecArtifact(ArtifactBase):
    """Structured phase-3 artifact."""

    model_config = ConfigDict(extra="forbid")

    demo_overview: str = Field(description="Implementation-oriented demo overview.")
    tech_stack: TechStack = Field(description="Stack constraints and compatibility requirements.")
    openai_integration: OpenAIIntegration = Field(
        description="OpenAI API/model selection and response handling strategy."
    )
    project_changes: list[str] = Field(
        default_factory=list,
        description="Files/areas expected to change.",
    )
    components: list[str] = Field(
        default_factory=list,
        description="Core UI/system components to build.",
    )
    state_model: StateModel = Field(description="Key state model details.")
    ai_seam: AISeam = Field(description="AI seam contract and mocking strategy.")
    walkthrough_implementation: WalkthroughImplementation = Field(
        description="Implementation plan for the in-app interactive walkthrough."
    )
    synthetic_data_implementation: SyntheticDataImplementation = Field(
        description="Deterministic synthetic data setup used for first-run demo behavior."
    )
    consistency_trace: ConsistencyTrace = Field(
        description="Cross-phase mapping to keep headline capability identifiers consistent."
    )
    tooling_plan: ToolingPlan = Field(
        description="Required tooling/no-tools plan consistent with prior phase decisions."
    )
    testing_strategy: TestingStrategy = Field(
        description="Unit testing requirements, targets, and mocking guidance."
    )
    ui_constraints: UIConstraints = Field(
        description="Minimalist layout, theme, and device-frame constraints."
    )
    acceptance_tests: list[AcceptanceCriterion] = Field(
        default_factory=list,
        description="Acceptance tests to validate behavior.",
    )
    non_goals: list[str] = Field(
        default_factory=list,
        description="What this implementation intentionally excludes.",
    )
