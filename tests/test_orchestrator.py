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
