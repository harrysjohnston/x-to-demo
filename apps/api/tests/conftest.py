"""Pytest configuration and shared fixtures."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.main import app


@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI application with test database session."""

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(client: TestClient) -> dict[str, str]:
    """Register+login a user and return Authorization header."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "auth@example.com", "name": "Auth User", "password": "password123"},
    )
    resp = client.post(
        "/api/v1/auth/login", json={"email": "auth@example.com", "password": "password123"}
    )
    assert resp.status_code == 200
    login_data = resp.json()["data"]
    access = login_data["access_token"]
    return {"Authorization": f"Bearer {access}"}
