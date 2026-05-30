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


class ConversationRenameRequest(BaseModel):
    """Body for PATCH /api/conversations/{id}."""
    title: str


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


class CorpusDocOut(BaseModel):
    """One document in the list returned by GET /api/corpus."""
    id: str
    title: str
    author: str
    year: int | None
    words: int
    pillar: str
    path: str


class CorpusDocText(BaseModel):
    """Raw markdown of one document for GET /api/corpus/{doc_id}."""
    id: str
    title: str
    author: str
    pillar: str
    text: str
