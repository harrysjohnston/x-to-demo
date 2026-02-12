"""Feature spec schema for phase 1 (input -> feature spec)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .common import AcceptanceCriterion, ArtifactBase, VersioningInfo


class FeatureIntent(BaseModel):
    """Intent framing captured from raw input."""

    problem: str = Field(description="Core user or business problem to solve.")
    objective: str = Field(description="Primary objective for this feature.")
    desired_outcome: str = Field(description="Desired externally visible outcome.")
    target_persona: str = Field(description="Main persona this feature serves.")


class ExternalBehavior(BaseModel):
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


class FeatureSpecArtifact(ArtifactBase):
    """Structured phase-1 artifact."""

    intent: FeatureIntent = Field(description="Problem and goal framing.")
    external_behavior: ExternalBehavior = Field(description="Behavior contract summary.")
    acceptance_criteria: list[AcceptanceCriterion] = Field(
        default_factory=list,
        description="Behavioral acceptance criteria.",
    )
    invariants: list[str] = Field(
        default_factory=list,
        description="Rules that should always remain true.",
    )
    success_metrics: list[str] = Field(
        default_factory=list,
        description="Signals indicating the feature achieved expected outcomes.",
    )
    versioning: VersioningInfo = Field(description="Version metadata for this artifact.")
