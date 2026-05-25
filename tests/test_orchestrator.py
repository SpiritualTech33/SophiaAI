"""
Unit tests for sophia.core.orchestrator.

Strategy: mock SophiaRetriever, GroqClient, and web_search so tests
run without FAISS, API keys, or network access.

Run: pytest tests/test_orchestrator.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.core.orchestrator import Sophia, SophiaResponse


def test_sophia_response_holds_fields():
    """SophiaResponse stores answer, chunks, web_results, search_mode."""
    response = SophiaResponse(
        answer="Wisdom is knowing what you do not know.",
        chunks=[],
        web_results=[],
        search_mode="corpus",
    )
    assert response.answer == "Wisdom is knowing what you do not know."
    assert response.chunks == []
    assert response.web_results == []
    assert response.search_mode == "corpus"


def test_sophia_init_stores_dependencies():
    """Sophia stores retriever, llm_client, and threshold."""
    mock_retriever = MagicMock()
    mock_llm = MagicMock()

    sophia = Sophia(
        retriever=mock_retriever,
        llm_client=mock_llm,
        confidence_threshold=0.5,
    )

    assert sophia._retriever is mock_retriever
    assert sophia._llm_client is mock_llm
    assert sophia._confidence_threshold == 0.5


def test_sophia_init_default_threshold():
    """Default confidence threshold is 0.45."""
    sophia = Sophia(retriever=MagicMock(), llm_client=MagicMock())
    assert sophia._confidence_threshold == 0.45


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

from sophia.rag.retriever import Chunk


def _make_chunk(text: str, source: str, pillar: str, score: float) -> Chunk:
    """Helper to build Chunk instances for tests."""
    return Chunk(
        text=text,
        source_file=source,
        pillar=pillar,
        chunk_id="test_chunk",
        score=score,
    )


# ---------------------------------------------------------------------------
# Task 2 — Corpus-only RAG path
# ---------------------------------------------------------------------------


def test_ask_corpus_only_returns_sophia_response():
    """High-confidence retrieval -> corpus-only response with answer and chunks."""
    chunks = [
        _make_chunk("The Tao that can be told is not the eternal Tao.",
                     "data/sophia_engine/philosophy/tao_te_ching.md", "philosophy", 0.82),
        _make_chunk("Emptiness is form, form is emptiness.",
                     "data/sophia_engine/spirit/heart_sutra.md", "spirit", 0.71),
    ]

    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = chunks

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "The Tao is the way of all things."

    sophia = Sophia(retriever=mock_retriever, llm_client=mock_llm)
    response = sophia.ask("What is the Tao?")

    assert isinstance(response, SophiaResponse)
    assert response.answer == "The Tao is the way of all things."
    assert response.chunks == chunks
    assert response.web_results == []
    assert response.search_mode == "corpus"


def test_ask_corpus_only_calls_retriever_with_query():
    """ask() passes the user query to retriever.retrieve()."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        _make_chunk("passage", "file.md", "mind", 0.9),
    ]

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "answer"

    sophia = Sophia(retriever=mock_retriever, llm_client=mock_llm)
    sophia.ask("What is wisdom?")

    mock_retriever.retrieve.assert_called_once_with("What is wisdom?", top_k=5)


def test_ask_corpus_only_sends_system_and_user_messages():
    """LLM receives a system message (with passages) and a user message."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        _make_chunk("Know thyself.", "file.md", "philosophy", 0.88),
    ]

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "answer"

    sophia = Sophia(retriever=mock_retriever, llm_client=mock_llm)
    sophia.ask("Who am I?")

    call_args = mock_llm.chat.call_args
    messages = call_args.kwargs.get("messages") or call_args[0][0]

    assert len(messages) >= 2
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "Who am I?"


def test_ask_corpus_system_prompt_contains_passages():
    """System prompt includes the retrieved passage text and source."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        _make_chunk("The unexamined life is not worth living.",
                     "data/sophia_engine/philosophy/socrates.md", "philosophy", 0.91),
    ]

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "answer"

    sophia = Sophia(retriever=mock_retriever, llm_client=mock_llm)
    sophia.ask("Why examine life?")

    call_args = mock_llm.chat.call_args
    messages = call_args.kwargs.get("messages") or call_args[0][0]
    system_content = messages[0]["content"]

    assert "The unexamined life is not worth living." in system_content
    assert "socrates.md" in system_content
