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


def test_user_has_conversations_relationship(db_session):
    """user.conversations returns all conversations owned by that user."""
    user = User(email="rel@test.com", hashed_password="hash")
    db_session.add(user)
    db_session.commit()

    db_session.add(Conversation(user_id=user.id, title="Talk 1"))
    db_session.add(Conversation(user_id=user.id, title="Talk 2"))
    db_session.commit()

    db_session.refresh(user)
    assert len(user.conversations) == 2
    titles = {c.title for c in user.conversations}
    assert titles == {"Talk 1", "Talk 2"}


def test_conversation_has_messages_relationship(db_session):
    """conversation.messages returns all messages in order."""
    user = User(email="msgs@test.com", hashed_password="hash")
    db_session.add(user)
    db_session.commit()

    conversation = Conversation(user_id=user.id, title="Deep Talk")
    db_session.add(conversation)
    db_session.commit()

    db_session.add(Message(conversation_id=conversation.id, role="user", content="Hello"))
    db_session.add(Message(conversation_id=conversation.id, role="sophia", content="Welcome"))
    db_session.commit()

    db_session.refresh(conversation)
    assert len(conversation.messages) == 2
    assert conversation.messages[0].role == "user"
    assert conversation.messages[1].role == "sophia"


def test_delete_user_cascades_to_conversations_and_messages(db_session):
    """Deleting a User deletes their Conversations and Messages."""
    user = User(email="cascade@test.com", hashed_password="hash")
    db_session.add(user)
    db_session.commit()

    conversation = Conversation(user_id=user.id, title="Doomed Talk")
    db_session.add(conversation)
    db_session.commit()

    db_session.add(Message(conversation_id=conversation.id, role="user", content="Goodbye"))
    db_session.commit()

    db_session.delete(user)
    db_session.commit()

    assert db_session.query(User).count() == 0
    assert db_session.query(Conversation).count() == 0
    assert db_session.query(Message).count() == 0


def test_delete_conversation_cascades_to_messages(db_session):
    """Deleting a Conversation deletes its Messages but not the User."""
    user = User(email="partcasc@test.com", hashed_password="hash")
    db_session.add(user)
    db_session.commit()

    conversation = Conversation(user_id=user.id, title="Temporary")
    db_session.add(conversation)
    db_session.commit()

    db_session.add(Message(conversation_id=conversation.id, role="user", content="Test"))
    db_session.commit()

    db_session.delete(conversation)
    db_session.commit()

    assert db_session.query(User).count() == 1
    assert db_session.query(Conversation).count() == 0
    assert db_session.query(Message).count() == 0


def test_conversation_repr():
    """Conversation.__repr__ returns a readable string."""
    conversation = Conversation(id=7, title="On Love")
    assert "On Love" in repr(conversation)


def test_message_repr():
    """Message.__repr__ returns a readable string."""
    message = Message(id=3, role="sophia")
    assert "sophia" in repr(message)


from sophia.db.service import (
    create_user,
    get_user_by_email,
    create_conversation,
    get_conversations_for_user,
    add_message,
    get_conversation_with_messages,
    delete_conversation,
)


def test_create_user_service(db_session):
    """create_user inserts a User and returns it with an id."""
    user = create_user(db_session, email="svc@test.com", hashed_password="hash123")
    assert user.id is not None
    assert user.email == "svc@test.com"


def test_get_user_by_email_found(db_session):
    """get_user_by_email returns the user when email exists."""
    create_user(db_session, email="find@test.com", hashed_password="hash")
    found = get_user_by_email(db_session, "find@test.com")
    assert found is not None
    assert found.email == "find@test.com"


def test_get_user_by_email_not_found(db_session):
    """get_user_by_email returns None when email does not exist."""
    result = get_user_by_email(db_session, "ghost@test.com")
    assert result is None


