# Phase 9 — Database Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `sophia/db/` package — SQLAlchemy ORM models and session machinery that give Sophia persistent memory of users, conversations, and messages. Satisfies school requirements #1 (database) and #2 (OOP).

**Architecture:** Three tables — `users`, `conversations`, `messages` — modeled with SQLAlchemy 2.0 DeclarativeBase. A `database.py` module owns the engine and session factory, configured for SQLite at `sophia_memory.db`. Models define relationships (User -> Conversations -> Messages). No business logic in models — they are pure data containers. A thin `service.py` provides CRUD operations that tests and future FastAPI routes will call.

**Tech Stack:** Python 3.12, SQLAlchemy 2.0.49 (DeclarativeBase), SQLite, pytest, dataclasses

---

## File Structure

```
sophia/db/
├── __init__.py       # Package init — exports engine, session, models
├── database.py       # Engine, session factory, Base class, create_all helper
├── models.py         # User, Conversation, Message ORM models
└── service.py        # CRUD functions: create_user, create_conversation, add_message, get_history

tests/
└── test_database.py  # All DB tests — in-memory SQLite, no disk I/O
```

## Design Decisions

**Why `service.py` separate from models?**
Models define shape. Services define behavior. Single responsibility. Models stay clean data containers. Services hold the queries. Future FastAPI routes call services, never construct raw queries.

**Why in-memory SQLite for tests?**
Fast, isolated, no cleanup needed. Each test gets a fresh database via a pytest fixture. No leftover `sophia_memory.db` files polluting the repo.

**Why no Alembic here?**
Alembic is Phase 13. This phase builds the models and uses `Base.metadata.create_all()` for tests and initial development. Migrations come later when schema evolution matters.

**Column conventions:**
- All primary keys: `id`, Integer, autoincrement.
- All timestamps: `created_at`, server_default `func.now()`.
- Foreign keys use `ondelete="CASCADE"` — deleting a user cascades to conversations and messages.
- `email` is unique and indexed. Passwords stored as bcrypt hashes (Phase 10 handles hashing).

---

## Task 1: Base class, engine, and session factory

**Files:**
- Create: `sophia/db/__init__.py`
- Create: `sophia/db/database.py`
- Create: `tests/test_database.py`

- [ ] **Step 1: Write failing test — engine creation**

Create `tests/test_database.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_database.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sophia.db'`

- [ ] **Step 3: Create package init**

Create `sophia/db/__init__.py`:

```python
"""
SophiaAI — Database package.

Public API:
    Base                 — SQLAlchemy DeclarativeBase for all models.
    build_engine         — Creates a SQLAlchemy engine from a URL.
    build_session_factory — Creates a sessionmaker bound to an engine.

Author: Cosmos De La Cruz — SophiaAI Phase 9
"""

from sophia.db.database import Base, build_engine, build_session_factory

__all__ = ["Base", "build_engine", "build_session_factory"]
```

- [ ] **Step 4: Implement database.py**

Create `sophia/db/database.py`:

```python
"""
Database engine, session factory, and declarative base.

Executive Brief:
    Single source of truth for SQLAlchemy configuration.
    All database access in the project flows through the engine
    and session factory created here.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DEFAULT_DATABASE_URL = "sqlite:///./sophia_memory.db"


class Base(DeclarativeBase):
    """Base class for all ORM models in SophiaAI."""


def build_engine(database_url: str = DEFAULT_DATABASE_URL, echo: bool = False) -> Engine:
    """
    Executive Brief:
        Create a SQLAlchemy engine for the given database URL.

    Args:
        database_url: SQLAlchemy connection string. Defaults to local SQLite file.
        echo: If True, log all SQL statements to stdout. Use only during development.

    Returns:
        Engine: A configured SQLAlchemy engine.
    """
    return create_engine(
        database_url,
        echo=echo,
        connect_args={"check_same_thread": False},
    )


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    """
    Executive Brief:
        Create a session factory bound to the given engine.

    Args:
        engine: The SQLAlchemy engine to bind sessions to.

    Returns:
        sessionmaker: A callable that produces new Session instances.
    """
    return sessionmaker(bind=engine)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_database.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add sophia/db/__init__.py sophia/db/database.py tests/test_database.py
git commit -m "feat(phase9): add database engine, session factory, and Base class"
```

