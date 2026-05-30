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


def update_conversation_title(
    session: Session,
    conversation_id: int,
    title: str,
) -> Conversation | None:
    """
    Executive Brief:
        Rename a conversation. Returns the updated conversation, or None if
        no conversation has that id. Ownership is the caller's check.

    Args:
        session: Active SQLAlchemy session.
        conversation_id: The conversation to rename.
        title: The new display title.

    Returns:
        Conversation | None: Updated instance, or None when not found.
    """
    conversation = (
        session.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )
    if conversation is None:
        return None
    conversation.title = title
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
    conversation = (
        session.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )
    if conversation is not None:
        _ = conversation.messages
    return conversation
