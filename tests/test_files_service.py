"""
Tests for the UserFile model and its service-layer CRUD.

Strategy: a private in-memory SQLite session (no HTTP). Exercises creation,
ownership-scoped reads, and the ordered text fetch used for chat injection.

Run: pytest tests/test_files_service.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from sophia.db.database import Base, build_session_factory
from sophia.db.models import UserFile
from sophia.db.service import (
    create_user,
    create_user_file,
    get_files_text,
    get_user_file,
)


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = build_session_factory(engine)
    db = factory()
    yield db
    db.close()
    engine.dispose()


def _make_file(session, user_id, name="doc.txt", text="hello"):
    return create_user_file(
        session,
        user_id=user_id,
        conversation_id=None,
        original_filename=name,
        stored_path=f"/uploads/{user_id}/{name}",
        mime_type="text/plain",
        extracted_text=text,
        size_bytes=len(text),
    )


def test_create_user_file_persists_with_id(session):
    user = create_user(session, "owner@sophia.ai", "hash")
    record = _make_file(session, user.id, text="The Tao is silent.")
    assert record.id is not None
    assert record.user_id == user.id
    assert record.extracted_text == "The Tao is silent."


def test_get_user_file_returns_owned_file(session):
    user = create_user(session, "owner@sophia.ai", "hash")
    record = _make_file(session, user.id)
    fetched = get_user_file(session, record.id, user.id)
    assert fetched is not None
    assert fetched.id == record.id


def test_get_user_file_denies_other_users_file(session):
    owner = create_user(session, "owner@sophia.ai", "hash")
    intruder = create_user(session, "intruder@sophia.ai", "hash")
    record = _make_file(session, owner.id)
    # Intruder must not be able to read the owner's file.
    assert get_user_file(session, record.id, intruder.id) is None


def test_get_user_file_missing_returns_none(session):
    user = create_user(session, "owner@sophia.ai", "hash")
    assert get_user_file(session, 999, user.id) is None


def test_get_files_text_returns_owned_texts_in_request_order(session):
    user = create_user(session, "owner@sophia.ai", "hash")
    a = _make_file(session, user.id, name="a.txt", text="alpha")
    b = _make_file(session, user.id, name="b.txt", text="beta")
    texts = get_files_text(session, [b.id, a.id], user.id)
    assert texts == ["beta", "alpha"]


def test_get_files_text_skips_files_not_owned(session):
    owner = create_user(session, "owner@sophia.ai", "hash")
    intruder = create_user(session, "intruder@sophia.ai", "hash")
    mine = _make_file(session, owner.id, text="mine")
    theirs = _make_file(session, intruder.id, text="theirs")
    texts = get_files_text(session, [mine.id, theirs.id], owner.id)
    assert texts == ["mine"]


def test_get_files_text_empty_for_no_ids(session):
    user = create_user(session, "owner@sophia.ai", "hash")
    assert get_files_text(session, [], user.id) == []


def test_user_file_is_registered_on_metadata():
    assert "user_files" in Base.metadata.tables
    assert UserFile.__tablename__ == "user_files"
