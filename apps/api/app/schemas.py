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


class CreateUploadRequest(BaseModel):
    """Request schema for creating a presigned upload URL."""

    filename: str = Field(description="Original filename")
    content_type: str = Field(description="MIME type (e.g., image/png)")
    size_bytes: int | None = Field(default=None, description="File size in bytes (optional)")


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


class XToDemoArtifact(BaseModel):
    """Single phase artifact generated during an X-to-Demo run."""

    phase_key: str = Field(description="Stable phase identifier")
    title: str = Field(description="Human-readable phase title")
    markdown: str = Field(description="Phase markdown output")
    saved_path: str = Field(description="Relative path where phase output was saved")


class XToDemoRunResponse(BaseModel):
    """Response payload returned after completing the X-to-Demo pipeline."""

    run_id: str = Field(description="Unique pipeline run identifier")
    created_at: datetime = Field(description="UTC timestamp for run creation")
    model: str = Field(description="OpenAI model used for this run")
    reasoning_effort: str = Field(description="Reasoning effort used for this run")
    artifacts: list[XToDemoArtifact] = Field(description="Ordered list of phase outputs")
    final_code_spec: str = Field(description="Final generated code specification markdown")
    final_code_spec_path: str = Field(description="Relative path to saved code spec markdown")
