"""S3/MinIO storage provider implementation."""

import re
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.storage.base import UploadInstruction


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage (remove special chars, keep extension)."""
    # Extract extension
    parts = filename.rsplit(".", 1)
    if len(parts) == 2:
        name, ext = parts
        ext = f".{ext}"
    else:
        name = filename
        ext = ""

    # Remove/replace unsafe characters
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    # Remove multiple underscores
    name = re.sub(r"_+", "_", name)
    # Remove leading/trailing underscores
    name = name.strip("_")

    return f"{name}{ext}" if name else f"file{ext}"


class S3StorageProvider:
    """S3-compatible storage provider (works with AWS S3 and MinIO)."""

    def __init__(
        self,
        bucket: str,
        region: str = "us-east-1",
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        expires_seconds: int = 900,
    ):
        """Initialize S3 storage provider.

        Args:
            bucket: S3 bucket name
            region: AWS region (ignored for MinIO)
            endpoint_url: Custom endpoint URL (e.g., MinIO: http://localhost:9000)
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key
            expires_seconds: Presigned URL expiration time in seconds
        """
        self.bucket = bucket
        self.region = region
        self.expires_seconds = expires_seconds

        # Create S3 client
        client_kwargs: dict[str, str | Config] = {}
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url
        if access_key_id and secret_access_key:
            client_kwargs["aws_access_key_id"] = access_key_id
            client_kwargs["aws_secret_access_key"] = secret_access_key

        # Use path-style addressing for MinIO compatibility
        if endpoint_url:
            client_kwargs["config"] = Config(
                signature_version="s3v4", s3={"addressing_style": "path"}
            )

        self.s3_client = boto3.client("s3", region_name=region, **client_kwargs)

    def create_upload(
        self,
        filename: str,
        content_type: str,
        max_size_bytes: int,
        user_id: int | None = None,
    ) -> UploadInstruction:
        """Create a presigned POST upload instruction.

        Args:
            filename: Original filename
            content_type: MIME type (e.g., "image/png")
            max_size_bytes: Maximum file size in bytes
            user_id: Optional user ID for scoping uploads

        Returns:
            UploadInstruction with presigned POST URL and fields
        """
        # Generate unique object key
        sanitized = sanitize_filename(filename)
        if user_id:
            object_key = f"uploads/{user_id}/{uuid4().hex}/{sanitized}"
        else:
            object_key = f"uploads/{uuid4().hex}/{sanitized}"

        # Calculate expiration
        expires_at = datetime.now(UTC) + timedelta(seconds=self.expires_seconds)

        try:
            # Generate presigned POST
            # Conditions enforce content-type and max size
            post_data = self.s3_client.generate_presigned_post(
                Bucket=self.bucket,
                Key=object_key,
                Fields={"Content-Type": content_type},
                Conditions=[
                    {"Content-Type": content_type},
                    ["content-length-range", 1, max_size_bytes],
                ],
                ExpiresIn=self.expires_seconds,
            )

            url = post_data["url"]
            fields = post_data["fields"]

            # Generate public URL (if bucket is public) or presigned GET URL
            # For now, we'll leave public_url as None - can be enhanced later
            public_url = None

            return UploadInstruction(
                url=url,
                method="POST",
                fields=fields,
                object_key=object_key,
                expires_at=expires_at,
                public_url=public_url,
            )
        except ClientError as exc:
            raise RuntimeError(f"Failed to generate presigned URL: {exc}") from exc