---

## Task 2: User model

**Files:**
- Modify: `tests/test_database.py`
- Create: `sophia/db/models.py`
- Modify: `sophia/db/__init__.py`

- [ ] **Step 1: Write failing tests — User model**

Append to `tests/test_database.py`:

```python
from sophia.db.models import User


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_database.py -v`
Expected: FAIL — `ImportError: cannot import name 'User' from 'sophia.db.models'`

- [ ] **Step 3: Implement User model**

Create `sophia/db/models.py`:

```python
"""
ORM models for SophiaAI.

Executive Brief:
    Three tables — users, conversations, messages — that form
    Sophia's persistent memory. Pure data containers with no
    business logic. Relationships define the ownership graph:
    User -> Conversations -> Messages.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sophia.db.database import Base


class User(Base):
    """A registered user of SophiaAI."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    conversations: Mapped[list[Conversation]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email!r})>"
```

**Note:** This file is intentionally incomplete at this step. The `Conversation` forward reference will fail until Task 3 adds it. To keep tests green now, use `TYPE_CHECKING`:

Replace the relationship and import block with this version:

```python
"""
ORM models for SophiaAI.

Executive Brief:
    Three tables — users, conversations, messages — that form
    Sophia's persistent memory. Pure data containers with no
    business logic. Relationships define the ownership graph:
    User -> Conversations -> Messages.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sophia.db.database import Base

if TYPE_CHECKING:
    pass


class User(Base):
    """A registered user of SophiaAI."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    conversations: Mapped[list[Conversation]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email!r})>"
```

This won't work either because `Conversation` doesn't exist yet. Use a string annotation for the relationship:

```python
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
```

SQLAlchemy resolves string references lazily, so this is safe even before `Conversation` is defined. But the `list["Conversation"]` type hint with no Conversation class defined in the module will fail at mapper configuration time when `create_all` is called.

**The correct approach:** Define all three models in a single file in Task 2 so relationships resolve. This keeps Task 2 larger but avoids broken intermediate states. Here is the complete `models.py`:

```python
"""
ORM models for SophiaAI.

Executive Brief:
    Three tables — users, conversations, messages — that form
    Sophia's persistent memory. Pure data containers with no
    business logic. Relationships define the ownership graph:
    User -> Conversations -> Messages.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sophia.db.database import Base


class User(Base):
    """A registered user of SophiaAI."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    conversations: Mapped[list[Conversation]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email!r})>"


class Conversation(Base):
    """A conversation between a user and Sophia."""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="New Conversation")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="conversations")
    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title!r})>"


class Message(Base):
    """A single message in a conversation."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False,
    )
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    conversation: Mapped[Conversation] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role!r})>"
```

- [ ] **Step 4: Update __init__.py exports**

Update `sophia/db/__init__.py`:

```python
"""
SophiaAI — Database package.

Public API:
    Base                 — SQLAlchemy DeclarativeBase for all models.
    build_engine         — Creates a SQLAlchemy engine from a URL.
    build_session_factory — Creates a sessionmaker bound to an engine.
    User                 — ORM model for registered users.
    Conversation         — ORM model for chat conversations.
    Message              — ORM model for individual messages.

Author: Cosmos De La Cruz — SophiaAI Phase 9
"""

from sophia.db.database import Base, build_engine, build_session_factory
from sophia.db.models import Conversation, Message, User

__all__ = [
    "Base",
    "build_engine",
    "build_session_factory",
    "User",
    "Conversation",
    "Message",
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_database.py -v`
Expected: 7 passed (3 from Task 1 + 4 new)

- [ ] **Step 6: Commit**

