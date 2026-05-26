"""
Unit tests for sophia.db.

Strategy: every test uses an in-memory SQLite database via a fresh engine.
No disk I/O, no leftover files. Each test is fully isolated.

Run: pytest tests/test_database.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import inspect, text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.db.database import Base, build_engine, build_session_factory


def test_build_engine_creates_working_engine():
    """build_engine returns an engine that can connect to in-memory SQLite."""
    engine = build_engine("sqlite:///:memory:")
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar() == 1
    engine.dispose()


def test_build_session_factory_returns_callable():
    """build_session_factory returns a sessionmaker bound to the engine."""
    engine = build_engine("sqlite:///:memory:")
    session_factory = build_session_factory(engine)
    session = session_factory()
    assert session.bind is engine
    session.close()
    engine.dispose()


def test_base_has_metadata():
    """Base class exposes metadata for create_all."""
    assert Base.metadata is not None


from sophia.db.models import User, Conversation, Message


@pytest.fixture
def db_session():
    """Yield a fresh in-memory database session, then tear down."""
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)
    session = session_factory()
    yield session
    session.close()
    engine.dispose()


def test_user_table_exists_after_create_all():
    """create_all produces a 'users' table."""
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
    assert "users" in inspector.get_table_names()
    engine.dispose()


def test_create_and_read_user(db_session):
    """Insert a User row and read it back."""
    user = User(
        email="sophia@spiritual.tech",
        hashed_password="fakehash_abc123",
    )
    db_session.add(user)
    db_session.commit()

    fetched = db_session.query(User).filter_by(email="sophia@spiritual.tech").first()
    assert fetched is not None
    assert fetched.email == "sophia@spiritual.tech"
    assert fetched.hashed_password == "fakehash_abc123"
    assert fetched.id is not None
    assert fetched.created_at is not None


def test_user_email_is_unique(db_session):
    """Duplicate emails raise IntegrityError."""
    from sqlalchemy.exc import IntegrityError

    user_one = User(email="dup@test.com", hashed_password="hash1")
    user_two = User(email="dup@test.com", hashed_password="hash2")
    db_session.add(user_one)
    db_session.commit()
    db_session.add(user_two)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_user_repr():
    """User.__repr__ returns a readable string."""
    user = User(id=1, email="test@example.com", hashed_password="x")
    assert "test@example.com" in repr(user)


def test_conversations_table_exists_after_create_all():
    """create_all produces a 'conversations' table."""
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
    assert "conversations" in inspector.get_table_names()
    engine.dispose()


def test_messages_table_exists_after_create_all():
    """create_all produces a 'messages' table."""
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
    assert "messages" in inspector.get_table_names()
    engine.dispose()


def test_create_conversation_linked_to_user(db_session):
    """A Conversation belongs to a User via user_id."""
    user = User(email="conv@test.com", hashed_password="hash")
    db_session.add(user)
    db_session.commit()

    conversation = Conversation(user_id=user.id, title="On the Nature of Being")
    db_session.add(conversation)
    db_session.commit()

    fetched = db_session.query(Conversation).first()
    assert fetched is not None
    assert fetched.user_id == user.id
    assert fetched.title == "On the Nature of Being"
    assert fetched.created_at is not None
    assert fetched.updated_at is not None


def test_create_message_linked_to_conversation(db_session):
    """A Message belongs to a Conversation via conversation_id."""
    user = User(email="msg@test.com", hashed_password="hash")
    db_session.add(user)
    db_session.commit()

    conversation = Conversation(user_id=user.id, title="First Talk")
    db_session.add(conversation)
    db_session.commit()

    message = Message(
        conversation_id=conversation.id,
        role="user",
        content="What is wisdom?",
    )
    db_session.add(message)
    db_session.commit()

    fetched = db_session.query(Message).first()
    assert fetched is not None
    assert fetched.role == "user"
    assert fetched.content == "What is wisdom?"
    assert fetched.sources_json is None
    assert fetched.created_at is not None


def test_message_stores_sources_json(db_session):
    """sources_json stores a JSON string of citation data."""
    import json

    user = User(email="src@test.com", hashed_password="hash")
    db_session.add(user)
    db_session.commit()

    conversation = Conversation(user_id=user.id)
    db_session.add(conversation)
    db_session.commit()

    sources = json.dumps([{"file": "lao_tzu.md", "score": 0.87}])
    message = Message(
        conversation_id=conversation.id,
        role="sophia",
        content="The Tao that can be told is not the eternal Tao.",
        sources_json=sources,
    )
    db_session.add(message)
    db_session.commit()

    fetched = db_session.query(Message).first()
    parsed = json.loads(fetched.sources_json)
    assert parsed[0]["file"] == "lao_tzu.md"
    assert parsed[0]["score"] == 0.87
