# Phase 11 — FastAPI Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire all existing modules (auth, db, orchestrator, retriever, LLM client) behind HTTP endpoints to create a working FastAPI web application. Satisfies school requirement #3 (framework).

**Architecture:** A `sophia/app/` package containing `main.py` (app factory + lifespan), `schemas.py` (Pydantic request/response models), `dependencies.py` (FastAPI dependency injection), and three sub-routers under `sophia/app/routers/` — `auth.py` (register/login), `chat.py` (conversation endpoints), `pages.py` (placeholder HTML pages for Phase 12). Heavy objects (SophiaRetriever, GroqClient, Sophia orchestrator) initialize once during app lifespan and live on `app.state`. Database sessions use a yield-based dependency. Authentication wraps Phase 10's `get_current_user` into a proper FastAPI `Depends()` chain with `OAuth2PasswordBearer`.

**Tech Stack:** FastAPI >= 0.115.0, Uvicorn, Pydantic v2, python-dotenv, httpx (test client). All other dependencies from Phases 5-10.

---

## File Structure

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `sophia/app/__init__.py` | Package exports |
| Create | `sophia/app/schemas.py` | Pydantic models for all request/response bodies |
| Create | `sophia/app/dependencies.py` | `get_db_session`, `get_authenticated_user` FastAPI dependencies |
| Create | `sophia/app/routers/__init__.py` | Empty — makes routers a package |
| Create | `sophia/app/routers/auth.py` | `POST /auth/register`, `POST /auth/login` |
| Create | `sophia/app/routers/chat.py` | `POST /api/chat`, `GET /api/conversations`, `GET /api/conversations/{id}` |
| Create | `sophia/app/routers/pages.py` | `GET /`, `GET /chat`, `GET /login`, `GET /register` (placeholder HTML) |
| Create | `sophia/app/main.py` | `create_app()` factory, `lifespan()` context manager, CORS |
| Create | `tests/conftest.py` | Shared fixtures: test app, test client, auth helpers |
| Create | `tests/test_app_auth.py` | Auth endpoint tests (~5 tests) |
| Create | `tests/test_app_chat.py` | Chat endpoint tests (~6 tests) |
| Create | `tests/test_app_pages.py` | Pages endpoint tests (~4 tests) |
| Modify | `.env.example` | Add `JWT_SECRET` and `DATABASE_URL` |

**Dependencies from prior phases (read-only, no modifications):**
- `sophia/auth/security.py` — `hash_password`, `verify_password`, `create_access_token`, `decode_access_token`
- `sophia/auth/dependencies.py` — `get_current_user(token, secret_key, session)`
- `sophia/db/database.py` — `Base`, `build_engine`, `build_session_factory`
- `sophia/db/models.py` — `User`, `Conversation`, `Message`
- `sophia/db/service.py` — all CRUD functions
- `sophia/core/orchestrator.py` — `Sophia`, `SophiaResponse`
- `sophia/rag/retriever.py` — `SophiaRetriever`, `Chunk`
- `sophia/llm/groq_client.py` — `GroqClient`

---

### Task 1: Package Structure + Pydantic Schemas

**Files:**
- Create: `sophia/app/__init__.py`
- Create: `sophia/app/routers/__init__.py`
- Create: `sophia/app/schemas.py`
- Create: `tests/test_app_schemas.py`

- [ ] **Step 1: Create package directories and init files**

Create `sophia/app/__init__.py`:

```python
"""
SophiaAI — Web Application package.

Public API:
    create_app — Factory that builds and configures the FastAPI instance.

Author: Cosmos De La Cruz — SophiaAI Phase 11
"""
```

Create `sophia/app/routers/__init__.py`:

```python
"""SophiaAI — Router sub-package."""
```

- [ ] **Step 2: Write failing tests for Pydantic schemas**

Create `tests/test_app_schemas.py`:

