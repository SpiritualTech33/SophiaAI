"""
Endpoint tests for HTML page routes.

Strategy: verify each page route renders its Jinja2 template (200) and
contains a stable structural marker. Assertions target markup that is
unlikely to change with copy edits (wordmark, form data-mode, chat
composer), not volatile prose.

Run: pytest tests/test_app_pages.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_landing_page(client):
    """GET / renders the landing template with the SOPHIA wordmark and a register link."""
    response = client.get("/")
    assert response.status_code == 200
    assert "SOPHIA" in response.text
    assert "/register" in response.text


def test_chat_page(client):
    """GET /chat renders the chat portal with composer and orb avatar markers."""
    response = client.get("/chat")
    assert response.status_code == 200
    assert 'id="composer"' in response.text
    assert "orb" in response.text


def test_login_page(client):
    """GET /login renders the login form (data-mode="login")."""
    response = client.get("/login")
    assert response.status_code == 200
    assert 'data-mode="login"' in response.text


def test_register_page(client):
    """GET /register renders the register form (data-mode="register")."""
    response = client.get("/register")
    assert response.status_code == 200
    assert 'data-mode="register"' in response.text


def test_static_css_served(client):
    """The design-system stylesheet is served from /static."""
    response = client.get("/static/css/sophia.css")
    assert response.status_code == 200
