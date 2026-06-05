"""
Endpoint tests for the streaming chat API (POST /api/chat/stream).

Strategy: mock the Sophia orchestrator's ask_stream so tests never touch
FAISS, embedding models, or the Groq API. Only the SSE layer and DB
persistence are exercised. TestClient buffers the streamed body, so the
full SSE text is available on response.text.

Run: pytest tests/test_app_chat_stream.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.core.orchestrator import StreamingSophiaResponse
from sophia.llm import SophiaLLMError
from sophia.rag.retriever import Chunk
from sophia.tools.web_search import SearchResult
from tests.conftest import register_and_get_token


class MockStreamSophia:
    """Fake orchestrator exposing ask_stream without any AI calls."""

    def __init__(self, tokens=("Hello ", "world."), search_mode="corpus",
                 web_results=None, chunks=None, raise_midstream=False):
        self._tokens = tokens
        self._search_mode = search_mode
        self._web_results = web_results or []
        self._chunks = chunks or []
        self._raise_midstream = raise_midstream

    def ask_stream(self, query, conversation_history=None, attachments=None):
        tokens = self._tokens
        raise_midstream = self._raise_midstream

        def gen():
            yield tokens[0]
            if raise_midstream:
                raise SophiaLLMError("Groq exploded mid-stream")
            for t in tokens[1:]:
                yield t

        return StreamingSophiaResponse(
            tokens=gen(),
            chunks=self._chunks,
            web_results=self._web_results,
            search_mode=self._search_mode,
        )


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _parse_sse(text: str):
    """Parse an SSE payload into a list of (event, data_dict) tuples."""
    frames = []
    for block in text.strip().split("\n\n"):
        if not block.strip():
            continue
        event = None
        data = None
        for line in block.splitlines():
            if line.startswith("event:"):
                event = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data = json.loads(line[len("data:"):].strip())
        frames.append((event, data))
    return frames


@pytest.fixture()
def stream_client(test_app, client):
    """Client with a streaming mock Sophia and a registered user token."""
    test_app.state.sophia = MockStreamSophia()
    token = register_and_get_token(client)
    return client, token


def test_stream_emits_meta_tokens_done_in_order(stream_client):
    """The SSE stream is meta first, then token(s), then done."""
    client, token = stream_client
    response = client.post(
        "/api/chat/stream",
        json={"message": "What is wisdom?"},
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    frames = _parse_sse(response.text)
    events = [e for e, _ in frames]

    assert events[0] == "meta"
    assert events[-1] == "done"
    assert "token" in events
    # meta precedes every token
    assert events.index("meta") < events.index("token")


def test_stream_meta_carries_mode_and_conversation_id(stream_client):
    """The meta frame includes search_mode and conversation_id."""
    client, token = stream_client
    response = client.post(
        "/api/chat/stream",
        json={"message": "Hello"},
        headers=_auth_header(token),
    )
    frames = _parse_sse(response.text)
    meta = next(data for event, data in frames if event == "meta")

    assert meta["search_mode"] == "corpus"
    assert meta["conversation_id"] >= 1
    assert meta["web_results"] == []


def test_stream_tokens_reconstruct_the_answer(stream_client):
    """Concatenated token frames equal the full answer."""
    client, token = stream_client
    response = client.post(
        "/api/chat/stream",
        json={"message": "Hi"},
        headers=_auth_header(token),
    )
    frames = _parse_sse(response.text)
    answer = "".join(data["text"] for event, data in frames if event == "token")
    assert answer == "Hello world."


def test_stream_persists_both_messages(stream_client):
    """After streaming, the conversation holds the user + sophia messages."""
    client, token = stream_client
    response = client.post(
        "/api/chat/stream",
        json={"message": "What is love?"},
        headers=_auth_header(token),
    )
    frames = _parse_sse(response.text)
    meta = next(data for event, data in frames if event == "meta")
    conversation_id = meta["conversation_id"]

    detail = client.get(
        f"/api/conversations/{conversation_id}", headers=_auth_header(token)
    ).json()
    assert len(detail["messages"]) == 2
    assert detail["messages"][0]["role"] == "user"
    assert detail["messages"][1]["role"] == "sophia"
    assert detail["messages"][1]["content"] == "Hello world."


def test_stream_web_results_surface_in_meta(test_app, client):
    """When the orchestrator returns web_results, they ride in the meta frame."""
    web = [SearchResult(title="A Web Page", url="https://example.com", snippet="snip")]
    test_app.state.sophia = MockStreamSophia(search_mode="hybrid", web_results=web)
    token = register_and_get_token(client)

    response = client.post(
        "/api/chat/stream",
        json={"message": "obscure question"},
        headers=_auth_header(token),
    )
    frames = _parse_sse(response.text)
    meta = next(data for event, data in frames if event == "meta")

    assert meta["search_mode"] == "hybrid"
    assert len(meta["web_results"]) == 1
    assert meta["web_results"][0]["url"] == "https://example.com"
    assert meta["web_results"][0]["title"] == "A Web Page"


def test_stream_corpus_sources_surface_in_meta(test_app, client):
    """Corpus citations ride in the meta frame so the Mind panel lights up."""
    chunks = [
        Chunk(text="The Tao is the way.", source_file="data/sophia_engine/philosophy/tao.md",
              pillar="philosophy", chunk_id="c1", score=0.81),
    ]
    test_app.state.sophia = MockStreamSophia(chunks=chunks)
    token = register_and_get_token(client)

    response = client.post(
        "/api/chat/stream",
        json={"message": "What is the Tao?"},
        headers=_auth_header(token),
    )
    frames = _parse_sse(response.text)
    meta = next(data for event, data in frames if event == "meta")

    assert len(meta["sources"]) == 1
    assert meta["sources"][0]["source_file"] == "data/sophia_engine/philosophy/tao.md"
    assert meta["sources"][0]["pillar"] == "philosophy"


def test_stream_midstream_error_emits_error_and_skips_persist(test_app, client):
    """A Groq failure mid-stream emits an error frame and saves no sophia message."""
    test_app.state.sophia = MockStreamSophia(raise_midstream=True)
    token = register_and_get_token(client)

    response = client.post(
        "/api/chat/stream",
        json={"message": "trigger failure"},
        headers=_auth_header(token),
    )
    frames = _parse_sse(response.text)
    events = [e for e, _ in frames]
    meta = next(data for event, data in frames if event == "meta")

    assert "error" in events
    assert "done" not in events

    detail = client.get(
        f"/api/conversations/{meta['conversation_id']}", headers=_auth_header(token)
    ).json()
    # Only the user message survives; no broken sophia message persisted.
    assert len(detail["messages"]) == 1
    assert detail["messages"][0]["role"] == "user"


def test_stream_requires_authentication(client):
    """POST /api/chat/stream without a token returns 401."""
    response = client.post("/api/chat/stream", json={"message": "Hello"})
    assert response.status_code == 401
