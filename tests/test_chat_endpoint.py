"""
End-to-end flow test for a logged-in user's full chat journey.

Strategy: mock the Sophia orchestrator so the test exercises the entire
HTTP + DB stack (register -> login -> chat -> persistence) without touching
FAISS, embedding models, or the Groq API.

Run: pytest tests/test_chat_endpoint.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.core.orchestrator import SophiaResponse


class MockSophia:
    """Fake orchestrator that returns a fixed response without AI calls."""

    def ask(self, query, conversation_history=None, attachments=None, image_attachments=None):
        return SophiaResponse(
            answer=f"Mocked wisdom about: {query}",
            chunks=[],
            web_results=[],
            search_mode="corpus",
        )


@pytest.fixture()
def flow_client(test_app, client):
    """Client whose app has a mocked Sophia wired in."""
    test_app.state.sophia = MockSophia()
    return client


def test_full_chat_flow_register_login_chat_persist(flow_client):
    """Register, log in, chat, then read the conversation back from the DB."""
    email, password = "journey@sophia.ai", "cosmic-wisdom-42"

    # 1. Register.
    register = flow_client.post(
        "/auth/register", json={"email": email, "password": password}
    )
    assert register.status_code == 201

    # 2. Log in with the same credentials and use THAT token going forward.
    login = flow_client.post(
        "/auth/login", json={"email": email, "password": password}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Send a chat message as the logged-in user.
    chat = flow_client.post(
        "/api/chat",
        json={"message": "What is the nature of wisdom?"},
        headers=headers,
    )
    assert chat.status_code == 200
    body = chat.json()
    assert "Mocked wisdom" in body["answer"]
    assert body["search_mode"] == "corpus"
    conversation_id = body["conversation_id"]
    assert conversation_id >= 1

    # 4. The conversation appears in the user's list.
    conversations = flow_client.get("/api/conversations", headers=headers)
    assert conversations.status_code == 200
    assert any(c["id"] == conversation_id for c in conversations.json())

    # 5. Both turns persisted with the correct roles.
    detail = flow_client.get(
        f"/api/conversations/{conversation_id}", headers=headers
    )
    assert detail.status_code == 200
    messages = detail.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "What is the nature of wisdom?"
    assert messages[1]["role"] == "sophia"
    assert "Mocked wisdom" in messages[1]["content"]
