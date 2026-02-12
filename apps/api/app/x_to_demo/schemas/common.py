"""Shared schema types for x-to-demo artifacts."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

ArtifactStatus = Literal["draft", "review", "ready"]


class SourceInfo(BaseModel):
    """Traceability metadata for a generated artifact."""

    x_source_type: str = Field(
        default="text",
        description="Type of source material used to derive this artifact.",
    )
    inputs: list[str] = Field(
        default_factory=list,
        description="Named upstream inputs consumed by this phase.",
    )
    notes: str = Field(
        default="",
        description="Extra provenance notes relevant for reviewers.",
    )


class AcceptanceCriterion(BaseModel):
    """Behavioral acceptance criterion in Given/When/Then format."""

    given: str = Field(description="Scenario precondition.")
    when: str = Field(description="Action/event under test.")
    then: list[str] = Field(
        min_length=1,
        description="Expected outcomes after the action/event.",
    )


class VersioningInfo(BaseModel):
    """Simple version metadata carried by each phase output."""

    version: str = Field(default="0.1.0", description="Semantic-ish version label.")
    changelog: list[str] = Field(
        default_factory=lambda: ["Initial draft"],
        description="Human readable change notes.",
    )
    updated_at_utc: str = Field(
        default_factory=lambda: datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        description="Last update timestamp in UTC ISO-like format.",
    )


class ArtifactBase(BaseModel):
    """Common top-level fields shared by all artifact schemas."""

    schema_version: str = Field(
        default="0.1",
        description="Schema version for this artifact payload.",
    )
    feature_name: str = Field(description="Stable feature name for this run.")
    status: ArtifactStatus = Field(
        default="draft",
        description="Lifecycle status used for review flow.",
    )
    source: SourceInfo = Field(description="Source and provenance metadata.")