```python
"""
Unit tests for sophia.app.schemas.

Strategy: validate Pydantic models accept good input, reject bad input,
and produce correct defaults.

Run: pytest tests/test_app_schemas.py -v
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.app.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationSummary,
    LoginRequest,
    MessageOut,
    RegisterRequest,
    SourceOut,
    TokenResponse,
)


def test_register_request_valid():
    """RegisterRequest accepts a valid email and password."""
    req = RegisterRequest(email="test@example.com", password="secret123")
    assert req.email == "test@example.com"
    assert req.password == "secret123"


def test_register_request_rejects_bad_email():
    """RegisterRequest rejects a malformed email."""
    with pytest.raises(Exception):
        RegisterRequest(email="not-an-email", password="secret123")


def test_login_request_valid():
    """LoginRequest accepts a valid email and password."""
    req = LoginRequest(email="user@sophia.ai", password="pass")
    assert req.email == "user@sophia.ai"


def test_token_response_defaults():
    """TokenResponse sets token_type to 'bearer' by default."""
    resp = TokenResponse(access_token="abc.def.ghi")
    assert resp.token_type == "bearer"


def test_chat_request_defaults():
    """ChatRequest makes conversation_id optional (None by default)."""
    req = ChatRequest(message="What is wisdom?")
    assert req.message == "What is wisdom?"
    assert req.conversation_id is None


def test_chat_request_with_conversation_id():
    """ChatRequest accepts an explicit conversation_id."""
    req = ChatRequest(message="Tell me more", conversation_id=42)
    assert req.conversation_id == 42


def test_chat_response_structure():
    """ChatResponse holds answer, sources list, conversation_id, search_mode."""
    resp = ChatResponse(
        answer="Wisdom is...",
        sources=[SourceOut(text="passage", source_file="f.md", pillar="mind", score=0.8)],
        conversation_id=1,
        search_mode="corpus",
    )
    assert resp.answer == "Wisdom is..."
    assert len(resp.sources) == 1
    assert resp.sources[0].pillar == "mind"


def test_conversation_summary():
    """ConversationSummary holds id, title, timestamps."""
    now = datetime.now()
    summary = ConversationSummary(id=1, title="Test", created_at=now, updated_at=now)
    assert summary.id == 1
    assert summary.title == "Test"


def test_message_out():
    """MessageOut holds message fields including nullable sources_json."""
    now = datetime.now()
    msg = MessageOut(id=1, role="user", content="Hello", sources_json=None, created_at=now)
    assert msg.role == "user"
    assert msg.sources_json is None


def test_conversation_detail():
    """ConversationDetail nests a list of MessageOut."""
    now = datetime.now()
    detail = ConversationDetail(
        id=1,
        title="My chat",
        messages=[
            MessageOut(id=1, role="user", content="Hi", sources_json=None, created_at=now),
            MessageOut(id=2, role="sophia", content="Hello", sources_json='[]', created_at=now),
        ],
    )
    assert len(detail.messages) == 2
    assert detail.messages[1].role == "sophia"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_app_schemas.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sophia.app.schemas'`

- [ ] **Step 4: Write the schemas module**

Create `sophia/app/schemas.py`:

```python
"""
Pydantic request and response models for SophiaAI endpoints.

Executive Brief:
    Every HTTP request body and response body has a corresponding
    Pydantic model here. No raw dicts cross the API boundary.
    FastAPI uses these for automatic validation, serialization,
    and OpenAPI documentation.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    """Body for POST /auth/register."""
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """Body for POST /auth/login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response containing a JWT access token."""
    access_token: str
    token_type: str = "bearer"


class ChatRequest(BaseModel):
    """Body for POST /api/chat."""
    message: str
    conversation_id: int | None = None


class SourceOut(BaseModel):
    """One source citation in a chat response."""
    text: str
    source_file: str
    pillar: str
    score: float


class ChatResponse(BaseModel):
    """Response from POST /api/chat."""
    answer: str
    sources: list[SourceOut]
    conversation_id: int
    search_mode: str


class ConversationSummary(BaseModel):
    """One conversation in the list returned by GET /api/conversations."""
    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    """One message inside a conversation detail response."""
    id: int
    role: str
    content: str
    sources_json: str | None
    created_at: datetime


class ConversationDetail(BaseModel):
    """Full conversation with messages for GET /api/conversations/{id}."""
    id: int
    title: str
    messages: list[MessageOut]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_app_schemas.py -v`
