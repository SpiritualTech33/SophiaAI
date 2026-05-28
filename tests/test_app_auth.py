"""
Endpoint tests for POST /auth/register and POST /auth/login.

Strategy: use TestClient + in-memory SQLite. No mocks needed —
auth endpoints only touch the database and crypto modules.

Run: pytest tests/test_app_auth.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.conftest import register_and_get_token


def test_register_new_user(client):
    """POST /auth/register creates a user and returns a JWT."""
    response = client.post(
        "/auth/register",
        json={"email": "new@sophia.ai", "password": "cosmos123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client):
    """POST /auth/register with an existing email returns 409."""
    client.post("/auth/register", json={"email": "dup@sophia.ai", "password": "pass1"})
    response = client.post(
        "/auth/register",
        json={"email": "dup@sophia.ai", "password": "pass2"},
    )
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"].lower()


def test_register_invalid_email(client):
    """POST /auth/register with a bad email returns 422."""
    response = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "pass"},
    )
    assert response.status_code == 422


def test_login_valid_credentials(client):
    """POST /auth/login with correct credentials returns a JWT."""
    register_and_get_token(client, "login@sophia.ai", "mypassword")
    response = client.post(
        "/auth/login",
        json={"email": "login@sophia.ai", "password": "mypassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    """POST /auth/login with wrong password returns 401."""
    register_and_get_token(client, "wrong@sophia.ai", "rightpass")
    response = client.post(
        "/auth/login",
        json={"email": "wrong@sophia.ai", "password": "wrongpass"},
    )
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


def test_login_nonexistent_user(client):
    """POST /auth/login with unknown email returns 401."""
    response = client.post(
        "/auth/login",
        json={"email": "ghost@sophia.ai", "password": "pass"},
    )
    assert response.status_code == 401