```bash
git add sophia/db/models.py sophia/db/__init__.py tests/test_database.py
git commit -m "feat(phase9): add User, Conversation, Message ORM models"
```

---

## Task 3: Conversation and Message model tests

**Files:**
- Modify: `tests/test_database.py`

- [ ] **Step 1: Write tests for Conversation model**

Append to `tests/test_database.py`:

```python
from sophia.db.models import Conversation, Message


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
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/test_database.py -v`
Expected: 12 passed (models already exist from Task 2)

- [ ] **Step 3: Commit**

```bash
git add tests/test_database.py
git commit -m "test(phase9): add Conversation and Message model tests"
```

---

## Task 4: Relationship and cascade tests

**Files:**
- Modify: `tests/test_database.py`

- [ ] **Step 1: Write tests for relationships and cascades**

Append to `tests/test_database.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/test_database.py -v`
Expected: 18 passed

- [ ] **Step 3: Commit**

```bash
git add tests/test_database.py
git commit -m "test(phase9): add relationship and cascade tests"
```

---

## Task 5: Service layer — CRUD operations

**Files:**
- Create: `sophia/db/service.py`
- Modify: `tests/test_database.py`
- Modify: `sophia/db/__init__.py`

- [ ] **Step 1: Write failing tests for service functions**

Append to `tests/test_database.py`:

```python
from sophia.db.service import (
    create_user,
    get_user_by_email,
    create_conversation,
    get_conversations_for_user,
    add_message,
    get_conversation_with_messages,
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_database.py -v`
Expected: FAIL — `ImportError: cannot import name 'create_user' from 'sophia.db.service'`

- [ ] **Step 3: Implement service.py**

Create `sophia/db/service.py`:

```python
"""
Database service layer — CRUD operations for SophiaAI.

Executive Brief:
    Pure query functions that accept a Session and return model instances.
    No HTTP, no auth, no business logic beyond the query itself.
    FastAPI routes and CLI tools call these; they never construct
    raw queries themselves.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from sophia.db.models import Conversation, Message, User


def create_user(session: Session, email: str, hashed_password: str) -> User:
    """
    Executive Brief:
        Insert a new user and return the persisted instance.

    Args:
        session: Active SQLAlchemy session.
        email: Unique email address.
        hashed_password: Pre-hashed password (hashing is the caller's job).

    Returns:
        User: The newly created user with a populated id.
    """
    user = User(email=email, hashed_password=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user_by_email(session: Session, email: str) -> User | None:
    """
    Executive Brief:
        Look up a user by email. Returns None if not found.
    """
    return session.query(User).filter(User.email == email).first()


def create_conversation(
    session: Session,
    user_id: int,
    title: str = "New Conversation",
) -> Conversation:
    """
    Executive Brief:
        Create a new conversation for the given user.

    Args:
        session: Active SQLAlchemy session.
        user_id: The owning user's id.
        title: Display title for the conversation.

    Returns:
        Conversation: The newly created conversation with a populated id.
    """
    conversation = Conversation(user_id=user_id, title=title)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


def get_conversations_for_user(session: Session, user_id: int) -> list[Conversation]:
    """
    Executive Brief:
        Return all conversations belonging to a user, newest first.
    """
    return (
        session.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
        .all()
    )


def add_message(
    session: Session,
    conversation_id: int,
    role: str,
    content: str,
    sources_json: str | None = None,
) -> Message:
    """
    Executive Brief:
        Append a message to a conversation.

    Args:
        session: Active SQLAlchemy session.
        conversation_id: The conversation this message belongs to.
        role: "user" or "sophia".
        content: The message text.
        sources_json: Optional JSON string of source citations.

    Returns:
        Message: The newly created message with a populated id.
    """
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        sources_json=sources_json,
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


def get_conversation_with_messages(
    session: Session,
    conversation_id: int,
) -> Conversation | None:
    """
    Executive Brief:
        Fetch a conversation by id with its messages eagerly loaded.
        Returns None if the conversation does not exist.
    """
    conversation = session.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation is not None:
        _ = conversation.messages
    return conversation
```

