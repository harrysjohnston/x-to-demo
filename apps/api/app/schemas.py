"""Shared API schemas for consistent request/response formats."""

from typing import Any

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
