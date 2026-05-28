"""
Endpoint tests for HTML page routes.

Strategy: verify each page route returns 200 with HTML content.
Pages are placeholder stubs — Phase 12 replaces them with Jinja2 templates.

Run: pytest tests/test_app_pages.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_landing_page(client):
    """GET / returns 200 with HTML containing 'SophiaAI'."""
    response = client.get("/")
    assert response.status_code == 200
    assert "SophiaAI" in response.text


def test_chat_page(client):
    """GET /chat returns 200 with HTML."""
    response = client.get("/chat")
    assert response.status_code == 200
    assert "Chat" in response.text


def test_login_page(client):
    """GET /login returns 200 with HTML."""
    response = client.get("/login")
    assert response.status_code == 200
    assert "Login" in response.text


def test_register_page(client):
    """GET /register returns 200 with HTML."""
    response = client.get("/register")
    assert response.status_code == 200
    assert "Register" in response.text
