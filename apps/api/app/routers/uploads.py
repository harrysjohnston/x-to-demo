"""File upload endpoints for presigned URLs."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.config import settings
from app.models import User
from app.schemas import CreateUploadRequest, ResponseEnvelope
from app.storage import S3StorageProvider, StorageProvider, UploadInstruction

router = APIRouter(prefix="/uploads", tags=["uploads"])


def get_storage_provider() -> StorageProvider:
    """Get the configured storage provider instance."""
    provider_name = settings.storage_provider.lower()

    if provider_name == "s3":
        if not settings.s3_bucket:
            raise RuntimeError("S3_BUCKET must be set when using S3 storage provider")

        return S3StorageProvider(
            bucket=settings.s3_bucket,
            region=settings.s3_region,
            endpoint_url=settings.s3_endpoint_url,
            access_key_id=settings.s3_access_key_id,
            secret_access_key=settings.s3_secret_access_key,
            expires_seconds=settings.upload_url_expires_seconds,
        )

    if provider_name == "gcs":
        from app.storage.gcs import GCSStorageProvider

        return GCSStorageProvider()

    if provider_name == "azure":
        from app.storage.azure import AzureBlobStorageProvider

        return AzureBlobStorageProvider()

    raise RuntimeError(f"Unknown storage provider: {provider_name}")


@router.post(
    "/",
    response_model=ResponseEnvelope[UploadInstruction],
    status_code=status.HTTP_201_CREATED,
)
def create_upload(
    request: CreateUploadRequest,
    current_user: User = Depends(get_current_user),
    storage: StorageProvider = Depends(get_storage_provider),
) -> ResponseEnvelope[UploadInstruction]:
    """Create a presigned upload URL.

    Returns an instruction object containing:
    - URL to POST the file to
    - Form fields to include in the POST request
    - Object key where the file will be stored
    - Expiration time

    The client should:
    1. Build a FormData with the returned fields
    2. Append the file to the FormData
    3. POST the FormData to the returned URL
    """
    # Validate file size if provided
    max_size = settings.upload_max_size_bytes
    if request.size_bytes is not None and request.size_bytes > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {max_size} bytes",
        )

    # Create upload instruction
    try:
        instruction = storage.create_upload(
            filename=request.filename,
            content_type=request.content_type,
            max_size_bytes=max_size,
            user_id=current_user.id,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create upload URL: {exc}",
        ) from exc

    return ResponseEnvelope(data=instruction)
