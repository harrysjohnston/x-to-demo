"""Demo spec schema for phase 2 (feature spec -> demo spec)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .common import ArtifactBase

InteractionMode = Literal[
    "text_chat",
    "image_upload",
    "voice",
    "multi_step_agent",
    "multimodal",
]


class StrictSchemaModel(BaseModel):
    """Schema model with strict unknown-field handling for structured outputs."""

    model_config = ConfigDict(extra="forbid")


class DemoScope(StrictSchemaModel):
    """Scope boundaries for the demo artifact."""

    in_scope: list[str] = Field(
        default_factory=list,
        description="Minimal set of showcase behaviors included in the demo.",
    )
    out_of_scope: list[str] = Field(
        default_factory=list,
        description=(
            "Behaviors explicitly excluded from the demo, including non-essential plumbing "
            "unless directly required."
        ),
    )


class HeadlineDemoItem(StrictSchemaModel):
    """One headline demo item mapped to a phase-1 capability."""

    capability_ref: str = Field(
        description="Reference to one phase-1 innovation_focus.ai_headline_capabilities[*].name."
    )
    interaction_mode: InteractionMode = Field(
        description=(
            "Primary interaction mode for this item (for example text chat, image upload, voice, or multi-step agent)."
        )
    )
    user_story_in_demo: str = Field(description="Focused user story demonstrated in this item.")
    ai_moment: str = Field(
        description="The model-call moment and why it is innovative for the user."
    )
    success_looks_like: str = Field(description="Observable success condition for this demo item.")


class AIPipelineDelineation(StrictSchemaModel):
    """Boundaries between AI and non-AI components in the demo."""

    ai_components: list[str] = Field(
        min_length=1,
        description="Components or steps where AI performs the core value-generating work.",
    )
    non_ai_components: list[str] = Field(
        min_length=1,
        description="Supporting components that are deterministic or presentation-focused.",
    )
    where_innovation_lives: str = Field(
        description="Direct explanation of where technical innovation resides."
    )


class MinimalistView(StrictSchemaModel):
    """Minimal UI view used in the demo experience."""

    name: str = Field(description="Short view name.")
    purpose: str = Field(description="Why this view exists in the demo.")
    primary_component: str = Field(description="Main interactive or display component.")
    visible_elements: list[str] = Field(
        min_length=1,
        description="UI elements intentionally visible in this minimal view.",
    )
    hidden_or_omitted_elements: list[str] = Field(
        default_factory=list,
        description="UI elements intentionally hidden or omitted for minimalism.",
    )


class ControlLoadingState(StrictSchemaModel):
    """Loading/working-state behavior contract for one control."""

    has_loading_state: bool = Field(
        description="Whether the control shows a loading/working state when activated."
    )
    loading_ui_behavior: str = Field(
        description=(
            "What the UI does while loading (spinner/disabled/label change), and what ends "
            "the loading state. Use 'not applicable' if has_loading_state is false."
        )
    )


class ControlEnablementRules(StrictSchemaModel):
    """Enable/disable rules and disabled explanation for one control."""

    enabled_when: list[str] = Field(
        min_length=1,
        description="Concrete conditions under which the control is enabled.",
    )
    disabled_when: list[str] = Field(
        min_length=1,
        description="Concrete conditions under which the control is disabled.",
    )
    disabled_explanation: str = Field(
        description="What the UI shows/explains when disabled (tooltip/helper text/inline message)."
    )


class InteractiveControlContract(StrictSchemaModel):
    """Functional contract for one interactive control."""

    control_id: str = Field(
        description="Stable identifier for the control used for mapping into tests and walkthrough targets."
    )
    label_or_icon_description: str = Field(
        description="User-visible label, or icon description when the control is icon-only."
    )
    control_type: str = Field(
        description="Type of control (button, toggle, text input, select, slider, and similar)."
    )
    expected_behavior: str = Field(
        description="Exactly what happens when the user interacts with the control."
    )
    observable_state_or_ui_change: str = Field(
        description=(
            "Observable UI/state signal that proves the control worked (state change, navigation, "
            "new content, toast/message, tool-call log entry, and similar). If the control is "
            "disabled in some states, this should describe enabled-state behavior."
        )
    )
    enablement_rules: ControlEnablementRules = Field(
        description="Enable/disable rules and disabled explanation."
    )
    loading_state: ControlLoadingState = Field(
        description="Loading/working UI behavior for this control."
    )


class ScreenInteractionContracts(StrictSchemaModel):
    """Per-screen inventory of interactive controls and their behavior contracts."""

    screen_name: str = Field(
        description=(
            "Name of the screen/view this contract applies to. Must match one of "
            "DemoExperience.minimalist_views[*].name."
        )
    )
    controls: list[InteractiveControlContract] = Field(
        min_length=1,
        description="Inventory of every interactive control on this screen.",
    )
    notes: str = Field(description="Clarifying notes for this screen's interactions (or 'none').")


class ThemeSupport(StrictSchemaModel):
    """Theme support constraints for the demo UI."""

    system_dark_light: Literal[True] = Field(
        description="Must be true: demo UI follows system dark/light preference."
    )


class SmartphoneFrame(StrictSchemaModel):
    """Optional smartphone frame metadata for mobile-like demos."""

    enabled: bool = Field(
        description=(
            "Enable smartphone frame only when device_target.is_mobile_like is true; "
            "otherwise set explicitly to false."
        )
    )
    width: int | None = Field(default=None, description="Optional frame width in CSS pixels.")
    height: int | None = Field(default=None, description="Optional frame height in CSS pixels.")
    bezel_style: str | None = Field(
        default=None,
        description="Optional bezel style descriptor when frame is enabled.",
    )


class DeviceTarget(StrictSchemaModel):
    """Device-targeting constraints for demo rendering."""

    is_mobile_like: bool = Field(description="Whether the proposed demo is mobile-app-like.")
    smartphone_frame: SmartphoneFrame = Field(
        description=(
            "Smartphone frame details. For non-mobile demos, smartphone_frame.enabled "
            "must be false."
        )
    )


class DemoExperience(StrictSchemaModel):
    """UI experience constraints for a minimalist, browser-compatible demo."""

    minimalist_views: list[MinimalistView] = Field(
        min_length=1,
        description="Minimal set of views that deliver the full demo experience.",
    )
    theme_support: ThemeSupport = Field(description="System theme requirements.")
    device_target: DeviceTarget = Field(description="Device framing requirements.")


class WalkthroughControls(StrictSchemaModel):
    """User controls available in the in-app walkthrough."""

    next: Literal[True] = Field(description="Must be true: walkthrough supports next.")
    back: bool = Field(description="Whether walkthrough supports navigating backward.")
    cancel: Literal[True] = Field(description="Must be true: walkthrough supports cancellation.")


class WalkthroughStep(StrictSchemaModel):
    """Single in-app walkthrough step tied to UI and AI behavior."""

    id: str = Field(description="Stable step identifier.")
    title: str = Field(description="Short step title.")
    ui_target: str = Field(description="UI element or region targeted by this step.")
    explanation: str = Field(description="What this step explains to the user.")
    what_ai_does_here: str = Field(
        description="Concise explanation of the AI behavior at this step."
    )
    success_criteria: str = Field(description="How this step's completion is verified.")


class InteractiveWalkthrough(StrictSchemaModel):
    """In-app interactive walkthrough requirements."""

    auto_start_on_launch: Literal[True] = Field(
        description="Must be true: walkthrough auto-starts on demo launch."
    )
    retrigger_mechanism: str = Field(
        description="How users can retrigger the walkthrough from inside the app."
    )
    controls: WalkthroughControls = Field(description="Required walkthrough controls.")
    steps: list[WalkthroughStep] = Field(
        min_length=1,
        description=(
            "In-app guided tour steps. This is not a presenter script or external instructions."
        ),
    )


class ToolingPlanIfNeeded(StrictSchemaModel):
    """Explicitly records tool usage decision and demo-time visibility."""

    mode: Literal["no_tools", "tools_with_synthetic_data"] = Field(
        description="Explicitly choose no tools or tools backed by synthetic data."
    )
    rationale: str = Field(
        description="Why this mode was selected; use 'not needed' when no tools are used."
    )
    tool_definitions: list[str] = Field(
        default_factory=list,
        description="Tool definitions used when mode is tools_with_synthetic_data.",
    )
    synthetic_data_source: str = Field(
        description="Synthetic data source description; use 'not used' when mode is no_tools."
    )
    ui_visible_tool_call_log: bool = Field(
        description="Whether the UI visibly displays tool calls and results."
    )


class EmbeddedDataObject(StrictSchemaModel):
    """Compact embedded synthetic dataset/object representation."""

    summary: str = Field(description="What this embedded object contains.")
    sample_records: list[str] = Field(
        min_length=1,
        description="Small deterministic sample records used by the demo.",
    )


TextOrEmbeddedData = str | EmbeddedDataObject


class PresetInputSet(StrictSchemaModel):
    """Global synthetic preset that can populate runtime inputs."""

    preset_id: str = Field(description="Stable preset identifier.")
    label: str = Field(description="User-facing preset label.")
    ordered_inputs: list[str] = Field(
        min_length=1,
        description="Deterministic ordered runtime inputs populated by this preset.",
    )
    where_used_in_headline_flows: list[str] = Field(
        default_factory=list,
        description="Capability refs or walkthrough step ids where this preset is used.",
    )
    expected_outputs: TextOrEmbeddedData = Field(
        description="Expected output if the user explicitly runs this preset."
    )
    notes: str = Field(description="Additional preset notes, or 'none'.")


class FirstRunInputSet(StrictSchemaModel):
    """Legacy first-run input contract retained for markdown compatibility helpers."""

    ordered_inputs: list[str] = Field(
        min_length=1,
        description="Legacy ordered inputs migrated into presets.",
    )
    trigger_action: str = Field(
        description="Legacy trigger text migrated to explicit preset execution behavior."
    )


class RequiredSyntheticAsset(StrictSchemaModel):
    """Required synthetic text/image/audio asset inventory entry for deterministic demos."""

    asset_id: str = Field(
        description=(
            "Stable identifier for this asset used for cross-phase references and test mapping."
        )
    )
    asset_type: Literal["text", "image", "audio"] = Field(description="Asset modality/type.")
    purpose: str = Field(
        description="Why this asset is needed (seeded scenario, example upload, UI preview, and similar)."
    )
    where_used_in_headline_flows: list[str] = Field(
        min_length=1,
        description=(
            "Headline demo item or step references that use this asset, using stable IDs or explicit references."
        ),
    )
    expected_format: str = Field(
        description=(
            "Expected file/text format and constraints (for example png 1024x1024, wav 16kHz mono, plain text <= 1KB)."
        )
    )
    size_constraints: str = Field(
        description="Max size guidance suitable for in-repo demo assets and fast load times."
    )
    must_be_labeled_synthetic: Literal[True] = Field(
        description="Must be true: this asset is explicitly labeled synthetic."
    )
    synthetic_label_text: str = Field(
        description="Exact synthetic label text shown for this asset in the demo."
    )


class SyntheticDemoInputs(StrictSchemaModel):
    """Synthetic-first dataset and selectable presets for deterministic demos."""

    seed_dataset: TextOrEmbeddedData = Field(
        description="Small safe seed dataset (embedded text or structured object)."
    )
    input_presets: list[PresetInputSet] = Field(
        default_factory=lambda: [
            PresetInputSet(
                preset_id="default-preset",
                label="Default preset",
                ordered_inputs=["Synthetic preset input"],
                where_used_in_headline_flows=[],
                expected_outputs="Expected output after explicit run action.",
                notes="none",
            )
        ],
        min_length=1,
        description="Global selectable presets used to populate runtime inputs.",
    )
    default_selected_preset_id: str = Field(
        default="default-preset",
        description="Preset id that should be selected by default in the UI.",
    )
    preset_application_behavior: str = Field(
        default=(
            "Applying a preset populates runtime input fields only; it does not execute the flow."
        ),
        description="Must state that applying a preset populates UI only and does not execute.",
    )
    preset_execution_behavior: str = Field(
        default=(
            "Preset execution requires explicit user action (Run/Submit) after inputs are populated."
        ),
        description="Must state that running a preset requires explicit user action.",
    )
    why_this_data: str = Field(
        description="How the synthetic data covers the one-to-three headline demo items."
    )
    safety_and_realism_notes: str = Field(
        description="Confirms non-PII safe data while preserving realistic but bounded behavior."
    )
    expected_outputs: TextOrEmbeddedData = Field(
        description="Expected first-run outputs as concise text or structured object."
    )
    required_assets: list[RequiredSyntheticAsset] = Field(
        description=(
            "Required inventory of synthetic text/image/audio assets needed for deterministic demo runs. "
            "Use an empty list when no extra assets are needed."
        )
    )

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_default_first_run_inputs(cls, value: object) -> object:
        """Migrate legacy default_first_run_inputs into the new preset-based fields."""
        if not isinstance(value, dict):
            return value

        data = dict(value)
        legacy = data.pop("default_first_run_inputs", None)
        if isinstance(legacy, dict) and "input_presets" not in data:
            ordered_inputs = legacy.get("ordered_inputs")
            if not isinstance(ordered_inputs, list) or not ordered_inputs:
                ordered_inputs = ["Legacy preset input (update required)."]

            preset_id = "legacy-default-first-run"
            data["input_presets"] = [
                {
                    "preset_id": preset_id,
                    "label": "Legacy default preset",
                    "ordered_inputs": ordered_inputs,
                    "where_used_in_headline_flows": [],
                    "expected_outputs": data.get(
                        "expected_outputs",
                        "Expected output after explicit run action.",
                    ),
                    "notes": "Migrated from legacy default_first_run_inputs.",
                }
            ]
            data.setdefault("default_selected_preset_id", preset_id)

            trigger_action = legacy.get("trigger_action")
            if isinstance(trigger_action, str) and trigger_action.strip():
                data.setdefault(
                    "preset_execution_behavior",
                    (
                        "Execution requires explicit user action (Run/Submit). "
                        f"Legacy trigger note: {trigger_action.strip()}"
                    ),
                )
            else:
                data.setdefault(
                    "preset_execution_behavior",
                    "Execution requires explicit user action (Run/Submit) after applying a preset.",
                )

            data.setdefault(
                "preset_application_behavior",
                "Applying a preset populates runtime input fields only; it does not execute.",
            )

        if "default_selected_preset_id" not in data:
            presets = data.get("input_presets")
            if isinstance(presets, list) and presets:
                first = presets[0]
                if isinstance(first, dict):
                    preset_id = first.get("preset_id")
                    if isinstance(preset_id, str) and preset_id.strip():
                        data["default_selected_preset_id"] = preset_id

        return data

    @property
    def default_first_run_inputs(self) -> FirstRunInputSet:
        """Compatibility projection for callers that still render legacy first-run sections."""
        first_preset = self.input_presets[0]
        return FirstRunInputSet(
            ordered_inputs=first_preset.ordered_inputs,
            trigger_action=self.preset_execution_behavior,
        )


class ConsistencyTrace(StrictSchemaModel):
    """Cross-phase consistency commitments between phase 1 and phase 2."""

    phase1_headline_capability_refs: list[str] = Field(
        min_length=1,
        max_length=3,
        description="Stable phase-1 headline capability identifiers used by this demo spec.",
    )
    stable_identifier_rule: str = Field(
        description="Rule to preserve stable capability identifiers across phases."
    )
    walkthrough_alignment_summary: str = Field(
        description="How walkthrough steps align to the same headline capability set."
    )


class ToolingDecisionTrace(StrictSchemaModel):
    """Trace of tooling decision carried forward from phase 1."""

    phase1_needs_tools: bool = Field(
        description="Tooling decision inherited from phase-1 tooling_need_assessment.needs_tools."
    )
    phase1_why_tools_needed: str = Field(
        description="Phase-1 rationale summary for the tooling decision."
    )
    must_remain_consistent: Literal[True] = Field(
        description="Must be true: phase-2 tooling cannot contradict phase-1 tooling decision."
    )
    consistency_notes: str = Field(
        description="Notes describing how tooling_plan_if_needed follows the phase-1 decision."
    )


class InteractionRequirements(StrictSchemaModel):
    """Cross-item interaction signals forwarded to phase 3 API selection."""

    requires_voice: bool = Field(
        description="True when any headline demo item requires live voice/audio interaction."
    )
    requires_tool_loop: bool = Field(
        description="True when any headline demo item requires iterative tool-use/planning loops."
    )


class RuntimeInputAndGuardrails(StrictSchemaModel):
    """Demo-specific runtime input contract and server-side guardrails behavior."""

    accepts_runtime_inputs: Literal[True] = Field(
        default=True, description="Must be true: demo accepts runtime inputs from the UI."
    )
    supported_input_modalities: list[str] = Field(
        default_factory=lambda: ["text"],
        description="Demo-specific runtime input modalities accepted by the UI/API.",
    )
    input_capture_summary: str = Field(
        default="Runtime inputs are captured from visible UI controls in the demo views.",
        description="What runtime inputs the UI accepts and where.",
    )
    guardrails_pipeline_summary: list[str] = Field(
        default_factory=lambda: [
            "Deterministic type/format/size checks",
            "Relevance model call with structured output verdict",
            "Safety model call with structured output verdict",
        ],
        description="Ordered guardrail pipeline summary including type, relevance, and safety.",
    )
    relevance_check_summary: str = Field(
        default="Server performs a relevance model call that returns a structured relevance verdict.",
        description="Summary of the relevance model-call guardrail.",
    )
    safety_check_summary: str = Field(
        default="Server performs a safety model call that returns a structured safety verdict.",
        description="Summary of the safety model-call guardrail.",
    )
    user_visible_outcomes_on_reject: list[str] = Field(
        default_factory=lambda: [
            "Show an unsupported-input message in the input panel.",
            "Show a safety/relevance rejection message near the run action.",
        ],
        description="User-visible reject outcomes and where messages appear.",
    )
    cancel_flow_behavior: str = Field(
        default=(
            "On reject, cancel before the main model call, preserve current UI state, and allow "
            "user edits/retry."
        ),
        description=(
            "Must explicitly state no main model call occurs on reject; UI state is preserved and "
            "edit/try-again remains available."
        ),
    )
    presets_go_through_same_guardrails: Literal[True] = Field(
        default=True,
        description="Must be true: preset-populated inputs use the same guardrails pipeline.",
    )


class DemoSpecArtifact(ArtifactBase):
    """Structured phase-2 artifact."""

    model_config = ConfigDict(extra="forbid")

    demo_overview: str = Field(description="One-paragraph description of the demo outcome.")
    demo_scope: DemoScope = Field(
        description="In/out scope boundaries consistent with minimalism and plumbing exclusion."
    )
    demo_format: str = Field(
        description="How the demo is delivered in-app as a product showcase, not a presenter script."
    )
    headline_demo_items: list[HeadlineDemoItem] = Field(
        min_length=1,
        max_length=3,
        description="One to three headline demo items tied to phase-1 capabilities.",
    )
    interaction_requirements: InteractionRequirements = Field(
        description="Phase-2 interaction signals used to drive phase-3 API selection consistency."
    )
    ai_pipeline_delineation: AIPipelineDelineation = Field(
        description="Boundary between AI and non-AI components."
    )
    demo_experience: DemoExperience = Field(
        description="Minimalist views, device targeting, and system theme support."
    )
    interaction_contracts: list[ScreenInteractionContracts] = Field(
        min_length=1,
        description=(
            "Required per-screen inventory of every interactive control and expected behavior, "
            "including enable/disable rules and loading states."
        ),
    )
    interactive_walkthrough: InteractiveWalkthrough = Field(
        description="In-app interactive walkthrough requirements."
    )
    runtime_input_and_guardrails: RuntimeInputAndGuardrails = Field(
        default_factory=RuntimeInputAndGuardrails,
        description=(
            "Demo-specific runtime input contract and server-side guardrails behavior, including "
            "reject outcomes and cancellation semantics."
        ),
    )
    synthetic_demo_inputs: SyntheticDemoInputs = Field(
        description=(
            "Synthetic-first data package with global selectable presets that populate runtime inputs "
            "without auto-running."
        )
    )
    consistency_trace: ConsistencyTrace = Field(
        description="Cross-phase consistency commitments for stable headline identifiers."
    )
    tooling_decision_trace: ToolingDecisionTrace = Field(
        description="Trace showing tooling decision remains consistent with phase 1."
    )
    tooling_plan_if_needed: ToolingPlanIfNeeded = Field(
        description=(
            "Explicitly states either no tools used, or tools with synthetic data and "
            "a UI-visible tool-call log."
        )
    )
    core_flow_steps: list[str] = Field(
        default_factory=list,
        description="Ordered flow steps used in the demo walkthrough.",
    )
    success_signals: list[str] = Field(
        default_factory=list,
        description="Signals indicating the demo achieved its goal.",
    )
    example_copy: list[str] = Field(
        default_factory=list,
        description="Sample UI or dialogue copy snippets.",
    )
