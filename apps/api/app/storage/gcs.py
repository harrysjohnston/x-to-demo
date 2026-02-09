"""Google Cloud Storage provider (stub for learning)."""

from app.storage.base import StorageProvider, UploadInstruction


class GCSStorageProvider:
    """Google Cloud Storage provider (stub implementation).

    This is a placeholder for future GCS implementation.
    """

    def create_upload(
        self,
        filename: str,
        content_type: str,
        max_size_bytes: int,
        user_id: int | None = None,
    ) -> UploadInstruction:
        """Create a presigned upload instruction (stub).

        Args:
            filename: Original filename
            content_type: MIME type
            max_size_bytes: Maximum file size in bytes
            user_id: Optional user ID

        Returns:
            UploadInstruction

        Raises:
            NotImplementedError: Always, as this is a stub
        """
        raise NotImplementedError("GCS provider not yet implemented")


# Type check: ensure it implements the protocol
_ = StorageProvider  # Suppress unused import warning
