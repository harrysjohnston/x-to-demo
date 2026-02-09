"""Base storage provider interface."""

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, Field


class UploadInstruction(BaseModel):
    """Presigned upload instruction returned to the client."""

    url: str = Field(description="URL where browser POSTs the form")
    method: str = Field(description="HTTP method (always POST)")
    fields: dict[str, str] = Field(description="Form fields to include in POST")
    object_key: str = Field(description="Final storage path/key")
    expires_at: datetime = Field(description="When the presigned URL expires")
    public_url: str | None = Field(default=None, description="Optional public download URL")


class StorageProvider(Protocol):
    """Protocol for storage providers that generate presigned upload URLs."""

    def create_upload(
        self,
        filename: str,
        content_type: str,
        max_size_bytes: int,
        user_id: int | None = None,
    ) -> UploadInstruction:
        """Create a presigned upload instruction.

        Args:
            filename: Original filename
            content_type: MIME type (e.g., "image/png")
            max_size_bytes: Maximum file size in bytes
            user_id: Optional user ID for scoping uploads

        Returns:
            UploadInstruction with URL, fields, and metadata
        """
        ...