Expected: 11 PASSED

- [ ] **Step 6: Commit**

```bash
git add sophia/app/__init__.py sophia/app/routers/__init__.py sophia/app/schemas.py tests/test_app_schemas.py
git commit -m "feat(phase11): add app package structure and Pydantic schemas with 11 tests"
```

---

### Task 2: FastAPI Dependencies

**Files:**
- Create: `sophia/app/dependencies.py`

- [ ] **Step 1: Write the dependencies module**

Create `sophia/app/dependencies.py`:

```python
"""
FastAPI dependency injection functions for SophiaAI.

Executive Brief:
    Two dependencies that thread through every protected endpoint:
    get_db_session yields a SQLAlchemy session per request (auto-closed),
    get_authenticated_user extracts + validates the JWT and returns the User.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from sophia.auth.dependencies import get_current_user as _get_current_user
from sophia.db.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db_session(request: Request):
    """
    Executive Brief:
        Yield a SQLAlchemy session from the app-level session factory.
        The session is closed after the request completes, whether
        it succeeded or raised.
    """
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_authenticated_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_db_session),
) -> User:
    """
    Executive Brief:
        Extract the Bearer token from the Authorization header,
        decode the JWT, look up the user in the database, and return
        the User ORM instance. Raises HTTP 401 on any failure.
    """
    jwt_secret = request.app.state.jwt_secret
    try:
        return _get_current_user(token, jwt_secret, session)
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error))
```

Dependencies are tested implicitly through router endpoint tests in Tasks 3-4.

- [ ] **Step 2: Commit**

```bash
git add sophia/app/dependencies.py
git commit -m "feat(phase11): add FastAPI dependencies (db session + auth)"
```

---

### Task 3: Auth Router + Tests

**Files:**
- Create: `sophia/app/routers/auth.py`
- Create: `tests/conftest.py`
- Create: `tests/test_app_auth.py`

- [ ] **Step 1: Create shared test fixtures**

Create `tests/conftest.py`:

```python
"""
Shared test fixtures for SophiaAI endpoint tests.

Executive Brief:
    Builds a lightweight FastAPI test app with in-memory SQLite,
    no heavy AI objects, and a known JWT secret. Every endpoint
    test file imports these fixtures via pytest auto-discovery.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.app.schemas import TokenResponse
from sophia.db.database import Base, build_engine, build_session_factory

TEST_JWT_SECRET = "test-secret-for-sophia-phase-11"


@pytest.fixture()
def test_app():
    """Create a FastAPI app with in-memory SQLite and no AI objects."""
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = build_session_factory(engine)

    app = FastAPI()
    app.state.session_factory = session_factory
    app.state.jwt_secret = TEST_JWT_SECRET

    from sophia.app.routers import auth, chat, pages
    app.include_router(auth.router)
    app.include_router(chat.router)
    app.include_router(pages.router)

    yield app

    engine.dispose()


@pytest.fixture()
def client(test_app):
    """TestClient bound to the test app."""
    with TestClient(test_app) as c:
        yield c


def register_and_get_token(client: TestClient, email: str = "test@sophia.ai", password: str = "wisdom123") -> str:
    """Helper: register a user and return the access token."""
    response = client.post("/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201
    return response.json()["access_token"]
```

- [ ] **Step 2: Write failing auth endpoint tests**

Create `tests/test_app_auth.py`:

