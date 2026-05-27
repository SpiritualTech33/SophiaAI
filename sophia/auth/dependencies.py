"""
FastAPI authentication dependencies for SophiaAI.

Executive Brief:
    Provides get_current_user — a callable that extracts a JWT
    from the request, validates it, and returns the User ORM instance.
    Designed as a pure function now; wired as a FastAPI Depends()
    in Phase 11 when routes are created.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from sophia.auth.security import decode_access_token
from sophia.db.models import User
from sophia.db.service import get_user_by_email


def get_current_user(
    token: str,
    secret_key: str,
    session: Session,
) -> User:
    """
    Executive Brief:
        Validate a JWT and return the corresponding User from the database.

    Args:
        token: The raw JWT string (extracted from Authorization header by the caller).
        secret_key: The HMAC key for token verification.
        session: An active SQLAlchemy session.

    Returns:
        User: The authenticated user.

    Raises:
        ValueError: If the token is invalid, expired, or the user does not exist.
    """
    payload = decode_access_token(token, secret_key)
    email = payload.get("sub")
    if email is None:
        raise ValueError("Token is invalid: missing subject claim")

    user = get_user_by_email(session, email)
    if user is None:
        raise ValueError(f"User not found: {email}")

    return user
