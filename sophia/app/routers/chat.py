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
    ConversationRenameRequest,
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
    update_conversation_title,
)

router = APIRouter(tags=["chat"])

_MAX_TITLE_LENGTH = 42


def _title_from_message(message: str) -> str:
    """
    Executive Brief:
        Derive a conversation title from its first user message: a single,
        trimmed line capped at _MAX_TITLE_LENGTH characters, with an ellipsis
        when truncated. Falls back to "New Conversation" for an empty message.
    """
    cleaned = " ".join(message.split())
    if not cleaned:
        return "New Conversation"
    if len(cleaned) <= _MAX_TITLE_LENGTH:
        return cleaned
    return cleaned[:_MAX_TITLE_LENGTH].rstrip() + "…"


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
        conversation = create_conversation(
            session, user.id, title=_title_from_message(body.message)
        )
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


@router.patch("/api/conversations/{conversation_id}", response_model=ConversationSummary)
def rename_conversation(
    conversation_id: int,
    body: ConversationRenameRequest,
    user: User = Depends(get_authenticated_user),
    session: Session = Depends(get_db_session),
) -> ConversationSummary:
    """
    Executive Brief:
        Rename one of the user's conversations. Returns 404 if it does not
        exist or belongs to a different user, 422 if the title is blank.
    """
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Title cannot be empty")

    conversation = get_conversation_with_messages(session, conversation_id)
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    updated = update_conversation_title(session, conversation_id, title[:_MAX_TITLE_LENGTH])
    return ConversationSummary(
        id=updated.id,
        title=updated.title,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


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
