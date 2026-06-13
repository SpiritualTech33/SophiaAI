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

from sophia.db.models import Conversation, Message, User, UserFile


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


def delete_conversation(session: Session, conversation_id: int) -> bool:
    """
    Executive Brief:
        Delete a conversation by id. Its messages are removed too via the
        cascade defined on the Conversation.messages relationship. Returns
        True if a conversation was deleted, False if none had that id.
        Ownership is the caller's check.

    Args:
        session: Active SQLAlchemy session.
        conversation_id: The conversation to delete.

    Returns:
        bool: True when a conversation was removed, False when not found.
    """
    conversation = (
        session.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )
    if conversation is None:
        return False
    session.delete(conversation)
    session.commit()
    return True


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


def create_user_file(
    session: Session,
    user_id: int,
    conversation_id: int | None,
    original_filename: str,
    stored_path: str,
    mime_type: str,
    extracted_text: str,
    size_bytes: int,
) -> UserFile:
    """
    Executive Brief:
        Persist a record of an uploaded file. The bytes already live on disk at
        stored_path; this stores the metadata plus the cached extracted text.

    Returns:
        UserFile: The newly created record with a populated id.
    """
    record = UserFile(
        user_id=user_id,
        conversation_id=conversation_id,
        original_filename=original_filename,
        stored_path=stored_path,
        mime_type=mime_type,
        extracted_text=extracted_text,
        size_bytes=size_bytes,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_user_file(session: Session, file_id: int, user_id: int) -> UserFile | None:
    """
    Executive Brief:
        Fetch a file by id, scoped to its owner. Returns None when the file does
        not exist or belongs to a different user — ownership is enforced here so
        callers cannot read another user's file by guessing its id.
    """
    return (
        session.query(UserFile)
        .filter(UserFile.id == file_id, UserFile.user_id == user_id)
        .first()
    )


def get_user_files(session: Session, file_ids: list[int], user_id: int) -> list[UserFile]:
    """
    Executive Brief:
        Return the full records of the given files, owner-scoped and kept in
        the caller's id order. Files the user does not own are silently
        skipped, so a forged id is invisible to the caller.
    """
    if not file_ids:
        return []
    owned = (
        session.query(UserFile)
        .filter(UserFile.id.in_(file_ids), UserFile.user_id == user_id)
        .all()
    )
    by_id = {record.id: record for record in owned}
    return [by_id[fid] for fid in file_ids if fid in by_id]


def get_files_text(session: Session, file_ids: list[int], user_id: int) -> list[str]:
    """
    Executive Brief:
        Return the extracted text of the given files, owner-scoped and kept in
        the caller's id order. Files the user does not own are silently skipped,
        so a forged id injects nothing into the prompt.
    """
    if not file_ids:
        return []
    owned = (
        session.query(UserFile)
        .filter(UserFile.id.in_(file_ids), UserFile.user_id == user_id)
        .all()
    )
    text_by_id = {record.id: record.extracted_text for record in owned}
    return [text_by_id[fid] for fid in file_ids if fid in text_by_id]
