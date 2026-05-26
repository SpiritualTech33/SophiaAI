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