```python
"""
Endpoint tests for POST /auth/register and POST /auth/login.

Strategy: use TestClient + in-memory SQLite. No mocks needed —
auth endpoints only touch the database and crypto modules.

Run: pytest tests/test_app_auth.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.conftest import register_and_get_token


def test_register_new_user(client):
    """POST /auth/register creates a user and returns a JWT."""
    response = client.post(
        "/auth/register",
        json={"email": "new@sophia.ai", "password": "cosmos123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client):
    """POST /auth/register with an existing email returns 409."""
    client.post("/auth/register", json={"email": "dup@sophia.ai", "password": "pass1"})
    response = client.post(
        "/auth/register",
        json={"email": "dup@sophia.ai", "password": "pass2"},
    )
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"].lower()


def test_register_invalid_email(client):
    """POST /auth/register with a bad email returns 422."""
    response = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "pass"},
    )
    assert response.status_code == 422


def test_login_valid_credentials(client):
    """POST /auth/login with correct credentials returns a JWT."""
    register_and_get_token(client, "login@sophia.ai", "mypassword")
    response = client.post(
        "/auth/login",
        json={"email": "login@sophia.ai", "password": "mypassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    """POST /auth/login with wrong password returns 401."""
    register_and_get_token(client, "wrong@sophia.ai", "rightpass")
    response = client.post(
        "/auth/login",
        json={"email": "wrong@sophia.ai", "password": "wrongpass"},
    )
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


def test_login_nonexistent_user(client):
    """POST /auth/login with unknown email returns 401."""
    response = client.post(
        "/auth/login",
        json={"email": "ghost@sophia.ai", "password": "pass"},
    )
    assert response.status_code == 401
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_app_auth.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sophia.app.routers.auth'`

- [ ] **Step 4: Write the auth router**

Create `sophia/app/routers/auth.py`:

```python
"""
Authentication endpoints for SophiaAI.

Executive Brief:
    POST /auth/register — create a new user, return a JWT.
    POST /auth/login    — verify credentials, return a JWT.
    No session cookies, no OAuth flows — pure token exchange.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from sophia.app.dependencies import get_db_session
from sophia.app.schemas import LoginRequest, RegisterRequest, TokenResponse
from sophia.auth.security import create_access_token, hash_password, verify_password
from sophia.db.service import create_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(
    body: RegisterRequest,
    request: Request,
    session: Session = Depends(get_db_session),
) -> TokenResponse:
    """
    Executive Brief:
        Register a new user. Hash the password, store in DB,
        return a JWT so the user is immediately logged in.
    """
    existing_user = get_user_by_email(session, body.email)
    if existing_user is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed = hash_password(body.password)
    user = create_user(session, body.email, hashed)

    jwt_secret = request.app.state.jwt_secret
    token = create_access_token(subject=user.email, secret_key=jwt_secret)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    request: Request,
    session: Session = Depends(get_db_session),
) -> TokenResponse:
    """
    Executive Brief:
        Authenticate an existing user. Verify password against the
        stored hash, return a JWT on success.
    """
    user = get_user_by_email(session, body.email)
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    jwt_secret = request.app.state.jwt_secret
    token = create_access_token(subject=user.email, secret_key=jwt_secret)
    return TokenResponse(access_token=token)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_app_auth.py -v`
Expected: 6 PASSED

- [ ] **Step 6: Commit**

```bash
git add tests/conftest.py tests/test_app_auth.py sophia/app/routers/auth.py
git commit -m "feat(phase11): add auth router (register + login) with 6 endpoint tests"
```

---

### Task 4: Chat Router + Tests

**Files:**
- Create: `sophia/app/routers/chat.py`
- Create: `tests/test_app_chat.py`

- [ ] **Step 1: Write failing chat endpoint tests**

Create `tests/test_app_chat.py`:

