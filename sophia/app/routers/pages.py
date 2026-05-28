"""
HTML page routes for SophiaAI.

Executive Brief:
    Server-rendered Jinja2 pages. Each route returns a TemplateResponse
    built from app.state.templates. These pages are public HTML shells;
    authentication is enforced client-side (the JS redirects to /login
    when no token is present) and server-side by the /api/* endpoints.

Mental Model:
    The page routes serve structure. The behavior lives in the static JS
    modules (cosmos.js, auth.js, chat.js), which talk to the JSON API
    using the JWT stored in localStorage.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["pages"])


def _render(request: Request, template_name: str) -> HTMLResponse:
    """
    Executive Brief:
        Render a template from the app-level Jinja2Templates instance.
        Centralized so every page route stays a single expressive line.
    """
    templates = request.app.state.templates
    return templates.TemplateResponse(request, template_name)


@router.get("/", response_class=HTMLResponse)
def landing_page(request: Request) -> HTMLResponse:
    """Serve the landing page."""
    return _render(request, "index.html")


@router.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request) -> HTMLResponse:
    """Serve the chat page."""
    return _render(request, "chat.html")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    """Serve the login page."""
    return _render(request, "login.html")


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request) -> HTMLResponse:
    """Serve the register page."""
    return _render(request, "register.html")
