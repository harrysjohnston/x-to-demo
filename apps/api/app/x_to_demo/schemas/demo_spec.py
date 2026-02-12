"""Demo spec schema for phase 2 (feature spec -> demo spec)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .common import ArtifactBase


class DemoScope(BaseModel):
    """Scope boundaries for the demo artifact."""

    in_scope: list[str] = Field(
        default_factory=list,
        description="Behaviors included in the demo.",
    )
    out_of_scope: list[str] = Field(
        default_factory=list,
        description="Behaviors explicitly excluded from the demo.",
    )


class DemoSpecArtifact(ArtifactBase):
    """Structured phase-2 artifact."""

    demo_overview: str = Field(description="One-paragraph description of the demo outcome.")
    demo_scope: DemoScope = Field(description="In/out scope boundaries.")
    demo_format: str = Field(description="How the demo is delivered/presented.")
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
