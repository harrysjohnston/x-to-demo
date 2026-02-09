"""Tests for authentication endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


class TestAuthRegisterLogin:
    def test_register_success(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "a@example.com", "name": "A", "password": "password123"},
        )
        assert resp.status_code == 201
        envelope = resp.json()
        assert "data" in envelope
        data = envelope["data"]
        assert data["email"] == "a@example.com"
        assert "id" in data

    def test_register_duplicate_email(self, client: TestClient):
        client.post(
            "/api/v1/auth/register",
            json={"email": "dup@example.com", "name": "A", "password": "password123"},
        )
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "dup@example.com", "name": "B", "password": "password123"},
        )
        assert resp.status_code == 400
        error_response = resp.json()
        assert "error" in error_response

    def test_login_success(self, client: TestClient):
        client.post(
            "/api/v1/auth/register",
            json={"email": "login@example.com", "name": "A", "password": "password123"},
        )
        resp = client.post(
            "/api/v1/auth/login", json={"email": "login@example.com", "password": "password123"}
        )
        assert resp.status_code == 200
        envelope = resp.json()
        assert "data" in envelope
        data = envelope["data"]
        assert data["token_type"] == "bearer"
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_wrong_password(self, client: TestClient):
        client.post(
            "/api/v1/auth/register",
            json={"email": "badpw@example.com", "name": "A", "password": "password123"},
        )
        resp = client.post(
            "/api/v1/auth/login", json={"email": "badpw@example.com", "password": "wrongpass"}
        )
        assert resp.status_code == 401
        error_response = resp.json()
        assert "error" in error_response


class TestAuthRefreshLogout:
    def test_refresh_rotates_and_revokes_old_token(self, client: TestClient):
        client.post(
            "/api/v1/auth/register",
            json={"email": "r@example.com", "name": "A", "password": "password123"},
        )
        login = client.post(
            "/api/v1/auth/login", json={"email": "r@example.com", "password": "password123"}
        )
        login_envelope = login.json()
        refresh_token = login_envelope["data"]["refresh_token"]

        refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert refreshed.status_code == 200
        refreshed_envelope = refreshed.json()
        new_refresh_token = refreshed_envelope["data"]["refresh_token"]
        assert new_refresh_token != refresh_token

        # Old refresh token should be revoked (rotation).
        old_again = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert old_again.status_code == 401

    def test_refresh_rejects_access_token(self, client: TestClient):
        client.post(
            "/api/v1/auth/register",
            json={"email": "t@example.com", "name": "A", "password": "password123"},
        )
        login = client.post(
            "/api/v1/auth/login", json={"email": "t@example.com", "password": "password123"}
        )
        login_envelope = login.json()
        access_token = login_envelope["data"]["access_token"]

        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
        assert resp.status_code == 401

    def test_logout_revokes_refresh_token(self, client: TestClient):
        client.post(
            "/api/v1/auth/register",
            json={"email": "l@example.com", "name": "A", "password": "password123"},
        )
        login = client.post(
            "/api/v1/auth/login", json={"email": "l@example.com", "password": "password123"}
        )
        login_envelope = login.json()
        refresh_token = login_envelope["data"]["refresh_token"]

        out = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
        assert out.status_code == 204

        after = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert after.status_code == 401
