"""
SophiaAI — Auth package.

Public API:
    hash_password          — Hash a plaintext password with bcrypt.
    verify_password        — Verify a password against a stored hash.
    create_access_token    — Create a signed JWT.
    decode_access_token    — Decode and validate a JWT.
    get_current_user       — Validate token and return the User.

Author: Cosmos De La Cruz — SophiaAI Phase 10
"""

from sophia.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from sophia.auth.dependencies import get_current_user

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "get_current_user",
]
