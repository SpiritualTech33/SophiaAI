# tests/test_web_search.py
"""
Unit tests for sophia.tools.web_search.

Strategy: mock duckduckgo_search.DDGS so tests never hit the network.
Each test verifies one behavior of web_search(), SearchResult, or
SophiaSearchError.

Run: pytest tests/test_web_search.py -v
"""

from __future__ import annotations

import sys
from dataclasses import fields
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.tools import SearchResult, SophiaSearchError, web_search


# ---------------------------------------------------------------------------
# SearchResult dataclass
# ---------------------------------------------------------------------------

def test_search_result_has_required_fields():
    """SearchResult has exactly three fields: title, url, snippet."""
    field_names = {f.name for f in fields(SearchResult)}
    assert field_names == {"title", "url", "snippet"}


def test_search_result_stores_values():
    """SearchResult holds the values passed at construction."""
    result = SearchResult(
        title="Lao Tzu",
        url="https://example.com/laotzu",
        snippet="The Tao that can be told is not the eternal Tao.",
    )
    assert result.title == "Lao Tzu"
    assert result.url == "https://example.com/laotzu"
    assert result.snippet == "The Tao that can be told is not the eternal Tao."


# ---------------------------------------------------------------------------
# SophiaSearchError
# ---------------------------------------------------------------------------

def test_sophia_search_error_is_exception():
    """SophiaSearchError inherits from Exception and carries a message."""
    error = SophiaSearchError("network down")
    assert isinstance(error, Exception)
    assert str(error) == "network down"


def test_sophia_search_error_preserves_cause():
    """SophiaSearchError can chain an original exception via __cause__."""
    original = ConnectionError("timeout")
    error = SophiaSearchError("search failed")
    error.__cause__ = original
    assert error.__cause__ is original


# ---------------------------------------------------------------------------
# web_search — input validation
# ---------------------------------------------------------------------------

def test_web_search_raises_on_empty_query():
    """Empty string query -> ValueError."""
    with pytest.raises(ValueError, match="query"):
        web_search(query="")


def test_web_search_raises_on_whitespace_query():
    """Whitespace-only query -> ValueError."""
    with pytest.raises(ValueError, match="query"):
        web_search(query="   ")


# ---------------------------------------------------------------------------
# web_search — happy path
# ---------------------------------------------------------------------------

@patch("sophia.tools.web_search.DDGS")
def test_web_search_returns_list_of_search_results(mock_ddgs_class):
    """Successful search -> list of SearchResult dataclasses."""
    mock_instance = MagicMock()
    mock_instance.text.return_value = [
        {
            "title": "Wisdom of Lao Tzu",
            "href": "https://example.com/laotzu",
            "body": "The journey of a thousand miles begins with a single step.",
        },
        {
            "title": "Stoic Philosophy",
            "href": "https://example.com/stoic",
            "body": "We suffer more in imagination than in reality.",
        },
    ]
    mock_ddgs_class.return_value = mock_instance

    results = web_search(query="ancient wisdom")

    assert len(results) == 2
    assert all(isinstance(r, SearchResult) for r in results)
    assert results[0].title == "Wisdom of Lao Tzu"
    assert results[0].url == "https://example.com/laotzu"
    assert results[0].snippet == "The journey of a thousand miles begins with a single step."
    assert results[1].title == "Stoic Philosophy"


@patch("sophia.tools.web_search.DDGS")
def test_web_search_uses_default_max_results(mock_ddgs_class):
    """When no max_results given, passes 5 to DDGS().text()."""
    mock_instance = MagicMock()
    mock_instance.text.return_value = []
    mock_ddgs_class.return_value = mock_instance

    web_search(query="test query")

    mock_instance.text.assert_called_once_with("test query", max_results=5)


@patch("sophia.tools.web_search.DDGS")
def test_web_search_uses_custom_max_results(mock_ddgs_class):
    """Explicit max_results overrides default."""
    mock_instance = MagicMock()
    mock_instance.text.return_value = []
    mock_ddgs_class.return_value = mock_instance

    web_search(query="test query", max_results=3)

    mock_instance.text.assert_called_once_with("test query", max_results=3)


@patch("sophia.tools.web_search.DDGS")
def test_web_search_returns_empty_list_when_no_results(mock_ddgs_class):
    """DDGS returns empty list -> web_search returns empty list, no error."""
    mock_instance = MagicMock()
    mock_instance.text.return_value = []
    mock_ddgs_class.return_value = mock_instance

    results = web_search(query="xyznonexistent")

    assert results == []
    assert isinstance(results, list)


@patch("sophia.tools.web_search.DDGS")
def test_web_search_skips_malformed_results(mock_ddgs_class):
    """Results missing required keys are skipped, not crash the function."""
    mock_instance = MagicMock()
    mock_instance.text.return_value = [
        {"title": "Good Result", "href": "https://example.com", "body": "Valid snippet."},
        {"title": "Bad Result"},  # missing href and body
        {"href": "https://orphan.com"},  # missing title and body
    ]
    mock_ddgs_class.return_value = mock_instance

    results = web_search(query="mixed results")

    assert len(results) == 1
    assert results[0].title == "Good Result"


# ---------------------------------------------------------------------------
# web_search — error wrapping
# ---------------------------------------------------------------------------

@patch("sophia.tools.web_search.DDGS")
def test_web_search_wraps_connection_error(mock_ddgs_class):
    """Network failure -> SophiaSearchError with 'network' in message."""
    mock_instance = MagicMock()
    mock_instance.text.side_effect = ConnectionError("DNS resolution failed")
    mock_ddgs_class.return_value = mock_instance

    with pytest.raises(SophiaSearchError, match="network"):
        web_search(query="test")


@patch("sophia.tools.web_search.DDGS")
def test_web_search_wraps_timeout_error(mock_ddgs_class):
    """Timeout -> SophiaSearchError with 'timed out' in message."""
    mock_instance = MagicMock()
    mock_instance.text.side_effect = TimeoutError("request timed out")
    mock_ddgs_class.return_value = mock_instance

    with pytest.raises(SophiaSearchError, match="timed out"):
        web_search(query="test")


@patch("sophia.tools.web_search.DDGS")
def test_web_search_wraps_unexpected_exception(mock_ddgs_class):
    """Any other exception -> SophiaSearchError with original chained."""
    mock_instance = MagicMock()
    mock_instance.text.side_effect = RuntimeError("something unexpected")
    mock_ddgs_class.return_value = mock_instance

    with pytest.raises(SophiaSearchError) as exc_info:
        web_search(query="test")

    assert exc_info.value.__cause__ is not None
    assert isinstance(exc_info.value.__cause__, RuntimeError)
