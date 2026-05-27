"""
Unit tests for sophia.auth.

Strategy: pure unit tests for hashing and JWT — no database needed
for Tasks 1-2. Task 3 uses in-memory SQLite for the FastAPI dependency.

Run: pytest tests/test_auth.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.auth.security import hash_password, verify_password


def test_hash_password_returns_bcrypt_string():
    """hash_password returns a bcrypt hash, not the plaintext."""
    hashed = hash_password("mysecret")
    assert hashed != "mysecret"
    assert hashed.startswith("$2b$")


def test_verify_password_correct():
    """verify_password returns True when password matches the hash."""
    hashed = hash_password("correcthorse")
    assert verify_password("correcthorse", hashed) is True


def test_verify_password_wrong():
    """verify_password returns False for an incorrect password."""
    hashed = hash_password("correcthorse")
    assert verify_password("wronghorse", hashed) is False


def test_hash_password_salts_differently():
    """Two hashes of the same password differ (bcrypt uses random salt)."""
    hash_one = hash_password("samepass")
    hash_two = hash_password("samepass")
    assert hash_one != hash_two


# ---------------------------------------------------------------------------
# Task 2: JWT Token Creation and Verification
# ---------------------------------------------------------------------------

from datetime import timedelta

from sophia.auth.security import create_access_token, decode_access_token


JWT_TEST_SECRET = "test-secret-key-not-for-production"


def test_create_access_token_returns_string():
    """create_access_token returns a non-empty JWT string."""
    token = create_access_token(
        subject="user@test.com",
        secret_key=JWT_TEST_SECRET,
    )
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_access_token_extracts_subject():
    """decode_access_token returns the email encoded in the token."""
    token = create_access_token(
        subject="sophia@spiritual.tech",
        secret_key=JWT_TEST_SECRET,
    )
    payload = decode_access_token(token, secret_key=JWT_TEST_SECRET)
    assert payload["sub"] == "sophia@spiritual.tech"


def test_create_access_token_sets_expiration():
    """The token payload contains an 'exp' claim."""
    token = create_access_token(
        subject="user@test.com",
        secret_key=JWT_TEST_SECRET,
        expires_delta=timedelta(hours=1),
    )
    payload = decode_access_token(token, secret_key=JWT_TEST_SECRET)
    assert "exp" in payload


def test_decode_access_token_rejects_expired_token():
    """decode_access_token raises ValueError for an expired token."""
    token = create_access_token(
        subject="user@test.com",
        secret_key=JWT_TEST_SECRET,
        expires_delta=timedelta(seconds=-1),
    )
    with pytest.raises(ValueError, match="expired"):
        decode_access_token(token, secret_key=JWT_TEST_SECRET)


def test_decode_access_token_rejects_invalid_token():
    """decode_access_token raises ValueError for a tampered token."""
    with pytest.raises(ValueError, match="invalid"):
        decode_access_token("this.is.garbage", secret_key=JWT_TEST_SECRET)


def test_decode_access_token_rejects_wrong_secret():
    """decode_access_token raises ValueError when secret doesn't match."""
    token = create_access_token(
        subject="user@test.com",
        secret_key=JWT_TEST_SECRET,
    )
    with pytest.raises(ValueError, match="invalid"):
        decode_access_token(token, secret_key="wrong-secret-key")


# ---------------------------------------------------------------------------
# Task 3: get_current_user FastAPI Dependency
# ---------------------------------------------------------------------------

from sophia.db.database import Base, build_engine, build_session_factory
from sophia.db.service import create_user
from sophia.auth.dependencies import get_current_user


@pytest.fixture
def db_session():
    """Yield a fresh in-memory database session for auth tests."""
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)
    session = session_factory()
    yield session
    session.close()
    engine.dispose()


def test_get_current_user_returns_user_for_valid_token(db_session):
    """get_current_user returns the User when token and user are valid."""
    hashed = hash_password("password123")
    user = create_user(db_session, email="valid@test.com", hashed_password=hashed)

    token = create_access_token(subject="valid@test.com", secret_key=JWT_TEST_SECRET)

    result = get_current_user(
        token=token,
        secret_key=JWT_TEST_SECRET,
        session=db_session,
    )
    assert result.id == user.id
    assert result.email == "valid@test.com"


def test_get_current_user_raises_for_invalid_token(db_session):
    """get_current_user raises ValueError for a garbage token."""
    with pytest.raises(ValueError, match="invalid"):
        get_current_user(
            token="not.a.real.token",
            secret_key=JWT_TEST_SECRET,
            session=db_session,
        )


def test_get_current_user_raises_for_nonexistent_user(db_session):
    """get_current_user raises ValueError when token is valid but user was deleted."""
    token = create_access_token(subject="ghost@test.com", secret_key=JWT_TEST_SECRET)

    with pytest.raises(ValueError, match="not found"):
        get_current_user(
            token=token,
            secret_key=JWT_TEST_SECRET,
            session=db_session,
        )