```python
"""
Endpoint tests for chat and conversation APIs.

Strategy: mock the Sophia orchestrator so tests never touch FAISS,
embedding models, or the Groq API. Only the HTTP layer and DB
service are exercised.

Run: pytest tests/test_app_chat.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.core.orchestrator import SophiaResponse
from tests.conftest import register_and_get_token


class MockSophia:
    """Fake orchestrator that returns a fixed response without AI calls."""

    def ask(self, query, conversation_history=None):
        return SophiaResponse(
            answer=f"Mocked wisdom about: {query}",
            chunks=[],
            web_results=[],
            search_mode="corpus",
        )


@pytest.fixture()
def auth_client(test_app, client):
    """Client with a mock Sophia and a pre-registered user token."""
    test_app.state.sophia = MockSophia()
    token = register_and_get_token(client)
    return client, token


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_chat_new_conversation(auth_client):
    """POST /api/chat without conversation_id creates a new conversation."""
    client, token = auth_client
    response = client.post(
        "/api/chat",
        json={"message": "What is love?"},
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    data = response.json()
    assert "Mocked wisdom" in data["answer"]
    assert data["conversation_id"] >= 1
    assert data["search_mode"] == "corpus"


def test_chat_existing_conversation(auth_client):
    """POST /api/chat with a valid conversation_id appends to that conversation."""
    client, token = auth_client
    headers = _auth_header(token)

    first = client.post("/api/chat", json={"message": "First"}, headers=headers)
    conversation_id = first.json()["conversation_id"]

    second = client.post(
        "/api/chat",
        json={"message": "Second", "conversation_id": conversation_id},
        headers=headers,
    )
    assert second.status_code == 200
    assert second.json()["conversation_id"] == conversation_id


def test_chat_unauthorized(client):
    """POST /api/chat without a token returns 401."""
    response = client.post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 401


def test_list_conversations(auth_client):
    """GET /api/conversations returns the user's conversation list."""
    client, token = auth_client
    headers = _auth_header(token)

    client.post("/api/chat", json={"message": "First chat"}, headers=headers)
    client.post("/api/chat", json={"message": "Second chat"}, headers=headers)

    response = client.get("/api/conversations", headers=headers)
    assert response.status_code == 200
    conversations = response.json()
    assert len(conversations) == 2
    assert "id" in conversations[0]
    assert "title" in conversations[0]


def test_get_conversation_detail(auth_client):
    """GET /api/conversations/{id} returns messages for that conversation."""
    client, token = auth_client
    headers = _auth_header(token)

    chat_resp = client.post("/api/chat", json={"message": "Hello Sophia"}, headers=headers)
    conversation_id = chat_resp.json()["conversation_id"]

    response = client.get(f"/api/conversations/{conversation_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conversation_id
    assert len(data["messages"]) == 2
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][1]["role"] == "sophia"


def test_get_conversation_not_found(auth_client):
    """GET /api/conversations/999 returns 404 for a nonexistent conversation."""
    client, token = auth_client
    response = client.get("/api/conversations/999", headers=_auth_header(token))
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_app_chat.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sophia.app.routers.chat'`

- [ ] **Step 3: Write the chat router**

Create `sophia/app/routers/chat.py`:

