"""
Endpoint tests for chat and conversation APIs.

Strategy: mock the Sophia orchestrator so tests never touch FAISS,
embedding models, or the Groq API. Only the HTTP layer and DB
service are exercised.

Run: pytest tests/test_app_chat.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.core.orchestrator import SophiaResponse
from tests.conftest import register_and_get_token


class MockSophia:
    """Fake orchestrator that returns a fixed response without AI calls."""

    def ask(self, query, conversation_history=None):
        return SophiaResponse(
            answer=f"Mocked wisdom about: {query}",
            chunks=[],
            web_results=[],
            search_mode="corpus",
        )


@pytest.fixture()
def auth_client(test_app, client):
    """Client with a mock Sophia and a pre-registered user token."""
    test_app.state.sophia = MockSophia()
    token = register_and_get_token(client)
    return client, token


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_chat_new_conversation(auth_client):
    """POST /api/chat without conversation_id creates a new conversation."""
    client, token = auth_client
    response = client.post(
        "/api/chat",
        json={"message": "What is love?"},
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    data = response.json()
    assert "Mocked wisdom" in data["answer"]
    assert data["conversation_id"] >= 1
    assert data["search_mode"] == "corpus"


def test_chat_existing_conversation(auth_client):
    """POST /api/chat with a valid conversation_id appends to that conversation."""
    client, token = auth_client
    headers = _auth_header(token)

    first = client.post("/api/chat", json={"message": "First"}, headers=headers)
    conversation_id = first.json()["conversation_id"]

    second = client.post(
        "/api/chat",
        json={"message": "Second", "conversation_id": conversation_id},
        headers=headers,
    )
    assert second.status_code == 200
    assert second.json()["conversation_id"] == conversation_id


def test_chat_unauthorized(client):
    """POST /api/chat without a token returns 401."""
    response = client.post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 401


def test_list_conversations(auth_client):
    """GET /api/conversations returns the user's conversation list."""
    client, token = auth_client
    headers = _auth_header(token)

    client.post("/api/chat", json={"message": "First chat"}, headers=headers)
    client.post("/api/chat", json={"message": "Second chat"}, headers=headers)

    response = client.get("/api/conversations", headers=headers)
    assert response.status_code == 200
    conversations = response.json()
    assert len(conversations) == 2
    assert "id" in conversations[0]
    assert "title" in conversations[0]


def test_get_conversation_detail(auth_client):
    """GET /api/conversations/{id} returns messages for that conversation."""
    client, token = auth_client
    headers = _auth_header(token)

    chat_resp = client.post("/api/chat", json={"message": "Hello Sophia"}, headers=headers)
    conversation_id = chat_resp.json()["conversation_id"]

    response = client.get(f"/api/conversations/{conversation_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conversation_id
    assert len(data["messages"]) == 2
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][1]["role"] == "sophia"


def test_get_conversation_not_found(auth_client):
    """GET /api/conversations/999 returns 404 for a nonexistent conversation."""
    client, token = auth_client
    response = client.get("/api/conversations/999", headers=_auth_header(token))
    assert response.status_code == 404
