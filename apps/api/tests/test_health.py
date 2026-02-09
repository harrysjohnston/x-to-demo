"""Smoke tests for the API application."""

import pytest

from app.main import app


def test_health_endpoint(client) -> None:
    """Test the health check endpoint returns correct response."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_endpoint_content_type(client) -> None:
    """Test the health endpoint returns correct content type."""
    response = client.get("/health")
    assert response.headers["content-type"] == "application/json"


def test_app_metadata() -> None:
    """Test that the FastAPI app has correct metadata."""
    assert app.title == "fullstack-template API"
    assert app.version == "0.0.0"
    assert app.description is not None


def test_openapi_docs_available(client) -> None:
    """Test that OpenAPI documentation is accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    openapi_schema = response.json()
    assert "openapi" in openapi_schema
    assert "info" in openapi_schema
    assert openapi_schema["info"]["title"] == "fullstack-template API"


def test_docs_ui_available(client) -> None:
    """Test that Swagger UI documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_redoc_available(client) -> None:
    """Test that ReDoc documentation is accessible."""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.unit
def test_nonexistent_endpoint_returns_404(client) -> None:
    """Test that nonexistent endpoints return 404."""
    response = client.get("/nonexistent")
    assert response.status_code == 404