```python
"""
Chat and conversation endpoints for SophiaAI.

Executive Brief:
    POST /api/chat                     — Send a message, get Sophia's response.
    GET  /api/conversations            — List the user's conversations.
    GET  /api/conversations/{id}       — Get a single conversation with messages.

    All endpoints require a valid JWT in the Authorization header.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from sophia.app.dependencies import get_authenticated_user, get_db_session
from sophia.app.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationSummary,
    MessageOut,
    SourceOut,
)
from sophia.db.models import User
from sophia.db.service import (
    add_message,
    create_conversation,
    get_conversation_with_messages,
    get_conversations_for_user,
)

router = APIRouter(tags=["chat"])


@router.post("/api/chat", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    request: Request,
    user: User = Depends(get_authenticated_user),
    session: Session = Depends(get_db_session),
) -> ChatResponse:
    """
    Executive Brief:
        Receive a user message, pass it to the Sophia orchestrator,
        persist both the question and the answer, return the response.
    """
    sophia = request.app.state.sophia

    if body.conversation_id is not None:
        conversation = get_conversation_with_messages(session, body.conversation_id)
        if conversation is None or conversation.user_id != user.id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation.messages
        ]
    else:
        conversation = create_conversation(session, user.id)
        history = None

    add_message(session, conversation.id, "user", body.message)

    response = sophia.ask(body.message, conversation_history=history)

    sources_data = [
        {"text": c.text[:200], "source_file": c.source_file, "pillar": c.pillar, "score": c.score}
        for c in response.chunks
    ]
    sources_json = json.dumps(sources_data) if sources_data else None
    add_message(session, conversation.id, "sophia", response.answer, sources_json)

    return ChatResponse(
        answer=response.answer,
        sources=[
            SourceOut(text=c.text[:200], source_file=c.source_file, pillar=c.pillar, score=c.score)
            for c in response.chunks
        ],
        conversation_id=conversation.id,
        search_mode=response.search_mode,
    )


@router.get("/api/conversations", response_model=list[ConversationSummary])
def list_conversations(
    user: User = Depends(get_authenticated_user),
    session: Session = Depends(get_db_session),
) -> list[ConversationSummary]:
    """
    Executive Brief:
        Return all conversations belonging to the authenticated user,
        newest first. No messages included — use the detail endpoint for that.
    """
    conversations = get_conversations_for_user(session, user.id)
    return [
        ConversationSummary(
            id=c.id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in conversations
    ]


@router.get("/api/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int,
    user: User = Depends(get_authenticated_user),
    session: Session = Depends(get_db_session),
) -> ConversationDetail:
    """
    Executive Brief:
        Return a single conversation with all its messages. Returns 404
        if the conversation does not exist or belongs to a different user.
    """
    conversation = get_conversation_with_messages(session, conversation_id)
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        messages=[
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                sources_json=m.sources_json,
                created_at=m.created_at,
            )
            for m in conversation.messages
        ],
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_app_chat.py -v`
Expected: 6 PASSED

- [ ] **Step 5: Commit**

```bash
git add sophia/app/routers/chat.py tests/test_app_chat.py
git commit -m "feat(phase11): add chat router (chat + conversations) with 6 endpoint tests"
```

---

### Task 5: Pages Router + Tests

**Files:**
- Create: `sophia/app/routers/pages.py`
- Create: `tests/test_app_pages.py`

- [ ] **Step 1: Write failing page tests**

Create `tests/test_app_pages.py`:

```python
"""
Endpoint tests for HTML page routes.

Strategy: verify each page route returns 200 with HTML content.
Pages are placeholder stubs — Phase 12 replaces them with Jinja2 templates.

Run: pytest tests/test_app_pages.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_landing_page(client):
    """GET / returns 200 with HTML containing 'SophiaAI'."""
    response = client.get("/")
    assert response.status_code == 200
    assert "SophiaAI" in response.text


def test_chat_page(client):
    """GET /chat returns 200 with HTML."""
    response = client.get("/chat")
    assert response.status_code == 200
    assert "Chat" in response.text


def test_login_page(client):
    """GET /login returns 200 with HTML."""
    response = client.get("/login")
    assert response.status_code == 200
    assert "Login" in response.text


def test_register_page(client):
    """GET /register returns 200 with HTML."""
    response = client.get("/register")
    assert response.status_code == 200
    assert "Register" in response.text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_app_pages.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sophia.app.routers.pages'`

- [ ] **Step 3: Write the pages router**

Create `sophia/app/routers/pages.py`:

