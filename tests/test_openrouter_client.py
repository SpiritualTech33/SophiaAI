# tests/test_openrouter_client.py
"""
Unit tests for sophia.llm.openrouter_client.

Strategy: mock httpx.Client so tests run without a real API key
and never hit the network. Each test verifies one behavior of OpenRouterClient
or SophiaLLMError.

Run: pytest tests/test_openrouter_client.py -v
"""

from __future__ import annotations

import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.llm import OpenRouterClient, SophiaLLMError


# ---------------------------------------------------------------------------
# SophiaLLMError
# ---------------------------------------------------------------------------

def test_sophia_llm_error_is_exception():
    """SophiaLLMError inherits from Exception and carries a message."""
    error = SophiaLLMError("something broke")
    assert isinstance(error, Exception)
    assert str(error) == "something broke"


def test_sophia_llm_error_preserves_cause():
    """SophiaLLMError can chain an original exception via __cause__."""
    original = ConnectionError("network down")
    error = SophiaLLMError("LLM unreachable")
    error.__cause__ = original
    assert error.__cause__ is original


# ---------------------------------------------------------------------------
# OpenRouterClient.__init__
# ---------------------------------------------------------------------------

@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"})
@patch("sophia.llm.openrouter_client.httpx.Client")
def test_init_creates_client_with_api_key(mock_client_class):
    """OpenRouterClient reads OPENROUTER_API_KEY from env and instantiates client."""
    client = OpenRouterClient()
    mock_client_class.assert_called_once_with(base_url="https://openrouter.ai/api/v1", timeout=60.0)
    assert client is not None


@patch.dict("os.environ", {}, clear=True)
def test_init_raises_when_api_key_missing():
    """Missing OPENROUTER_API_KEY → SophiaLLMError with clear message."""
    with pytest.raises(SophiaLLMError, match="OPENROUTER_API_KEY"):
        OpenRouterClient()


# ---------------------------------------------------------------------------
# OpenRouterClient.chat — happy path
# ---------------------------------------------------------------------------

@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"})
@patch("sophia.llm.openrouter_client.httpx.Client")
def test_chat_returns_response_content(mock_client_class):
    """Successful API call → returns the assistant message content as str."""
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Wisdom is knowing what you do not know."
                }
            }
        ]
    }

    mock_instance = MagicMock()
    mock_instance.post.return_value = fake_response
    mock_client_class.return_value = mock_instance

    client = OpenRouterClient()
    result = client.chat(messages=[{"role": "user", "content": "What is wisdom?"}])

    assert result == "Wisdom is knowing what you do not know."
    assert isinstance(result, str)


@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"})
@patch("sophia.llm.openrouter_client.httpx.Client")
def test_chat_uses_default_model(mock_client_class):
    """When no model arg given, uses default model (e.g. google/gemini-2.5-flash)."""
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "choices": [{"message": {"content": "answer"}}]
    }

    mock_instance = MagicMock()
    mock_instance.post.return_value = fake_response
    mock_client_class.return_value = mock_instance

    client = OpenRouterClient()
    client.chat(messages=[{"role": "user", "content": "hi"}])

    call_kwargs = mock_instance.post.call_args.kwargs
    assert call_kwargs["json"]["model"] == "google/gemini-2.5-flash"


@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"})
@patch("sophia.llm.openrouter_client.httpx.Client")
def test_chat_uses_custom_model(mock_client_class):
    """Explicit model arg overrides default."""
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "choices": [{"message": {"content": "answer"}}]
    }

    mock_instance = MagicMock()
    mock_instance.post.return_value = fake_response
    mock_client_class.return_value = mock_instance

    client = OpenRouterClient()
    client.chat(
        messages=[{"role": "user", "content": "hi"}],
        model="google/gemini-2.5-pro",
    )

    call_kwargs = mock_instance.post.call_args.kwargs
    assert call_kwargs["json"]["model"] == "google/gemini-2.5-pro"


# ---------------------------------------------------------------------------
# OpenRouterClient.chat — input validation
# ---------------------------------------------------------------------------

