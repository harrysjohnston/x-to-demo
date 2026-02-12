"""Code spec schema for phase 3 (demo spec -> code spec)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .common import AcceptanceCriterion, ArtifactBase


class TechStack(BaseModel):
    """High-level stack decisions for the implementation."""

    frontend: str = Field(description="Primary frontend framework/runtime.")
    backend: str | None = Field(
        default=None,
        description="Primary backend system when relevant.",
    )
    language: str = Field(description="Primary implementation language.")


class StateModel(BaseModel):
    """Top-level state fields surfaced by the implementation."""

    fields: list[str] = Field(
        default_factory=list,
        description="Key state fields to model explicitly.",
    )


class AISeam(BaseModel):
    """Model/tooling contract boundary in the implementation."""

    schemas: list[str] = Field(
        default_factory=list,
        description="Schema contracts used at the AI seam.",
    )
    contracts: list[str] = Field(
        default_factory=list,
        description="Function/protocol contracts for AI-driven components.",
    )
    mock_strategy: str = Field(description="How AI dependencies are mocked in local/dev flows.")


class CodeSpecArtifact(ArtifactBase):
    """Structured phase-3 artifact."""

    demo_overview: str = Field(description="Implementation-oriented demo overview.")
    tech_stack: TechStack = Field(description="Recommended stack choices.")
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
    acceptance_tests: list[AcceptanceCriterion] = Field(
        default_factory=list,
        description="Acceptance tests to validate behavior.",
    )
    non_goals: list[str] = Field(
        default_factory=list,
        description="What this implementation intentionally excludes.",
    )
