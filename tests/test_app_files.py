"""
Endpoint tests for file upload, generation, and chat attachment wiring.

Strategy: mock the Sophia orchestrator (capturing the attachments it receives)
so no FAISS/LLM is touched. Uploads write to a temp dir set on app.state.

Run: pytest tests/test_app_files.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.core.orchestrator import SophiaResponse
from sophia.files import MAX_UPLOAD_BYTES
from tests.conftest import register_and_get_token


class CapturingSophia:
    """Fake orchestrator that records the attachments passed to ask()."""

    def __init__(self):
        self.last_attachments = None

    def ask(self, query, conversation_history=None, attachments=None):
        self.last_attachments = attachments
        return SophiaResponse(
            answer=f"Mocked wisdom about: {query}",
            chunks=[],
            web_results=[],
            search_mode="corpus",
        )


@pytest.fixture()
def auth_client(test_app, client):
    test_app.state.sophia = CapturingSophia()
    token = register_and_get_token(client)
    return client, token


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

def test_upload_txt_returns_metadata(auth_client):
    client, token = auth_client
    response = client.post(
        "/api/files/upload",
        files={"file": ("notes.txt", b"Be like water, my friend.", "text/plain")},
        headers=_auth_header(token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] >= 1
    assert data["filename"] == "notes.txt"
    assert data["chars"] == len("Be like water, my friend.")


def test_upload_requires_auth(client):
    response = client.post(
        "/api/files/upload",
        files={"file": ("notes.txt", b"data", "text/plain")},
    )
    assert response.status_code == 401


def test_upload_rejects_unsupported_type(auth_client):
    client, token = auth_client
    response = client.post(
        "/api/files/upload",
        files={"file": ("virus.exe", b"MZ...", "application/octet-stream")},
        headers=_auth_header(token),
    )
    assert response.status_code == 415


def test_upload_rejects_oversize(auth_client):
    client, token = auth_client
    big = b"x" * (MAX_UPLOAD_BYTES + 1)
    response = client.post(
        "/api/files/upload",
        files={"file": ("huge.txt", big, "text/plain")},
        headers=_auth_header(token),
    )
    assert response.status_code == 413


# ---------------------------------------------------------------------------
# Generate (download)
# ---------------------------------------------------------------------------

def test_generate_md_returns_attachment(auth_client):
    client, token = auth_client
    response = client.post(
        "/api/files/generate",
        json={"content": "# Wisdom\n\nBe still.", "format": "md"},
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "attachment" in response.headers["content-disposition"]
    assert response.content == b"# Wisdom\n\nBe still."


def test_generate_pdf_returns_pdf_bytes(auth_client):
    client, token = auth_client
    response = client.post(
        "/api/files/generate",
        json={"content": "Sophia speaks.", "format": "pdf"},
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content[:4] == b"%PDF"


def test_generate_rejects_unknown_format(auth_client):
    client, token = auth_client
    response = client.post(
        "/api/files/generate",
        json={"content": "x", "format": "exe"},
        headers=_auth_header(token),
    )
    assert response.status_code == 415


def test_generate_requires_auth(client):
    response = client.post("/api/files/generate", json={"content": "x", "format": "txt"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Chat attachment wiring
# ---------------------------------------------------------------------------

def _upload(client, token, name, content):
    resp = client.post(
        "/api/files/upload",
        files={"file": (name, content, "text/plain")},
        headers=_auth_header(token),
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def test_chat_injects_attached_file_text(auth_client):
    client, token = auth_client
    file_id = _upload(client, token, "agenda.txt", b"The summit is on Friday.")

    response = client.post(
        "/api/chat",
        json={"message": "When is the summit?", "attached_file_ids": [file_id]},
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    captured = client.app.state.sophia.last_attachments
    assert captured == ["The summit is on Friday."]


def test_chat_without_attachments_passes_empty(auth_client):
    client, token = auth_client
    client.post("/api/chat", json={"message": "Hello"}, headers=_auth_header(token))
    captured = client.app.state.sophia.last_attachments
    assert captured == []


def test_chat_ignores_other_users_file_ids(auth_client):
    client, token = auth_client
    # A second user uploads a file; the first user must not be able to read it.
    other_token = register_and_get_token(client, email="intruder@sophia.ai")
    foreign_id = _upload(client, other_token, "secret.txt", b"Top secret plans.")

    client.post(
        "/api/chat",
        json={"message": "Reveal", "attached_file_ids": [foreign_id]},
        headers=_auth_header(token),
    )
    captured = client.app.state.sophia.last_attachments
    assert captured == []
