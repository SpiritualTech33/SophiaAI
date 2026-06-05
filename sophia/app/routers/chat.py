"""
Chat and conversation endpoints for SophiaAI.

Executive Brief:
    POST /api/chat                     — Send a message, get Sophia's response.
    GET  /api/conversations            — List the user's conversations.
    GET  /api/conversations/{id}       — Get a single conversation with messages.
    PATCH  /api/conversations/{id}     — Rename a conversation.
    DELETE /api/conversations/{id}     — Delete a conversation and its messages.

    All endpoints require a valid JWT in the Authorization header.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from sophia.app.dependencies import get_authenticated_user, get_db_session
from sophia.llm import SophiaLLMError
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
    delete_conversation,
    get_conversation_with_messages,
    get_conversations_for_user,
    get_files_text,
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

    attachments = get_files_text(session, body.attached_file_ids, user.id)
    response = sophia.ask(
        body.message, conversation_history=history, attachments=attachments
    )

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


def _sse_frame(event: str, data: dict) -> str:
    """Serialize one Server-Sent Event frame. data is always JSON-encoded so
    answer tokens with newlines or quotes survive transport intact."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/api/chat/stream")
def chat_stream(
    body: ChatRequest,
    request: Request,
    user: User = Depends(get_authenticated_user),
    session: Session = Depends(get_db_session),
) -> StreamingResponse:
    """
    Executive Brief:
        The streaming twin of /api/chat. Resolves the conversation and saves
        the user message up front, then streams the answer as Server-Sent
        Events: a `meta` frame (search_mode + web_results + conversation_id),
        then `token` frames, then `done`. On a mid-stream LLM failure it emits
        an `error` frame and persists no broken answer.

    Mental Model:
        The request-scoped session creates the conversation and saves the user
        message (committed before streaming starts). The sophia message is
        written from a fresh session opened inside the generator, because the
        generator runs while the response streams — after the request-scoped
        session would otherwise be torn down.
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
    conversation_id = conversation.id

    attachments = get_files_text(session, body.attached_file_ids, user.id)
    stream = sophia.ask_stream(
        body.message, conversation_history=history, attachments=attachments
    )
    session_factory = request.app.state.session_factory

    # Corpus citations are known up front (chunks are retrieved before the LLM
    # runs), so they ride in the meta frame to light the Mind panel and source
    # chips immediately, and are persisted with the answer once streaming ends.
    sources_data = [
        {"text": c.text[:200], "source_file": c.source_file,
         "pillar": c.pillar, "score": c.score}
        for c in stream.chunks
    ]
    sources_json = json.dumps(sources_data) if sources_data else None

    def event_generator():
        web_results = [
            {"title": r.title, "url": r.url, "snippet": r.snippet}
            for r in stream.web_results
        ]
        yield _sse_frame("meta", {
            "search_mode": stream.search_mode,
            "web_results": web_results,
            "sources": sources_data,
            "conversation_id": conversation_id,
        })

        buffer: list[str] = []
        try:
            for token in stream.tokens:
                buffer.append(token)
                yield _sse_frame("token", {"text": token})
        except SophiaLLMError:
            yield _sse_frame("error", {
                "message": "Sophia could not complete her answer. Please try again.",
            })
            return

        answer = "".join(buffer)

        write_session = session_factory()
        try:
            add_message(write_session, conversation_id, "sophia", answer, sources_json)
        finally:
            write_session.close()

        yield _sse_frame("done", {})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


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


@router.delete("/api/conversations/{conversation_id}", status_code=204)
def delete_conversation_endpoint(
    conversation_id: int,
    user: User = Depends(get_authenticated_user),
    session: Session = Depends(get_db_session),
) -> Response:
    """
    Executive Brief:
        Delete one of the user's conversations and all its messages.
        Returns 204 on success, 404 if it does not exist or belongs to a
        different user.
    """
    conversation = get_conversation_with_messages(session, conversation_id)
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    delete_conversation(session, conversation_id)
    return Response(status_code=204)


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