```python
"""
HTML page routes for SophiaAI.

Executive Brief:
    Placeholder pages that return minimal HTML. Phase 12 replaces
    these with proper Jinja2 templates, static assets, and a real
    chat UI. These stubs exist so the route structure is wired and
    testable now.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
def landing_page() -> HTMLResponse:
    """Serve the landing page."""
    return HTMLResponse(
        "<html><body>"
        "<h1>SophiaAI</h1>"
        "<p>A bridge between the Divine and Technology.</p>"
        "<p><a href='/login'>Login</a> | <a href='/register'>Register</a></p>"
        "</body></html>"
    )


@router.get("/chat", response_class=HTMLResponse)
def chat_page() -> HTMLResponse:
    """Serve the chat page."""
    return HTMLResponse(
        "<html><body>"
        "<h1>Chat with Sophia</h1>"
        "<p>The conversation UI will arrive in Phase 12.</p>"
        "</body></html>"
    )


@router.get("/login", response_class=HTMLResponse)
def login_page() -> HTMLResponse:
    """Serve the login page."""
    return HTMLResponse(
        "<html><body>"
        "<h1>Login</h1>"
        "<p>The login form will arrive in Phase 12.</p>"
        "</body></html>"
    )


@router.get("/register", response_class=HTMLResponse)
def register_page() -> HTMLResponse:
    """Serve the register page."""
    return HTMLResponse(
        "<html><body>"
        "<h1>Register</h1>"
        "<p>The registration form will arrive in Phase 12.</p>"
        "</body></html>"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_app_pages.py -v`
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add sophia/app/routers/pages.py tests/test_app_pages.py
git commit -m "feat(phase11): add pages router with placeholder HTML and 4 tests"
```

---

### Task 6: App Main + Lifespan + .env Update

**Files:**
- Create: `sophia/app/main.py`
- Modify: `.env.example`

- [ ] **Step 1: Write the app factory and lifespan**

Create `sophia/app/main.py`:

```python
"""
FastAPI application entry point for SophiaAI.

Executive Brief:
    create_app() builds the FastAPI instance: mounts routers, adds CORS
    middleware, and binds the lifespan context manager. The lifespan
    initializes all heavy objects once at startup — database engine,
    session factory, SophiaRetriever (FAISS + embedding model),
    GroqClient, and the Sophia orchestrator — and stores them on
    app.state so every request shares them.

Run:
    uvicorn sophia.app.main:app --reload
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sophia.db.database import Base, build_engine, build_session_factory

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sophia.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Executive Brief:
        Startup: create DB engine, create tables, build session factory,
        load AI objects (retriever, LLM client, orchestrator).
        Shutdown: dispose the engine.
    """
    logger.info("SophiaAI starting up ...")

    database_url = os.environ.get("DATABASE_URL", "sqlite:///./sophia_memory.db")
    engine = build_engine(database_url)
    Base.metadata.create_all(bind=engine)
    app.state.session_factory = build_session_factory(engine)
    app.state.jwt_secret = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")

    from sophia.core import Sophia
    from sophia.llm import GroqClient
    from sophia.rag import SophiaRetriever

    retriever = SophiaRetriever()
    llm_client = GroqClient()
    app.state.sophia = Sophia(retriever=retriever, llm_client=llm_client)

    logger.info("SophiaAI ready. Listening for requests.")
    yield

    engine.dispose()
    logger.info("SophiaAI shut down.")


