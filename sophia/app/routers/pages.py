"""
HTML page routes for SophiaAI.

Executive Brief:
    Placeholder pages that return minimal HTML. Phase 12 replaces
    these with proper Jinja2 templates, static assets, and a real
    chat UI. These stubs exist so the route structure is wired and
    testable now.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
def landing_page() -> HTMLResponse:
    """Serve the landing page."""
    return HTMLResponse(
        "<html><body>"
        "<h1>SophiaAI</h1>"
        "<p>A bridge between the Divine and Technology.</p>"
        "<p><a href='/login'>Login</a> | <a href='/register'>Register</a></p>"
        "</body></html>"
    )


@router.get("/chat", response_class=HTMLResponse)
def chat_page() -> HTMLResponse:
    """Serve the chat page."""
    return HTMLResponse(
        "<html><body>"
        "<h1>Chat with Sophia</h1>"
        "<p>The conversation UI will arrive in Phase 12.</p>"
        "</body></html>"
    )


@router.get("/login", response_class=HTMLResponse)
def login_page() -> HTMLResponse:
    """Serve the login page."""
    return HTMLResponse(
        "<html><body>"
        "<h1>Login</h1>"
        "<p>The login form will arrive in Phase 12.</p>"
        "</body></html>"
    )


@router.get("/register", response_class=HTMLResponse)
def register_page() -> HTMLResponse:
    """Serve the register page."""
    return HTMLResponse(
        "<html><body>"
        "<h1>Register</h1>"
        "<p>The registration form will arrive in Phase 12.</p>"
        "</body></html>"
    )
