"""Feature spec schema for phase 1 (input -> feature spec)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .common import ArtifactBase

IOModality = Literal["text", "image", "audio", "video", "file", "mixed"]


class StrictSchemaModel(BaseModel):
    """Schema model with strict unknown-field handling for structured outputs."""

    model_config = ConfigDict(extra="forbid")


class FeatureIntent(StrictSchemaModel):
    """Intent framing captured from raw input."""

    problem: str = Field(description="Core user or business problem to solve.")
    objective: str = Field(description="Primary objective for this feature.")
    desired_outcome: str = Field(description="Desired externally visible outcome.")
    target_persona: str = Field(description="Main persona this feature serves.")


class ExternalBehavior(StrictSchemaModel):
    """Externally observable behavior contract."""

    inputs: list[str] = Field(
        default_factory=list,
        description="Key inputs the feature depends on.",
    )
    outputs: list[str] = Field(
        default_factory=list,
        description="Primary outputs produced by the feature.",
    )
    states: list[str] = Field(
        default_factory=list,
        description="High level user-visible states.",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Error states users could encounter.",
    )


class ModalityDescription(StrictSchemaModel):
    """Typed modality plus plain-language description."""

    modality: IOModality = Field(
        default="text",
        description="Dominant modality used for this capability interface.",
    )
    description: str = Field(description="Human-readable details for this modality contract.")


class HeadlineAICapability(StrictSchemaModel):
    """One headline AI capability chosen for the demo."""

    name: str = Field(description="Short capability name.")
    input_modalities: list[IOModality] = Field(
        min_length=1,
        description=(
            "Explicit input modalities used by this capability (for example ['text'] or ['audio'])."
        ),
    )
    user_value: str = Field(description="Why this capability matters to users.")
    what_is_generated_or_optimized: str = Field(
        description="Specific content, decision, or optimization produced by AI."
    )
    why_ai_or_innovation_is_required: str = Field(
        description="Why deterministic logic or manual flow is insufficient."
    )
    inputs: ModalityDescription = Field(description="Primary input contract for this capability.")
    outputs: ModalityDescription = Field(description="Primary output contract for this capability.")
    demo_proof: str = Field(description="Observable in-demo proof that this capability is working.")


class AssumptionsAndConstraints(StrictSchemaModel):
    """Default assumptions and scope constraints for the generated proposal."""

    text_output_by_default: bool = Field(
        description="Whether text-first output is the default experience."
    )
    no_external_tools_unless_necessary: bool = Field(
        description="Whether external tools are excluded unless absolutely needed."
    )
    minimalist_ui: bool = Field(
        description="Whether the proposed UI intentionally keeps only essential elements."
    )
    system_theme_support: bool = Field(
        description="Whether dark/light system theme support is included."
    )
    notes: str = Field(description="Additional assumptions or caveats for reviewers.")


class GuardrailsSummary(StrictSchemaModel):
    """High-level guardrail behavior summary."""

    off_topic_short_circuit: str = Field(
        description="How off-topic requests are identified and short-circuited."
    )
    unsafe_or_disallowed_short_circuit: str = Field(
        description="How unsafe/disallowed requests are refused or diverted safely."
    )
    allowed_summary: str = Field(description="Summary of accepted request patterns.")
    refused_summary: str = Field(description="Summary of refusal behavior.")


class ToolingNeedAssessment(StrictSchemaModel):
    """Explicit tool requirement decision for this feature proposal."""

    needs_tools: bool = Field(description="Whether tools are required to demo core value.")
    why_tools_needed: str = Field(
        description="Rationale for tool use, or 'not needed' when tools are unnecessary."
    )


class InnovationFocus(StrictSchemaModel):
    """AI-first framing for this feature specification."""

    ai_headline_capabilities: list[HeadlineAICapability] = Field(
        min_length=1,
        max_length=3,
        description="One to three headline AI capabilities that define the demo scope.",
    )
    assumptions_and_constraints: AssumptionsAndConstraints = Field(
        description="Default constraints to keep scope small and AI-first."
    )
    guardrails_summary: GuardrailsSummary = Field(
        description="Concise summary of allowed/refused behavior guardrails."
    )
    tooling_need_assessment: ToolingNeedAssessment = Field(
        description="Decision and rationale for whether external tooling is needed."
    )


class HeadlineAcceptanceCriterion(StrictSchemaModel):
    """Acceptance criterion tied to one headline AI capability."""

    capability_ref: str = Field(
        description="Reference to one innovation_focus.ai_headline_capabilities[*].name entry."
    )
    given: str = Field(description="Scenario precondition.")
    when: str = Field(description="Action/event under test.")
    then: list[str] = Field(
        min_length=1,
        description="Expected outcomes after the action/event.",
    )


class FeatureSpecArtifact(ArtifactBase):
    """Structured phase-1 artifact."""

    model_config = ConfigDict(extra="forbid")

    intent: FeatureIntent = Field(description="Problem and goal framing.")
    external_behavior: ExternalBehavior = Field(description="Behavior contract summary.")
    innovation_focus: InnovationFocus = Field(
        description="AI-first framing, guardrails, and capability selection for this feature."
    )
    acceptance_criteria: list[HeadlineAcceptanceCriterion] = Field(
        min_length=1,
        description=(
            "Acceptance criteria explicitly scoped to the selected headline AI capabilities "
            "via capability_ref."
        ),
    )
    excluded_plumbing: list[str] = Field(
        min_length=1,
        description=(
            "Common plumbing explicitly out of scope unless required by the proposal "
            "(for example: auth, roles, billing, audit logs, observability, feature flags, "
            "rate limits, queues/jobs, multi-tenancy, admin tooling, deployment/CI/CD)."
        ),
    )
    invariants: list[str] = Field(
        default_factory=list,
        description="Rules that should always remain true.",
    )
    success_metrics: list[str] = Field(
        default_factory=list,
        description="Signals indicating the feature achieved expected outcomes.",
    )
