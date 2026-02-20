"""Shared API schemas for consistent request/response formats."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Standard error detail structure."""

    code: str = Field(description="Error code for programmatic handling")
    message: str = Field(description="Human-readable error message")
    field: str | None = Field(default=None, description="Field name if error is field-specific")


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: ErrorDetail = Field(description="Error details")


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    offset: int = Field(description="Number of items skipped")
    limit: int = Field(description="Maximum number of items returned")
    total: int | None = Field(default=None, description="Total number of items (if available)")


class ResponseEnvelope[T](BaseModel):
    """Standard response envelope wrapping data."""

    data: T = Field(description="Response data")
    meta: dict | None = Field(default=None, description="Additional metadata (e.g., pagination)")


class ListResponseEnvelope[T](BaseModel):
    """Standard response envelope for list endpoints with pagination."""

    data: list[T] = Field(description="List of items")
    meta: PaginationMeta = Field(description="Pagination metadata")


class SSEEvent(BaseModel):
    """Server-Sent Event payload."""

    event: str = Field(description="Event type name")
    data: dict[str, Any] = Field(description="Event payload data")
    id: str | None = Field(default=None, description="Event ID for resumption (Last-Event-ID)")


class XToDemoRunRequest(BaseModel):
    """Request schema for running the end-to-end X-to-Demo pipeline."""

    x_input: str = Field(
        min_length=20,
        description="Raw input X (any type; often text extracted from notes, docs, tickets, or transcripts)",
    )
    additional_context: str | None = Field(
        default=None,
        description="Optional context such as roadmap constraints or prior decisions",
    )
    feature_name_hint: str | None = Field(
        default=None,
        max_length=200,
        description="Optional feature label to guide naming in generated artifacts",
    )
    model: Literal["gpt-5.2", "gpt-5.1", "gpt-5-mini", "gpt-5-nano", "gpt-4.1-nano"] | None = Field(
        default=None,
        description="Optional model override for this run",
    )
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh"] | None = Field(
        default=None,
        description="Optional reasoning effort override for this run",
    )
    stop_after_phase: Literal["feature_spec", "demo_spec", "code_spec"] | None = Field(
        default=None,
        description="Optional phase key to stop after (inclusive) for partial execution",
    )


class XToDemoArtifact(BaseModel):
    """Single phase artifact generated during an X-to-Demo run."""

    phase_key: str = Field(description="Stable phase identifier")
    title: str = Field(description="Human-readable phase title")
    markdown: str = Field(description="Phase markdown output")
    saved_path: str = Field(description="Relative path where phase output was saved")
    json_path: str = Field(description="Relative path where canonical phase JSON was saved")
    xml_path: str = Field(description="Relative path where canonical phase XML was saved")
    json_content: dict[str, Any] = Field(description="Canonical JSON payload for this artifact")
    content_hash: str = Field(description="SHA256 hash of canonical artifact JSON")


class XToDemoRunResponse(BaseModel):
    """Response payload returned after completing the X-to-Demo pipeline."""

    run_id: str = Field(description="Unique pipeline run identifier")
    created_at: datetime = Field(description="UTC timestamp for run creation")
    model: str = Field(description="OpenAI model used for this run")
    reasoning_effort: str = Field(description="Reasoning effort used for this run")
    artifacts: list[XToDemoArtifact] = Field(description="Ordered list of phase outputs")
    final_code_spec: str | None = Field(
        default=None,
        description="Final generated code specification markdown (present when code_spec completed)",
    )
    final_code_spec_path: str | None = Field(
        default=None,
        description="Relative path to saved code spec markdown (if completed)",
    )
    stop_after_phase: Literal["feature_spec", "demo_spec", "code_spec"] = Field(
        description="Phase key this run stopped after (inclusive)",
    )
    next_phase_key: Literal["feature_spec", "demo_spec", "code_spec"] | None = Field(
        default=None,
        description="Next incomplete phase key if run is partial",
    )
    usage_totals: dict[str, int] = Field(
        description="Accumulated token usage across executed phases"
    )
    cost_totals: dict[str, float] | None = Field(
        default=None,
        description="Accumulated estimated cost totals across executed phases",
    )


class XToDemoPhaseStatus(BaseModel):
    """Manifest status summary for one pipeline phase."""

    phase_key: Literal["feature_spec", "demo_spec", "code_spec"] = Field(
        description="Stable phase identifier"
    )
    title: str = Field(description="Human-readable phase title")
    status: Literal["pending", "running", "completed", "failed", "stale"] = Field(
        description="Current phase execution status"
    )
    input_artifact_ref: str | None = Field(
        default=None,
        description="Phase key of the artifact consumed by this phase",
    )
    output_json_path: str | None = Field(
        default=None,
        description="Path to persisted canonical JSON output",
    )
    output_xml_path: str | None = Field(
        default=None,
        description="Path to persisted canonical XML output",
    )
    output_md_path: str | None = Field(
        default=None,
        description="Path to persisted markdown output",
    )
    content_hash: str | None = Field(
        default=None,
        description="SHA256 hash of the canonical JSON payload",
    )
    error: str | None = Field(default=None, description="Failure detail if phase execution failed")


class XToDemoRunDetailResponse(BaseModel):
    """Detailed run state response for inspection and resume decisions."""

    run_id: str = Field(description="Unique pipeline run identifier")
    created_at: datetime = Field(description="UTC timestamp for initial run creation")
    updated_at: datetime = Field(description="UTC timestamp for latest run update")
    model: str = Field(description="OpenAI model used for this run")
    reasoning_effort: str = Field(description="Reasoning effort used for this run")
    stop_after_phase: Literal["feature_spec", "demo_spec", "code_spec"] = Field(
        description="Configured stop-after phase for the last execution"
    )
    next_phase_key: Literal["feature_spec", "demo_spec", "code_spec"] | None = Field(
        default=None,
        description="Next phase that can be executed via resume",
    )
    phases: list[XToDemoPhaseStatus] = Field(description="Ordered phase status records")
    artifacts: list[XToDemoArtifact] = Field(description="Currently materialized artifacts")
    usage_totals: dict[str, int] = Field(description="Accumulated token usage")
    cost_totals: dict[str, float] | None = Field(
        default=None, description="Accumulated estimated cost"
    )


class XToDemoArtifactResponse(BaseModel):
    """Response model for reading a single artifact payload."""

    run_id: str = Field(description="Run identifier")
    artifact: XToDemoArtifact = Field(description="Requested artifact")


class XToDemoUpdateArtifactRequest(BaseModel):
    """Request payload for editing an artifact."""

    markdown: str | None = Field(
        default=None,
        description="Edited human-readable markdown (canonical data in .json/.xml)",
    )
    json_content: dict[str, Any] | None = Field(
        default=None,
        description="Direct canonical JSON payload edit",
    )


class XToDemoResumeRequest(BaseModel):
    """Request payload for resuming an existing run."""

    from_phase: Literal["feature_spec", "demo_spec", "code_spec"] | None = Field(
        default=None,
        description="Optional explicit phase to resume from",
    )
    stop_after_phase: Literal["feature_spec", "demo_spec", "code_spec"] | None = Field(
        default=None,
        description="Optional phase to stop after on this resume run",
    )
    use_edited_artifacts: bool = Field(
        default=True,
        description="When true, resume consumes latest edited artifact content",
    )