@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"})
@patch("sophia.llm.openrouter_client.httpx.Client")
def test_chat_raises_on_empty_messages(mock_client_class):
    """Empty messages list → ValueError."""
    mock_client_class.return_value = MagicMock()
    client = OpenRouterClient()

    with pytest.raises(ValueError, match="messages"):
        client.chat(messages=[])


@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"})
@patch("sophia.llm.openrouter_client.httpx.Client")
def test_chat_raises_on_none_messages(mock_client_class):
    """None messages → ValueError."""
    mock_client_class.return_value = MagicMock()
    client = OpenRouterClient()

    with pytest.raises(ValueError, match="messages"):
        client.chat(messages=None)


# ---------------------------------------------------------------------------
# OpenRouterClient.chat — error wrapping
# ---------------------------------------------------------------------------

@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"})
@patch("sophia.llm.openrouter_client.httpx.Client")
def test_chat_wraps_api_connection_error(mock_client_class):
    """httpx.HTTPError → SophiaLLMError."""
    mock_instance = MagicMock()
    mock_instance.post.side_effect = httpx.ConnectError("network down")
    mock_client_class.return_value = mock_instance

    client = OpenRouterClient()
    with pytest.raises(SophiaLLMError, match="connection failed"):
        client.chat(messages=[{"role": "user", "content": "hi"}])


@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"})
@patch("sophia.llm.openrouter_client.httpx.Client")
def test_chat_wraps_rate_limit_error(mock_client_class):
    """HTTP 429 → SophiaLLMError with 'rate limit'."""
    fake_response = MagicMock()
    fake_response.status_code = 429

    mock_instance = MagicMock()
    mock_instance.post.return_value = fake_response
    mock_client_class.return_value = mock_instance

    client = OpenRouterClient()
    with pytest.raises(SophiaLLMError, match="rate limit"):
        client.chat(messages=[{"role": "user", "content": "hi"}])


@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"})
@patch("sophia.llm.openrouter_client.httpx.Client")
def test_chat_wraps_api_status_error(mock_client_class):
    """HTTP 500 → SophiaLLMError."""
    fake_response = MagicMock()
    fake_response.status_code = 500
    fake_response.text = "Internal server error"

    mock_instance = MagicMock()
    mock_instance.post.return_value = fake_response
    mock_client_class.return_value = mock_instance

    client = OpenRouterClient()
    with pytest.raises(SophiaLLMError, match="500"):
        client.chat(messages=[{"role": "user", "content": "hi"}])


# ---------------------------------------------------------------------------
# OpenRouterClient.chat — empty response handling
# ---------------------------------------------------------------------------

@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"})
@patch("sophia.llm.openrouter_client.httpx.Client")
def test_chat_raises_on_empty_response_content(mock_client_class):
    """API returns None content → SophiaLLMError."""
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "choices": [{"message": {"content": None}}]
    }

    mock_instance = MagicMock()
    mock_instance.post.return_value = fake_response
    mock_client_class.return_value = mock_instance

    client = OpenRouterClient()
    with pytest.raises(SophiaLLMError, match="empty"):
        client.chat(messages=[{"role": "user", "content": "hi"}])


@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"})
@patch("sophia.llm.openrouter_client.httpx.Client")
def test_chat_raises_on_no_choices(mock_client_class):
    """API returns empty choices list → SophiaLLMError."""
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "choices": []
    }

    mock_instance = MagicMock()
    mock_instance.post.return_value = fake_response
    mock_client_class.return_value = mock_instance

    client = OpenRouterClient()
    with pytest.raises(SophiaLLMError, match="empty"):
        client.chat(messages=[{"role": "user", "content": "hi"}])


# ---------------------------------------------------------------------------
# OpenRouterClient.chat_stream — streaming
# ---------------------------------------------------------------------------