def test_create_conversation_service(db_session):
    """create_conversation creates a Conversation tied to a user."""
    user = create_user(db_session, email="conv_svc@test.com", hashed_password="hash")
    conversation = create_conversation(db_session, user_id=user.id, title="Service Talk")
    assert conversation.id is not None
    assert conversation.user_id == user.id
    assert conversation.title == "Service Talk"


def test_get_conversations_for_user_service(db_session):
    """get_conversations_for_user returns all conversations for a user."""
    user = create_user(db_session, email="list@test.com", hashed_password="hash")
    create_conversation(db_session, user_id=user.id, title="Alpha")
    create_conversation(db_session, user_id=user.id, title="Beta")
    conversations = get_conversations_for_user(db_session, user_id=user.id)
    assert len(conversations) == 2


def test_add_message_service(db_session):
    """add_message appends a message to a conversation."""
    user = create_user(db_session, email="addmsg@test.com", hashed_password="hash")
    conversation = create_conversation(db_session, user_id=user.id)
    message = add_message(
        db_session,
        conversation_id=conversation.id,
        role="user",
        content="What is the meaning of life?",
    )
    assert message.id is not None
    assert message.conversation_id == conversation.id
    assert message.role == "user"


def test_add_message_with_sources(db_session):
    """add_message stores sources_json when provided."""
    import json

    user = create_user(db_session, email="srcsvc@test.com", hashed_password="hash")
    conversation = create_conversation(db_session, user_id=user.id)
    sources = json.dumps([{"file": "plato.md", "score": 0.92}])
    message = add_message(
        db_session,
        conversation_id=conversation.id,
        role="sophia",
        content="To live well is to live wisely.",
        sources_json=sources,
    )
    assert message.sources_json is not None
    parsed = json.loads(message.sources_json)
    assert parsed[0]["file"] == "plato.md"


def test_get_conversation_with_messages_service(db_session):
    """get_conversation_with_messages returns conversation and its messages."""
    user = create_user(db_session, email="full@test.com", hashed_password="hash")
    conversation = create_conversation(db_session, user_id=user.id, title="Full Flow")
    add_message(db_session, conversation_id=conversation.id, role="user", content="Q1")
    add_message(db_session, conversation_id=conversation.id, role="sophia", content="A1")
    add_message(db_session, conversation_id=conversation.id, role="user", content="Q2")

    result = get_conversation_with_messages(db_session, conversation_id=conversation.id)
    assert result is not None
    assert result.title == "Full Flow"
    assert len(result.messages) == 3
    assert result.messages[0].content == "Q1"
    assert result.messages[2].content == "Q2"


def test_get_conversation_with_messages_not_found(db_session):
    """get_conversation_with_messages returns None for nonexistent id."""
    result = get_conversation_with_messages(db_session, conversation_id=9999)
    assert result is None


def test_delete_conversation_service(db_session):
    """delete_conversation removes the conversation and returns True."""
    user = create_user(db_session, email="del@test.com", hashed_password="hash")
    conversation = create_conversation(db_session, user_id=user.id, title="Doomed")
    conversation_id = conversation.id

    deleted = delete_conversation(db_session, conversation_id=conversation_id)
    assert deleted is True
    assert get_conversation_with_messages(db_session, conversation_id) is None


def test_delete_conversation_cascades_to_its_messages(db_session):
    """delete_conversation also removes the conversation's messages."""
    user = create_user(db_session, email="delcascade@test.com", hashed_password="hash")
    conversation = create_conversation(db_session, user_id=user.id)
    add_message(db_session, conversation_id=conversation.id, role="user", content="Q1")
    add_message(db_session, conversation_id=conversation.id, role="sophia", content="A1")

    delete_conversation(db_session, conversation_id=conversation.id)
    remaining = db_session.query(Message).filter_by(conversation_id=conversation.id).all()
    assert remaining == []


def test_delete_conversation_not_found_returns_false(db_session):
    """delete_conversation returns False when no conversation has that id."""
    assert delete_conversation(db_session, conversation_id=9999) is False
