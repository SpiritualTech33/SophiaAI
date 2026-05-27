"""
Cryptographic utilities for SophiaAI authentication.

Executive Brief:
    Password hashing with bcrypt via passlib. JWT creation and
    verification with python-jose. All secrets read from environment
    variables — nothing hardcoded in production.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Executive Brief:
        Hash a plaintext password using bcrypt.

    Args:
        plain_password: The user's raw password.

    Returns:
        str: A bcrypt hash string starting with '$2b$'.
    """
    return password_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Executive Brief:
        Verify a plaintext password against a stored bcrypt hash.

    Args:
        plain_password: The password the user just typed.
        hashed_password: The stored hash from the database.

    Returns:
        bool: True if password matches, False otherwise.
    """
    return password_context.verify(plain_password, hashed_password)


ALGORITHM = "HS256"
DEFAULT_TOKEN_LIFETIME_HOURS = 24


def create_access_token(
    subject: str,
    secret_key: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Executive Brief:
        Create a signed JWT containing the user's identity.

    Args:
        subject: The value stored in the 'sub' claim (typically email).
        secret_key: The HMAC key used to sign the token.
        expires_delta: Custom token lifetime. Defaults to 24 hours.

    Returns:
        str: An encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    if expires_delta is None:
        expires_delta = timedelta(hours=DEFAULT_TOKEN_LIFETIME_HOURS)
    expire = now + expires_delta

    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> dict:
    """
    Executive Brief:
        Decode and validate a JWT. Returns the payload dict on success.

    Args:
        token: The raw JWT string from the Authorization header.
        secret_key: The HMAC key used to verify the signature.

    Returns:
        dict: The decoded payload with at least 'sub' and 'exp' keys.

    Raises:
        ValueError: If the token is expired, tampered, or malformed.
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError as jwt_error:
        error_message = str(jwt_error).lower()
        if "expired" in error_message:
            raise ValueError("Token has expired") from jwt_error
        raise ValueError("Token is invalid") from jwt_error
