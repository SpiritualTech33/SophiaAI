"""
Unit tests for sophia.app.schemas.

Strategy: validate Pydantic models accept good input, reject bad input,
and produce correct defaults.

Run: pytest tests/test_app_schemas.py -v
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.app.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationSummary,
    LoginRequest,
    MessageOut,
    RegisterRequest,
    SourceOut,
    TokenResponse,
)


def test_register_request_valid():
    """RegisterRequest accepts a valid email and password."""
    req = RegisterRequest(email="test@example.com", password="secret123")
    assert req.email == "test@example.com"
    assert req.password == "secret123"


def test_register_request_rejects_bad_email():
    """RegisterRequest rejects a malformed email."""
    with pytest.raises(Exception):
        RegisterRequest(email="not-an-email", password="secret123")


def test_login_request_valid():
    """LoginRequest accepts a valid email and password."""
    req = LoginRequest(email="user@sophia.ai", password="pass")
    assert req.email == "user@sophia.ai"


def test_token_response_defaults():
    """TokenResponse sets token_type to 'bearer' by default."""
    resp = TokenResponse(access_token="abc.def.ghi")
    assert resp.token_type == "bearer"


def test_chat_request_defaults():
    """ChatRequest makes conversation_id optional (None by default)."""
    req = ChatRequest(message="What is wisdom?")
    assert req.message == "What is wisdom?"
    assert req.conversation_id is None


def test_chat_request_with_conversation_id():
    """ChatRequest accepts an explicit conversation_id."""
    req = ChatRequest(message="Tell me more", conversation_id=42)
    assert req.conversation_id == 42


def test_chat_response_structure():
    """ChatResponse holds answer, sources list, conversation_id, search_mode."""
    resp = ChatResponse(
        answer="Wisdom is...",
        sources=[SourceOut(text="passage", source_file="f.md", pillar="mind", score=0.8)],
        conversation_id=1,
        search_mode="corpus",
    )
    assert resp.answer == "Wisdom is..."
    assert len(resp.sources) == 1
    assert resp.sources[0].pillar == "mind"


def test_conversation_summary():
    """ConversationSummary holds id, title, timestamps."""
    now = datetime.now()
    summary = ConversationSummary(id=1, title="Test", created_at=now, updated_at=now)
    assert summary.id == 1
    assert summary.title == "Test"


def test_message_out():
    """MessageOut holds message fields including nullable sources_json."""
    now = datetime.now()
    msg = MessageOut(id=1, role="user", content="Hello", sources_json=None, created_at=now)
    assert msg.role == "user"
    assert msg.sources_json is None


def test_conversation_detail():
    """ConversationDetail nests a list of MessageOut."""
    now = datetime.now()
    detail = ConversationDetail(
        id=1,
        title="My chat",
        messages=[
            MessageOut(id=1, role="user", content="Hi", sources_json=None, created_at=now),
            MessageOut(id=2, role="sophia", content="Hello", sources_json='[]', created_at=now),
        ],
    )
    assert len(detail.messages) == 2
    assert detail.messages[1].role == "sophia"
