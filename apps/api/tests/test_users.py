"""Tests for user CRUD endpoints."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.auth import hash_password
from app.models import User


@pytest.fixture(name="sample_user")
def sample_user_fixture(session: Session):
    """Create a sample user for testing."""
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash=hash_password("password123"),
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


class TestCreateUser:
    """Tests for creating users."""

    def test_create_user_requires_auth(self, client: TestClient):
        response = client.post(
            "/api/v1/users/",
            json={"email": "newuser@example.com", "name": "New User", "password": "password123"},
        )
        assert response.status_code == 401

    def test_create_user_success(self, client: TestClient, auth_headers: dict[str, str]):
        """Test successful user creation."""
        response = client.post(
            "/api/v1/users/",
            headers=auth_headers,
            json={"email": "newuser@example.com", "name": "New User", "password": "password123"},
        )
        assert response.status_code == 201
        envelope = response.json()
        assert "data" in envelope
        data = envelope["data"]
        assert data["email"] == "newuser@example.com"
        assert data["name"] == "New User"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_user_duplicate_email(
        self, client: TestClient, sample_user: User, auth_headers: dict[str, str]
    ):
        """Test that creating a user with duplicate email fails."""
        response = client.post(
            "/api/v1/users/",
            headers=auth_headers,
            json={"email": sample_user.email, "name": "Another User", "password": "password123"},
        )
        assert response.status_code == 400
        error_response = response.json()
        assert "error" in error_response
        assert "already exists" in error_response["error"]["message"]

    def test_create_user_invalid_data(self, client: TestClient, auth_headers: dict[str, str]):
        """Test that creating a user with invalid data fails."""
        response = client.post(
            "/api/v1/users/",
            headers=auth_headers,
            json={"email": "invalid"},  # Missing required 'name' field
        )
        assert response.status_code == 422


class TestListUsers:
    """Tests for listing users."""

    def test_list_users_requires_auth(self, client: TestClient):
        """Test listing users requires authentication."""
        response = client.get("/api/v1/users/")
        assert response.status_code == 401

    def test_list_users_with_data(
        self, client: TestClient, sample_user: User, auth_headers: dict[str, str]
    ):
        """Test listing users with data."""
        response = client.get("/api/v1/users/", headers=auth_headers)
        assert response.status_code == 200
        envelope = response.json()
        assert "data" in envelope
        assert "meta" in envelope
        data = envelope["data"]
        assert len(data) >= 1
        assert any(u["email"] == sample_user.email for u in data)
        # Check pagination metadata
        assert envelope["meta"]["offset"] == 0
        assert envelope["meta"]["limit"] == 100

    def test_list_users_pagination(
        self, client: TestClient, session: Session, auth_headers: dict[str, str]
    ):
        """Test pagination of user list."""
        # Create multiple users
        for i in range(5):
            user = User(
                email=f"user{i}@example.com",
                name=f"User {i}",
                is_active=True,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            session.add(user)
        session.commit()

        # Test pagination (using offset instead of skip)
        response = client.get("/api/v1/users/?offset=2&limit=2", headers=auth_headers)
        assert response.status_code == 200
        envelope = response.json()
        assert "data" in envelope
        assert "meta" in envelope
        data = envelope["data"]
        assert len(data) == 2
        assert envelope["meta"]["offset"] == 2
        assert envelope["meta"]["limit"] == 2


class TestGetUser:
    """Tests for getting a single user."""

    def test_get_user_requires_auth(self, client: TestClient, sample_user: User):
        response = client.get(f"/api/v1/users/{sample_user.id}")
        assert response.status_code == 401

    def test_get_user_success(
        self, client: TestClient, sample_user: User, auth_headers: dict[str, str]
    ):
        """Test getting a user by ID."""
        response = client.get(f"/api/v1/users/{sample_user.id}", headers=auth_headers)
        assert response.status_code == 200
        envelope = response.json()
        assert "data" in envelope
        data = envelope["data"]
        assert data["id"] == sample_user.id
        assert data["email"] == sample_user.email
        assert data["name"] == sample_user.name

    def test_get_user_not_found(self, client: TestClient, auth_headers: dict[str, str]):
        """Test getting a non-existent user."""
        response = client.get("/api/v1/users/99999", headers=auth_headers)
        assert response.status_code == 404
        error_response = response.json()
        assert "error" in error_response
        assert "not found" in error_response["error"]["message"]


class TestUpdateUser:
    """Tests for updating users."""

    def test_update_user_success(
        self, client: TestClient, sample_user: User, auth_headers: dict[str, str]
    ):
        """Test updating a user."""
        response = client.patch(
            f"/api/v1/users/{sample_user.id}",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        envelope = response.json()
        assert "data" in envelope
        data = envelope["data"]
        assert data["name"] == "Updated Name"
        assert data["email"] == sample_user.email  # Unchanged

    def test_update_user_email(
        self, client: TestClient, sample_user: User, auth_headers: dict[str, str]
    ):
        """Test updating a user's email."""
        response = client.patch(
            f"/api/v1/users/{sample_user.id}",
            headers=auth_headers,
            json={"email": "newemail@example.com"},
        )
        assert response.status_code == 200
        envelope = response.json()
        assert "data" in envelope
        data = envelope["data"]
        assert data["email"] == "newemail@example.com"

    def test_update_user_is_active(
        self, client: TestClient, sample_user: User, auth_headers: dict[str, str]
    ):
        """Test toggling user's active status."""
        response = client.patch(
            f"/api/v1/users/{sample_user.id}",
            headers=auth_headers,
            json={"is_active": False},
        )
        assert response.status_code == 200
        envelope = response.json()
        assert "data" in envelope
        data = envelope["data"]
        assert data["is_active"] is False

    def test_update_user_not_found(self, client: TestClient, auth_headers: dict[str, str]):
        """Test updating a non-existent user."""
        response = client.patch(
            "/api/v1/users/99999",
            headers=auth_headers,
            json={"name": "New Name"},
        )
        assert response.status_code == 404


class TestDeleteUser:
    """Tests for deleting users."""

    def test_delete_user_success(
        self, client: TestClient, sample_user: User, session: Session, auth_headers: dict[str, str]
    ):
        """Test deleting a user."""
        user_id = sample_user.id
        response = client.delete(f"/api/v1/users/{user_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify user is deleted
        deleted_user = session.get(User, user_id)
        assert deleted_user is None

    def test_delete_user_not_found(self, client: TestClient, auth_headers: dict[str, str]):
        """Test deleting a non-existent user."""
        response = client.delete("/api/v1/users/99999", headers=auth_headers)
        assert response.status_code == 404


class TestDatabaseModels:
    """Tests for database models and session management."""

    def test_user_model_creation(self, session: Session):
        """Test creating a user directly with SQLModel."""
        user = User(
            email="direct@example.com",
            name="Direct User",
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.id is not None
        assert user.email == "direct@example.com"

    def test_user_query(self, session: Session, sample_user: User):
        """Test querying users from database."""
        users = session.exec(select(User).where(User.email == sample_user.email)).all()
        assert len(users) == 1
        assert users[0].email == sample_user.email

    def test_user_unique_email_constraint(self, session: Session, sample_user: User):
        """Test that email uniqueness is enforced."""
        duplicate_user = User(
            email=sample_user.email,  # Same email
            name="Duplicate",
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(duplicate_user)
        with pytest.raises(IntegrityError, match=r"UNIQUE constraint|unique constraint"):
            session.commit()