@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"})
@patch("sophia.llm.openrouter_client.httpx.Client")
def test_chat_stream_yields_deltas_in_order(mock_client_class):
    """chat_stream yields each delta's content in arrival order."""
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.iter_lines.return_value = [
        "data: {\"choices\": [{\"delta\": {\"content\": \"Wisdom \"}}]}",
        "data: {\"choices\": [{\"delta\": {\"content\": \"is \"}}]}",
        "data: {\"choices\": [{\"delta\": {\"content\": \"love.\"}}]}",
        "data: [DONE]"
    ]

    mock_instance = MagicMock()
    mock_instance.stream.return_value.__enter__.return_value = fake_response
    mock_client_class.return_value = mock_instance

    client = OpenRouterClient()
    tokens = list(client.chat_stream(messages=[{"role": "user", "content": "?"}]))

    assert tokens == ["Wisdom ", "is ", "love."]


@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"})
@patch("sophia.llm.openrouter_client.httpx.Client")
def test_chat_stream_skips_none_deltas(mock_client_class):
    """A final chunk with delta.content=None (stream end) is skipped, not yielded."""
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.iter_lines.return_value = [
        "data: {\"choices\": [{\"delta\": {\"content\": \"Hello\"}}]}",
        "data: {\"choices\": [{\"delta\": {\"content\": null}}]}",
        "data: [DONE]"
    ]

    mock_instance = MagicMock()
    mock_instance.stream.return_value.__enter__.return_value = fake_response
    mock_client_class.return_value = mock_instance

    client = OpenRouterClient()
    tokens = list(client.chat_stream(messages=[{"role": "user", "content": "hi"}]))

    assert tokens == ["Hello"]


@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"})
@patch("sophia.llm.openrouter_client.httpx.Client")
def test_chat_stream_raises_on_empty_messages(mock_client_class):
    """Empty messages list → ValueError, eagerly (before any iteration)."""
    mock_client_class.return_value = MagicMock()
    client = OpenRouterClient()

    with pytest.raises(ValueError, match="messages"):
        client.chat_stream(messages=[])


@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"})
@patch("sophia.llm.openrouter_client.httpx.Client")
def test_chat_stream_wraps_rate_limit_error(mock_client_class):
    """A RateLimitError (HTTP 429) during streaming is wrapped as SophiaLLMError."""
    fake_response = MagicMock()
    fake_response.status_code = 429

    mock_instance = MagicMock()
    mock_instance.stream.return_value.__enter__.return_value = fake_response
    mock_client_class.return_value = mock_instance

    client = OpenRouterClient()
    with pytest.raises(SophiaLLMError, match="rate limit"):
        list(client.chat_stream(messages=[{"role": "user", "content": "hi"}]))


@patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"})
@patch("sophia.llm.openrouter_client.httpx.Client")
def test_chat_stream_wraps_api_status_error(mock_client_class):
    """HTTP 500 during streaming is wrapped as SophiaLLMError."""
    fake_response = MagicMock()
    fake_response.status_code = 500
    fake_response.read.return_value = b"{\"error\": {\"message\": \"server crash\"}}"

    mock_instance = MagicMock()
    mock_instance.stream.return_value.__enter__.return_value = fake_response
    mock_client_class.return_value = mock_instance

    client = OpenRouterClient()
    with pytest.raises(SophiaLLMError, match="server crash"):
        list(client.chat_stream(messages=[{"role": "user", "content": "hi"}]))


# ---------------------------------------------------------------------------
# Real-API integration test (skips if OPENROUTER_API_KEY is placeholder or not set)
# ---------------------------------------------------------------------------

import os
from dotenv import load_dotenv

load_dotenv()
_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
_HAS_API_KEY = bool(_API_KEY) and _API_KEY != "sk-or-v1-placeholder-key"


@pytest.mark.skipif(
    not _HAS_API_KEY,
    reason="OPENROUTER_API_KEY not set; skipping live API test.",
)
def test_chat_live_api_returns_nonempty_string():
    """End-to-end: real API key + real OpenRouter endpoint → non-empty response."""
    client = OpenRouterClient()
    result = client.chat(
        messages=[{"role": "user", "content": "Say hello in exactly three words."}]
    )
    assert isinstance(result, str)
    assert len(result) > 0
