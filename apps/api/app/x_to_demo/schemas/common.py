"""Shared schema types for x-to-demo artifacts."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ArtifactStatus = Literal["draft", "review", "ready"]


class SourceInfo(BaseModel):
    """Traceability metadata for a generated artifact."""

    model_config = ConfigDict(extra="forbid")

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

    model_config = ConfigDict(extra="forbid")

    given: str = Field(description="Scenario precondition.")
    when: str = Field(description="Action/event under test.")
    then: list[str] = Field(
        min_length=1,
        description="Expected outcomes after the action/event.",
    )


class VersioningInfo(BaseModel):
    """Simple version metadata carried by each phase output."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(default="0.1.0", description="Semantic-ish version label.")
    changelog: list[str] = Field(
        default_factory=lambda: ["Initial draft"],
        description="Human readable change notes.",
    )
    updated_at_utc: str = Field(
        default_factory=lambda: datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        description="Last update timestamp in UTC ISO-like format.",
    )


class SpecGenerationMetadata(BaseModel):
    """Metadata that describes how the spec was generated."""

    model_config = ConfigDict(extra="forbid")
    schema_version: str = Field(
        default="0.2",
        description="Schema version for this artifact payload.",
    )
    status: ArtifactStatus = Field(
        default="draft",
        description="Lifecycle status used for review flow.",
    )
    source: SourceInfo = Field(description="Source and provenance metadata.")
    versioning: VersioningInfo = Field(
        default_factory=VersioningInfo,
        description="Version metadata for this artifact.",
    )


class ArtifactBase(BaseModel):
    """Common top-level fields shared by all artifact schemas."""

    model_config = ConfigDict(extra="forbid")
    feature_name: str = Field(description="Stable feature name for this run.")
    spec_generation_metadata: SpecGenerationMetadata = Field(
        description=(
            "Spec generation metadata (schema version, source provenance, lifecycle status, "
            "and versioning). This metadata should be kept separate from product behavior content."
        )
    )

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_top_level_metadata(cls, value: object) -> object:
        """Backfill nested metadata from legacy top-level fields when present."""
        if not isinstance(value, dict):
            return value

        data = dict(value)
        if "spec_generation_metadata" in data:
            return data

        metadata_fields = ("schema_version", "status", "source", "versioning")
        if not any(field in data for field in metadata_fields):
            return data

        metadata: dict[str, object] = {}
        for field in metadata_fields:
            if field in data:
                metadata[field] = data.pop(field)

        data["spec_generation_metadata"] = metadata
        return data
