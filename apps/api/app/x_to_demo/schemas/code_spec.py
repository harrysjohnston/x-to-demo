"""Code spec schema for phase 3 (demo spec -> code spec)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .common import AcceptanceCriterion, ArtifactBase

REQUIRED_AGENT_SKILLS_TO_APPLY: tuple[str, ...] = (
    "demo-e2e",
    "canonical-spec-format-parity",
    "openai-live-integration-tests",
)


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


class OpenAIRequestValidation(StrictSchemaModel):
    """Preflight validation and fail-fast error behavior for OpenAI requests."""

    preflight_checks: list[str] = Field(
        min_length=1,
        description=(
            "Concrete checks run before sending any OpenAI request, including model name "
            "validation, required field presence, and structured-output schema constraint "
            "validation for strict compatibility."
        ),
    )
    fail_fast_behavior: str = Field(
        description=(
            "Fail-fast behavior when validation fails. Must state that no request is sent and "
            "that a clear error message is surfaced in the UI."
        )
    )
    ui_error_state_contract: str = Field(
        description=(
            "UI-visible error contract describing where validation failures are shown and how "
            "users recover (for example retry/reset/fix configuration)."
        )
    )
    debug_logging_policy: str = Field(
        description=(
            "Debug metadata logging policy (request id, model, timings, status, schema parse "
            "outcome) that explicitly forbids persisting sensitive content such as raw prompts, "
            "raw responses, or API keys."
        )
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
    request_validation: OpenAIRequestValidation = Field(
        description="Required preflight validation and fail-fast UI error behavior."
    )


class AssetGenerationGuardrails(StrictSchemaModel):
    """Mandatory guardrails for synthetic asset generation."""

    no_real_person_likeness: Literal[True] = Field(
        description="Must be true: generated assets must not depict real-person likenesses."
    )
    no_copyrighted_brand_assets: Literal[True] = Field(
        description=(
            "Must be true: generated assets must not include copyrighted logos, characters, or identifiable IP."
        )
    )
    no_pii: Literal[True] = Field(
        description="Must be true: generated assets must not include personally identifiable information."
    )
    content_safety_notes: str = Field(
        description="Additional prompt/content safety constraints, or 'none' when no extras are needed."
    )


class AssetGenerationAPIChoice(StrictSchemaModel):
    """API/model choice by asset modality."""

    asset_type: Literal["text", "image", "audio"] = Field(
        description="Asset modality this API/model choice applies to."
    )
    openai_api_surface: Literal["responses", "realtime", "agents"] = Field(
        description="OpenAI API surface used to generate this asset type."
    )
    model: str = Field(
        description=(
            "Model identifier for this asset type. Prefer defaults (gpt-5.2 for responses/agents and "
            "gpt-realtime for realtime) unless demo-specific requirements justify overrides."
        )
    )
    why_this_choice: str = Field(
        description="Short rationale tied to quality, cost, determinism, and demo requirements."
    )


class AssetGenerationPlan(StrictSchemaModel):
    """Plan for generating required synthetic text/image/audio assets in repo."""

    when_assets_are_required: str = Field(
        description=(
            "Explicit rule for DemoSpec.synthetic_demo_inputs.required_assets: if empty, no generation "
            "is needed; if non-empty, generate assets and commit them to the repository."
        )
    )
    api_and_model_by_asset_type: list[AssetGenerationAPIChoice] = Field(
        min_length=1, description="Per-modality OpenAI API/model choices used for asset generation."
    )
    generation_commands_or_scripts: list[str] = Field(
        min_length=1,
        description="Concrete local commands/scripts for deterministic-ish synthetic asset generation.",
    )
    repo_storage_location: str = Field(
        description="In-repo storage path for generated synthetic assets."
    )
    naming_convention: str = Field(
        description="Stable naming convention that includes asset_id and synthetic status."
    )
    how_app_loads_and_references_assets: str = Field(
        description="How runtime loads and references generated assets in seeded demo flows."
    )
    explicit_synthetic_labeling_in_app: str = Field(
        description="How the app visibly labels generated assets as synthetic in relevant UI surfaces."
    )
    guardrails: AssetGenerationGuardrails = Field(
        description="Mandatory content/safety guardrails for generation."
    )
    no_live_generation_on_startup: Literal[True] = Field(
        description="Must be true: app startup must not depend on live asset generation calls."
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


class RelevanceVerdict(StrictSchemaModel):
    """Structured-output verdict from relevance guardrail model call."""

    is_relevant: bool = Field(
        description="Whether runtime input is relevant to supported demo scope."
    )
    reason: str = Field(description="Internal/logging reason for the relevance verdict.")
    user_message: str = Field(description="User-facing relevance message shown on reject.")


class SafetyVerdict(StrictSchemaModel):
    """Structured-output verdict from safety guardrail model call."""

    is_safe: bool = Field(description="Whether runtime input passes safety policy.")
    reason: str = Field(description="Internal/logging reason for the safety verdict.")
    user_message: str = Field(description="User-facing safety message shown on reject.")


class RuntimeGuardrailsPlan(StrictSchemaModel):
    """Server-side runtime guardrails plan before main AI execution."""

    server_side_only: Literal[True] = Field(
        default=True,
        description="Must be true: runtime guardrails execute server-side only.",
    )
    deterministic_type_checks: list[str] = Field(
        default_factory=lambda: [
            "Validate supported modality and mime/format before model calls.",
            "Validate payload/file size constraints before processing.",
            "Return unsupported verdict for unsupported modality/format.",
        ],
        description="Deterministic type/format/size checks run before relevance/safety model calls.",
    )
    relevance_model_call: str = Field(
        default="Use configured default model for relevance structured-output call.",
        description="Demo-specific relevance model call (model id or selection rule).",
    )
    relevance_prompt_contract: str = Field(
        default=(
            "Pass demo scope context, supported modalities, and runtime input summary; require JSON-only output."
        ),
        description="Prompt contract for relevance model call.",
    )
    relevance_output_schema: str = Field(
        default="RelevanceVerdict { is_relevant: bool, reason: str, user_message: str }",
        description="Output schema contract for relevance verdict.",
    )
    safety_model_call: str = Field(
        default="Use configured default model for safety structured-output call.",
        description="Demo-specific safety model call (model id or selection rule).",
    )
    safety_prompt_contract: str = Field(
        default=(
            "Pass runtime input summary and policy context; require JSON-only output with safety verdict."
        ),
        description="Prompt contract for safety model call.",
    )
    safety_output_schema: str = Field(
        default="SafetyVerdict { is_safe: bool, reason: str, user_message: str }",
        description="Output schema contract for safety verdict.",
    )
    verdict_handling: str = Field(
        default=(
            "unsupported -> show not-supported message and stop; block -> show safety message and stop; allow -> continue."
        ),
        description="Mapping of unsupported/block/allow outcomes to flow behavior.",
    )
    logging_policy: str = Field(
        default=(
            "Log request ids, verdicts, timings, and schema-parse outcomes only; never persist raw runtime content."
        ),
        description="Guardrails logging policy aligned with request validation no-raw-content constraints.",
    )


class AISeamGuardrails(StrictSchemaModel):
    """Input filtering and refusal behavior at the AI seam."""

    input_filters: list[str] = Field(
        min_length=1,
        description="Deterministic input checks enforced before guardrail model calls.",
    )
    refusal_policy: str = Field(description="Refusal policy and message behavior.")
    short_circuit_behavior: str = Field(
        description="Short-circuit behavior for disallowed or off-topic requests."
    )
    runtime_guardrails_plan: RuntimeGuardrailsPlan = Field(
        default_factory=RuntimeGuardrailsPlan,
        description=(
            "Explicit server-side runtime guardrails plan with deterministic checks, relevance call, and safety call."
        ),
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


class MockedTestTier(StrictSchemaModel):
    """Mocked OpenAI tests that run by default in local and CI flows."""

    always_run_by_default: Literal[True] = Field(
        description="Must be true: mocked tests run by default in CI/local."
    )
    coverage_requirements: list[str] = Field(
        min_length=1,
        description=(
            "Mocked-test coverage requirements, including request payload formation, schema "
            "parsing/validation, guardrail short-circuit behavior, and tool-call display "
            "behavior when tools are present."
        ),
    )
    mocking_strategy: str = Field(
        description=(
            "Deterministic OpenAI mocking strategy (fixtures/snapshots) aligned to the test plan."
        )
    )


class LiveSmokeTestTier(StrictSchemaModel):
    """Opt-in live smoke tests that validate real OpenAI connectivity safely."""

    opt_in: Literal[True] = Field(description="Must be true: live smoke tests are opt-in only.")
    run_condition: str = Field(
        description=(
            "Exact run condition for live smoke tests, explicitly gated by OPENAI_API_KEY and "
            "optionally a dedicated opt-in flag such as RUN_LIVE_OPENAI_TESTS=1."
        )
    )
    skip_behavior: str = Field(
        description=(
            "Skip behavior contract: tests are safe to skip when not opted in and report as "
            "skipped (not failed) in the default suite."
        )
    )
    cost_and_safety_constraints: list[str] = Field(
        min_length=1,
        description=(
            "Low-cost safety constraints for live tests (minimal calls, default models, low "
            "token usage, deterministic assertions where feasible)."
        ),
    )
    what_it_verifies: list[str] = Field(
        min_length=1,
        description=(
            "Capabilities verified by live smoke tests, including request success, response parse "
            "success, and expected UI/state update for at least one headline flow."
        ),
    )
    commands_or_how_to_run: list[str] = Field(
        min_length=1, description="Concrete commands or steps for running live smoke tests locally."
    )


class OpenAITestTiers(StrictSchemaModel):
    """Required two-tier OpenAI testing strategy."""

    mocked: MockedTestTier = Field(description="Mocked unit/integration tests (default tier).")
    live_smoke: LiveSmokeTestTier = Field(
        description="Opt-in live integration smoke tests (gated tier)."
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
    openai_test_tiers: OpenAITestTiers = Field(
        description=(
            "Required two-tier OpenAI tests: mocked tests run by default and live smoke tests "
            "run only when explicitly opted in (for example OPENAI_API_KEY plus flag)."
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
    synthetic_assets_validation: str = Field(
        description=(
            "Required synthetic-asset validation plan covering expected repo-path existence, basic "
            "file sanity checks (type/extension, non-zero size, configured size limits), and proof "
            "that seeded startup flows run without live asset-generation network calls."
        )
    )
    preset_inputs_integration_coverage: str = Field(
        default=(
            "Integration tests iterate every preset, apply preset values, execute guardrails, and "
            "verify the flow can reach mocked main AI execution."
        ),
        description=(
            "Preset integration coverage contract that is explicit, deterministic, and implementable."
        ),
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
    auto_apply_default_preset_on_load: str = Field(
        default="Select and apply the default preset to UI inputs only; do not execute automatically.",
        description=(
            "How the default preset is selected and applied on load (populate only; execution requires explicit run action)."
        ),
    )
    auto_populate_first_run: str | None = Field(
        default=None,
        description=(
            "Deprecated legacy field retained for compatibility with older artifacts that used auto-run phrasing."
        ),
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
    agent_skills_to_apply: list[str] = Field(
        default_factory=lambda: list(REQUIRED_AGENT_SKILLS_TO_APPLY),
        min_length=1,
        description=(
            "Skill slugs required for implementation. Must include the baseline demo skill, format parity, and live OpenAI test guidance."
        ),
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
    asset_generation_plan: AssetGenerationPlan = Field(
        description=(
            "Required plan for generating needed synthetic assets via OpenAI APIs and committing "
            "them to the repository."
        )
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

    @model_validator(mode="after")
    def ensure_required_agent_skills(self) -> CodeSpecArtifact:
        """Ensure mandatory implementation skills are always present."""
        skills = list(dict.fromkeys([*self.agent_skills_to_apply, *REQUIRED_AGENT_SKILLS_TO_APPLY]))
        if self.openai_integration.covers_requires_voice:
            skills = list(dict.fromkeys([*skills, "multimodal-inputs"]))
        self.agent_skills_to_apply = skills
        return self
