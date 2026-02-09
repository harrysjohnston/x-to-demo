"""Tests for file upload endpoints."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage import UploadInstruction


@pytest.fixture(name="mock_storage_provider")
def mock_storage_provider_fixture():
    """Create a mock storage provider."""
    provider = MagicMock()
    provider.create_upload.return_value = UploadInstruction(
        url="https://s3.example.com/bucket/upload",
        method="POST",
        fields={
            "key": "uploads/1/test-file.txt",
            "policy": "test-policy",
            "x-amz-signature": "test-signature",
            "Content-Type": "text/plain",
        },
        object_key="uploads/1/test-file.txt",
        expires_at=datetime.now(UTC),
        public_url=None,
    )
    return provider


@pytest.fixture(name="client_with_mock_storage")
def client_with_mock_storage_fixture(client: TestClient, mock_storage_provider):
    """Create a test client with mocked storage provider."""
    from app.routers import uploads

    app.dependency_overrides[uploads.get_storage_provider] = lambda: mock_storage_provider
    yield client
    app.dependency_overrides.clear()


class TestCreateUpload:
    """Tests for creating presigned upload URLs."""

    def test_create_upload_requires_auth(self, client: TestClient):
        """Test that creating upload URL requires authentication."""
        response = client.post(
            "/api/v1/uploads/",
            json={"filename": "test.txt", "content_type": "text/plain"},
        )
        assert response.status_code == 401

    def test_create_upload_success(
        self,
        client_with_mock_storage: TestClient,
        auth_headers: dict[str, str],
        mock_storage_provider,
    ):
        """Test successful creation of presigned upload URL."""
        response = client_with_mock_storage.post(
            "/api/v1/uploads/",
            headers=auth_headers,
            json={"filename": "test.txt", "content_type": "text/plain", "size_bytes": 1024},
        )
        assert response.status_code == 201
        envelope = response.json()
        assert "data" in envelope
        data = envelope["data"]
        assert data["url"] == "https://s3.example.com/bucket/upload"
        assert data["method"] == "POST"
        assert "fields" in data
        assert data["object_key"] == "uploads/1/test-file.txt"
        assert "expires_at" in data

        # Verify storage provider was called correctly
        mock_storage_provider.create_upload.assert_called_once()
        call_kwargs = mock_storage_provider.create_upload.call_args[1]
        assert call_kwargs["filename"] == "test.txt"
        assert call_kwargs["content_type"] == "text/plain"
        assert call_kwargs["max_size_bytes"] > 0
        assert call_kwargs["user_id"] is not None

    def test_create_upload_without_size(
        self, client_with_mock_storage: TestClient, auth_headers: dict[str, str]
    ):
        """Test creating upload URL without size_bytes."""
        response = client_with_mock_storage.post(
            "/api/v1/uploads/",
            headers=auth_headers,
            json={"filename": "test.txt", "content_type": "text/plain"},
        )
        assert response.status_code == 201
        envelope = response.json()
        assert "data" in envelope

    def test_create_upload_file_too_large(
        self, client_with_mock_storage: TestClient, auth_headers: dict[str, str]
    ):
        """Test that files exceeding max size are rejected."""
        # Set max size to 1MB
        with patch("app.config.settings.upload_max_size_bytes", 1024 * 1024):
            response = client_with_mock_storage.post(
                "/api/v1/uploads/",
                headers=auth_headers,
                json={
                    "filename": "large.txt",
                    "content_type": "text/plain",
                    "size_bytes": 2 * 1024 * 1024,  # 2MB
                },
            )
            assert response.status_code == 400
            error_response = response.json()
            assert "error" in error_response
            assert "exceeds maximum" in error_response["error"]["message"].lower()

    def test_create_upload_invalid_data(
        self, client_with_mock_storage: TestClient, auth_headers: dict[str, str]
    ):
        """Test that invalid request data is rejected."""
        # Missing required fields
        response = client_with_mock_storage.post(
            "/api/v1/uploads/",
            headers=auth_headers,
            json={"filename": "test.txt"},  # Missing content_type
        )
        assert response.status_code == 422

    def test_create_upload_storage_error(
        self,
        client_with_mock_storage: TestClient,
        auth_headers: dict[str, str],
        mock_storage_provider,
    ):
        """Test handling of storage provider errors."""
        mock_storage_provider.create_upload.side_effect = RuntimeError("Storage unavailable")
        response = client_with_mock_storage.post(
            "/api/v1/uploads/",
            headers=auth_headers,
            json={"filename": "test.txt", "content_type": "text/plain"},
        )
        assert response.status_code == 500
        error_response = response.json()
        assert "error" in error_response
        assert "Failed to create upload URL" in error_response["error"]["message"]