- [ ] **Step 4: Update __init__.py exports**

Update `sophia/db/__init__.py` to add service exports:

```python
"""
SophiaAI — Database package.

Public API:
    Base                 — SQLAlchemy DeclarativeBase for all models.
    build_engine         — Creates a SQLAlchemy engine from a URL.
    build_session_factory — Creates a sessionmaker bound to an engine.
    User                 — ORM model for registered users.
    Conversation         — ORM model for chat conversations.
    Message              — ORM model for individual messages.
    create_user          — Insert a new user.
    get_user_by_email    — Look up a user by email.
    create_conversation  — Start a new conversation for a user.
    get_conversations_for_user — List conversations for a user.
    add_message          — Append a message to a conversation.
    get_conversation_with_messages — Fetch a conversation with its messages.

Author: Cosmos De La Cruz — SophiaAI Phase 9
"""

from sophia.db.database import Base, build_engine, build_session_factory
from sophia.db.models import Conversation, Message, User
from sophia.db.service import (
    add_message,
    create_conversation,
    create_user,
    get_conversation_with_messages,
    get_conversations_for_user,
    get_user_by_email,
)

__all__ = [
    "Base",
    "build_engine",
    "build_session_factory",
    "User",
    "Conversation",
    "Message",
    "create_user",
    "get_user_by_email",
    "create_conversation",
    "get_conversations_for_user",
    "add_message",
    "get_conversation_with_messages",
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_database.py -v`
Expected: 27 passed

- [ ] **Step 6: Commit**

```bash
git add sophia/db/service.py sophia/db/__init__.py tests/test_database.py
git commit -m "feat(phase9): add service layer with CRUD operations"
```

---

## Task 6: Full suite regression check + cosmos_log

**Files:**
- Modify: `documentation/cosmos_log.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests pass (previous 76 + new ~27 = ~103 total), 0 failures, 0 regressions.

- [ ] **Step 2: Verify table count**

Run a quick sanity script:

```bash
python -c "from sophia.db import Base, build_engine; e = build_engine('sqlite:///:memory:'); Base.metadata.create_all(e); print([t for t in Base.metadata.tables]); e.dispose()"
```

Expected output: `['users', 'conversations', 'messages']`

- [ ] **Step 3: Update CLAUDE.md project state**

Change the project state line in `CLAUDE.md` from:
```
Phase 8 complete. Ready to start Phase 9 - Database Layer
```
To:
```
Phase 9 complete. Ready to start Phase 10 - Auth Layer
```

- [ ] **Step 4: Append Phase 9 entry to cosmos_log.md**

Add a Phase 9 section documenting: what was built, artifacts, key decisions (three tables, service layer, in-memory test strategy), test counts, and what comes next (Phase 10 — Auth Layer).

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md documentation/cosmos_log.md
git commit -m "docs(phase9): update cosmos_log and CLAUDE.md for Phase 9 completion"
```

---

## Self-Review Results

**Spec coverage:**
- `database.py` with engine + session factory: Task 1 ✓
- `models.py` with User, Conversation, Message: Task 2 ✓
- Three tables (users, conversations, messages): Task 2 ✓
- SQLAlchemy 2.0 DeclarativeBase: Task 1 (Base class) ✓
- Relationships and cascades: Task 2 (code) + Task 4 (tests) ✓
- `__init__.py` exports: Tasks 1, 2, 5 ✓
- Service layer (beyond spec, but supports school OOP requirement): Task 5 ✓
- Full regression: Task 6 ✓

**Placeholder scan:** No TBD, TODO, or "implement later" found. All code blocks are complete.

**Type consistency:** `build_engine`, `build_session_factory`, `Base`, model names, and service function signatures are consistent across all tasks.

**Spec gap found:** The developing_plan.md mentions `sophia_memory.db` as the database file — `DEFAULT_DATABASE_URL` in `database.py` matches (`sqlite:///./sophia_memory.db`). ✓