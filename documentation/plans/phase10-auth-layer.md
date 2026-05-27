# Phase 10 — Auth Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add password hashing (bcrypt) and JWT authentication to SophiaAI, wiring into the User model from Phase 9. Satisfies school requirement #4 (login).

**Architecture:** Two files in `sophia/auth/`. `security.py` owns all cryptographic operations — hashing passwords with passlib and creating/decoding JWT tokens with python-jose. `dependencies.py` owns the FastAPI integration — a `get_current_user` dependency that extracts the JWT from the request, validates it, and returns the User ORM instance. No business logic leaks into either file; they are pure utilities consumed by future route handlers (Phase 11).

**Tech Stack:** passlib[bcrypt] >= 1.7.4, python-jose[cryptography] >= 3.3.0, SQLAlchemy (from Phase 9), FastAPI (dependency injection only — no routes yet).

---

## File Structure

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `sophia/auth/__init__.py` | Public API exports for the auth package |
| Create | `sophia/auth/security.py` | `hash_password`, `verify_password`, `create_access_token`, `decode_access_token` |
| Create | `sophia/auth/dependencies.py` | `get_current_user` FastAPI dependency |
| Create | `tests/test_auth.py` | All Phase 10 tests (~13 tests) |

**Dependencies from Phase 9 (read-only, no modifications):**
- `sophia/db/models.py` — `User` model
- `sophia/db/service.py` — `get_user_by_email`
- `sophia/db/database.py` — `Base`, `build_engine`, `build_session_factory`

---

### Task 1: Password Hashing — Tests First

**Files:**
- Create: `tests/test_auth.py`
- Create: `sophia/auth/__init__.py` (empty placeholder)
- Create: `sophia/auth/security.py`

- [ ] **Step 1: Create the auth package placeholder**

Create `sophia/auth/__init__.py` so Python can import from the package:

```python
"""
SophiaAI — Auth package.
"""
```

- [ ] **Step 2: Write failing tests for password hashing**

Create `tests/test_auth.py`:

```python
"""
Unit tests for sophia.auth.

Strategy: pure unit tests for hashing and JWT — no database needed
for Tasks 1-2. Task 3 uses in-memory SQLite for the FastAPI dependency.

Run: pytest tests/test_auth.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_auth.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sophia.auth.security'`

- [ ] **Step 4: Implement password hashing**

Create `sophia/auth/security.py`:

```python
"""
Cryptographic utilities for SophiaAI authentication.

Executive Brief:
    Password hashing with bcrypt via passlib. JWT creation and
    verification with python-jose. All secrets read from environment
    variables — nothing hardcoded in production.
"""

from __future__ import annotations

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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_auth.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add sophia/auth/__init__.py sophia/auth/security.py tests/test_auth.py
git commit -m "feat(phase10): add password hashing with bcrypt — 4 tests"
```

---

### Task 2: JWT Token Creation and Verification

**Files:**
- Modify: `sophia/auth/security.py` — add `create_access_token`, `decode_access_token`
- Modify: `tests/test_auth.py` — add JWT tests

- [ ] **Step 1: Write failing tests for JWT**

Append to `tests/test_auth.py`:

```python
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
    import pytest

    token = create_access_token(
        subject="user@test.com",
        secret_key=JWT_TEST_SECRET,
        expires_delta=timedelta(seconds=-1),
    )
    with pytest.raises(ValueError, match="expired"):
        decode_access_token(token, secret_key=JWT_TEST_SECRET)


def test_decode_access_token_rejects_invalid_token():
    """decode_access_token raises ValueError for a tampered token."""
    import pytest

    with pytest.raises(ValueError, match="invalid"):
        decode_access_token("this.is.garbage", secret_key=JWT_TEST_SECRET)


def test_decode_access_token_rejects_wrong_secret():
    """decode_access_token raises ValueError when secret doesn't match."""
    import pytest

    token = create_access_token(
        subject="user@test.com",
        secret_key=JWT_TEST_SECRET,
    )
    with pytest.raises(ValueError, match="invalid"):
        decode_access_token(token, secret_key="wrong-secret-key")
```

- [ ] **Step 2: Run tests to verify new tests fail**

Run: `pytest tests/test_auth.py -v`
Expected: 4 passed, 6 FAILED (import error for `create_access_token`)

- [ ] **Step 3: Implement JWT functions**

Add to `sophia/auth/security.py` (below existing code):

```python
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

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
```

- [ ] **Step 4: Run tests to verify all pass**

Run: `pytest tests/test_auth.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add sophia/auth/security.py tests/test_auth.py
git commit -m "feat(phase10): add JWT create/decode with python-jose — 10 tests"
```

---

### Task 3: FastAPI `get_current_user` Dependency

**Files:**
- Create: `sophia/auth/dependencies.py`
- Modify: `tests/test_auth.py` — add dependency tests

- [ ] **Step 1: Write failing tests for `get_current_user`**

Append to `tests/test_auth.py`:

```python
import pytest
from sqlalchemy.orm import Session

from sophia.db.database import Base, build_engine, build_session_factory
from sophia.db.models import User
from sophia.db.service import create_user
from sophia.auth.security import hash_password, create_access_token
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
```

- [ ] **Step 2: Run tests to verify new tests fail**

Run: `pytest tests/test_auth.py -v`
Expected: 10 passed, 3 FAILED (import error for `get_current_user`)

- [ ] **Step 3: Implement `get_current_user`**

Create `sophia/auth/dependencies.py`:

```python
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
from sophia.db.service import get_user_by_email
from sophia.db.models import User


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
```

- [ ] **Step 4: Run tests to verify all pass**

Run: `pytest tests/test_auth.py -v`
Expected: 13 passed

- [ ] **Step 5: Commit**

```bash
git add sophia/auth/dependencies.py tests/test_auth.py
git commit -m "feat(phase10): add get_current_user dependency — 13 tests"
```

---

### Task 4: Package Exports and Full Verification

**Files:**
- Modify: `sophia/auth/__init__.py` — add public API exports

- [ ] **Step 1: Update `__init__.py` with public exports**

```python
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
```

- [ ] **Step 2: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests pass (103 existing + 13 new = 116 total, minus any skips)

- [ ] **Step 3: Verify imports work from package level**

Run: `python -c "from sophia.auth import hash_password, verify_password, create_access_token, decode_access_token, get_current_user; print('All imports OK')"`
Expected: `All imports OK`

- [ ] **Step 4: Final commit**

```bash
git add sophia/auth/__init__.py
git commit -m "feat(phase10): finalize auth package exports"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Password hashing with passlib bcrypt → Task 1 (`hash_password`, `verify_password`)
- [x] JWT creation and verification with python-jose → Task 2 (`create_access_token`, `decode_access_token`)
- [x] Integration with User model from Phase 9 → Task 3 (`get_current_user` queries User via `get_user_by_email`)
- [x] FastAPI dependency → Task 3 (`get_current_user` — pure function now, wired as `Depends()` in Phase 11)
- [x] 24-hour token lifetime → `DEFAULT_TOKEN_LIFETIME_HOURS = 24` in security.py
- [x] JWT_SECRET from env variable → secret_key passed as argument; env reading deferred to Phase 11 app startup

**Placeholder scan:** No TBDs, no TODOs, no "implement later". Every step has code.

**Type consistency:** `hash_password` → str, `verify_password` → bool, `create_access_token` → str, `decode_access_token` → dict, `get_current_user` → User. All consistent across tests and implementation.

**Phase 9 contract:** `get_user_by_email(session, email) -> User | None` — used exactly as defined. No modifications to Phase 9 code.