def create_app() -> FastAPI:
    """
    Executive Brief:
        Factory that assembles the FastAPI application.
        Registers routers, adds CORS middleware, binds the lifespan.
    """
    application = FastAPI(
        title="SophiaAI",
        description="A bridge between the Divine and Technology.",
        version="0.11.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from sophia.app.routers import auth, chat, pages
    application.include_router(auth.router)
    application.include_router(chat.router)
    application.include_router(pages.router)

    return application


app = create_app()
```

- [ ] **Step 2: Update .env.example**

Add `JWT_SECRET` and `DATABASE_URL` to `.env.example`:

```
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
JWT_SECRET=change-me-to-a-random-secret
DATABASE_URL=sqlite:///./sophia_memory.db
```

- [ ] **Step 3: Run the full test suite**

Run: `pytest tests/ -v`
Expected: All previous tests (116) plus new tests (27) = ~143 PASSED.
The new tests are: 11 schema + 6 auth + 6 chat + 4 pages = 27.

If any prior tests break, investigate and fix before proceeding.

- [ ] **Step 4: Verify the app starts locally (manual smoke test)**

Run: `uvicorn sophia.app.main:app --reload`

This requires a `.env` file with a valid `GROQ_API_KEY` and the FAISS index built. If those are present, the app should start and log:
```
SophiaAI starting up ...
SophiaRetriever ready. ntotal=1422 | d=384 | ...
GroqClient initialized. Default model: llama-3.1-8b-instant
Sophia initialized. Confidence threshold: 0.45
SophiaAI ready. Listening for requests.
```

Visit `http://127.0.0.1:8000/` — should see the placeholder landing page.
Visit `http://127.0.0.1:8000/docs` — should see the OpenAPI documentation with all endpoints.

- [ ] **Step 5: Commit**

```bash
git add sophia/app/main.py .env.example
git commit -m "feat(phase11): add app main with lifespan, CORS, and router wiring"
```

---

### Task 7: Final Verification + Phase Commit

- [ ] **Step 1: Run full test suite one final time**

Run: `pytest tests/ -v --tb=short`
Expected: All tests PASSED (prior 116 + new 27 = ~143).

- [ ] **Step 2: Update cosmos_log.md**

Append a Phase 11 entry to `cosmos_log.md` documenting:
- What was built: FastAPI skeleton with 3 routers, 6 endpoints, Pydantic schemas, dependency injection, app lifespan
- Artifacts: `sophia/app/` package (7 files), 4 test files, 27 new tests
- School requirement satisfied: #3 (framework)
- Key decisions: lifespan for heavy object init, yield-based DB sessions, OAuth2PasswordBearer for token extraction, test app with in-memory SQLite + mock Sophia
- Next step: Phase 12 (Templates and Chat UI)

- [ ] **Step 3: Final commit**

```bash
git add cosmos_log.md
git commit -m "docs(phase11): update cosmos_log with Phase 11 narrative"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] `sophia/app/main.py` with FastAPI instance and lifespan — Task 6
- [x] `sophia/app/routers/auth.py` — POST /register, POST /login — Task 3
- [x] `sophia/app/routers/chat.py` — POST /api/chat, GET /api/conversations, GET /api/conversations/{id} — Task 4
- [x] `sophia/app/routers/pages.py` — GET /, GET /chat, GET /login, GET /register — Task 5
- [x] Lifespan initializes Retriever, GroqClient, Sophia on app.state — Task 6
- [x] CORS middleware — Task 6
- [x] Pydantic schemas for all request/response bodies — Task 1
- [x] FastAPI dependencies (DB session + auth) — Task 2
- [x] TDD with endpoint tests — Tasks 1, 3, 4, 5
- [x] .env.example updated with JWT_SECRET — Task 6

**Placeholder scan:** No TBD, TODO, or "implement later" found.

**Type consistency:**
- `RegisterRequest`, `LoginRequest`, `TokenResponse` — used identically in schemas.py, auth router, and tests
- `ChatRequest`, `ChatResponse`, `SourceOut` — used identically in schemas.py, chat router, and tests
- `ConversationSummary`, `ConversationDetail`, `MessageOut` — used identically in schemas.py, chat router, and tests
- `get_db_session`, `get_authenticated_user` — defined in dependencies.py, consumed by auth.py and chat.py with matching signatures
- `SophiaResponse` — imported from `sophia.core.orchestrator`, used in MockSophia in tests
