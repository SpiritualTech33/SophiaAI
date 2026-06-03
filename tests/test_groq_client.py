# tests/test_groq_client.py
"""
Unit tests for sophia.llm.groq_client.

Strategy: mock the groq.Groq client so tests run without a real API key
and never hit the network. Each test verifies one behavior of GroqClient
or SophiaLLMError.

Run: pytest tests/test_groq_client.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.llm import GroqClient, SophiaLLMError


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
# GroqClient.__init__
# ---------------------------------------------------------------------------

@patch.dict("os.environ", {"GROQ_API_KEY": "test-key-123"})
@patch("sophia.llm.groq_client.Groq")
def test_init_creates_client_with_api_key(mock_groq_class):
    """GroqClient reads GROQ_API_KEY from env and passes it to Groq()."""
    client = GroqClient()
    mock_groq_class.assert_called_once_with(api_key="test-key-123")
    assert client is not None


@patch.dict("os.environ", {}, clear=True)
def test_init_raises_when_api_key_missing():
    """Missing GROQ_API_KEY → SophiaLLMError with clear message."""
    with pytest.raises(SophiaLLMError, match="GROQ_API_KEY"):
        GroqClient()


# ---------------------------------------------------------------------------
# GroqClient.chat — happy path
# ---------------------------------------------------------------------------

@patch.dict("os.environ", {"GROQ_API_KEY": "test-key-123"})
@patch("sophia.llm.groq_client.Groq")
def test_chat_returns_response_content(mock_groq_class):
    """Successful API call → returns the assistant message content as str."""
    fake_response = MagicMock()
    fake_response.choices = [MagicMock()]
    fake_response.choices[0].message.content = "Wisdom is knowing what you do not know."

    mock_instance = MagicMock()
    mock_instance.chat.completions.create.return_value = fake_response
    mock_groq_class.return_value = mock_instance

    client = GroqClient()
    result = client.chat(messages=[{"role": "user", "content": "What is wisdom?"}])

    assert result == "Wisdom is knowing what you do not know."
    assert isinstance(result, str)


@patch.dict("os.environ", {"GROQ_API_KEY": "test-key-123"})
@patch("sophia.llm.groq_client.Groq")
def test_chat_uses_default_model(mock_groq_class):
    """When no model arg given, uses 'openai/gpt-oss-20b'."""
    fake_response = MagicMock()
    fake_response.choices = [MagicMock()]
    fake_response.choices[0].message.content = "answer"

    mock_instance = MagicMock()
    mock_instance.chat.completions.create.return_value = fake_response
    mock_groq_class.return_value = mock_instance

    client = GroqClient()
    client.chat(messages=[{"role": "user", "content": "hi"}])

    call_kwargs = mock_instance.chat.completions.create.call_args
    assert call_kwargs.kwargs["model"] == "openai/gpt-oss-20b"


@patch.dict("os.environ", {"GROQ_API_KEY": "test-key-123"})
@patch("sophia.llm.groq_client.Groq")
def test_chat_uses_custom_model(mock_groq_class):
    """Explicit model arg overrides default."""
    fake_response = MagicMock()
    fake_response.choices = [MagicMock()]
    fake_response.choices[0].message.content = "answer"

    mock_instance = MagicMock()
    mock_instance.chat.completions.create.return_value = fake_response
    mock_groq_class.return_value = mock_instance

    client = GroqClient()
    client.chat(
        messages=[{"role": "user", "content": "hi"}],
        model="llama-3.3-70b-versatile",
    )

    call_kwargs = mock_instance.chat.completions.create.call_args
    assert call_kwargs.kwargs["model"] == "llama-3.3-70b-versatile"


# ---------------------------------------------------------------------------
# GroqClient.chat — input validation
# ---------------------------------------------------------------------------

@patch.dict("os.environ", {"GROQ_API_KEY": "test-key-123"})
@patch("sophia.llm.groq_client.Groq")
def test_chat_raises_on_empty_messages(mock_groq_class):
    """Empty messages list → ValueError. Don't waste an API call."""
    mock_groq_class.return_value = MagicMock()
    client = GroqClient()

    with pytest.raises(ValueError, match="messages"):
        client.chat(messages=[])


@patch.dict("os.environ", {"GROQ_API_KEY": "test-key-123"})
@patch("sophia.llm.groq_client.Groq")
def test_chat_raises_on_none_messages(mock_groq_class):
    """None messages → ValueError."""
    mock_groq_class.return_value = MagicMock()
    client = GroqClient()

    with pytest.raises(ValueError, match="messages"):
        client.chat(messages=None)


# ---------------------------------------------------------------------------
# GroqClient.chat — error wrapping
# ---------------------------------------------------------------------------

@patch.dict("os.environ", {"GROQ_API_KEY": "test-key-123"})
@patch("sophia.llm.groq_client.Groq")
def test_chat_wraps_api_connection_error(mock_groq_class):
    """groq.APIConnectionError → SophiaLLMError with 'connection' in message."""
    import groq

    mock_instance = MagicMock()
    mock_instance.chat.completions.create.side_effect = groq.APIConnectionError(
        request=MagicMock()
    )
    mock_groq_class.return_value = mock_instance

    client = GroqClient()
    with pytest.raises(SophiaLLMError, match="connection"):
        client.chat(messages=[{"role": "user", "content": "hi"}])


@patch.dict("os.environ", {"GROQ_API_KEY": "test-key-123"})
@patch("sophia.llm.groq_client.Groq")
def test_chat_wraps_rate_limit_error(mock_groq_class):
    """groq.RateLimitError → SophiaLLMError with 'rate limit' in message."""
    import groq

    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.headers = {}

    mock_instance = MagicMock()
    mock_instance.chat.completions.create.side_effect = groq.RateLimitError(
        message="rate limited",
        response=mock_response,
        body=None,
    )
    mock_groq_class.return_value = mock_instance

    client = GroqClient()
    with pytest.raises(SophiaLLMError, match="rate limit"):
        client.chat(messages=[{"role": "user", "content": "hi"}])


@patch.dict("os.environ", {"GROQ_API_KEY": "test-key-123"})
@patch("sophia.llm.groq_client.Groq")
def test_chat_wraps_api_status_error(mock_groq_class):
    """groq.APIStatusError → SophiaLLMError with status code in message."""
    import groq

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.headers = {}

    mock_instance = MagicMock()
    mock_instance.chat.completions.create.side_effect = groq.APIStatusError(
        message="internal server error",
        response=mock_response,
        body=None,
    )
    mock_groq_class.return_value = mock_instance

    client = GroqClient()
    with pytest.raises(SophiaLLMError, match="500"):
        client.chat(messages=[{"role": "user", "content": "hi"}])


# ---------------------------------------------------------------------------
# GroqClient.chat — empty response handling
# ---------------------------------------------------------------------------

@patch.dict("os.environ", {"GROQ_API_KEY": "test-key-123"})
@patch("sophia.llm.groq_client.Groq")
def test_chat_raises_on_empty_response_content(mock_groq_class):
    """API returns None content → SophiaLLMError. Don't return None silently."""
    fake_response = MagicMock()
    fake_response.choices = [MagicMock()]
    fake_response.choices[0].message.content = None

    mock_instance = MagicMock()
    mock_instance.chat.completions.create.return_value = fake_response
    mock_groq_class.return_value = mock_instance

    client = GroqClient()
    with pytest.raises(SophiaLLMError, match="empty"):
        client.chat(messages=[{"role": "user", "content": "hi"}])


@patch.dict("os.environ", {"GROQ_API_KEY": "test-key-123"})
@patch("sophia.llm.groq_client.Groq")
def test_chat_raises_on_no_choices(mock_groq_class):
    """API returns empty choices list → SophiaLLMError."""
    fake_response = MagicMock()
    fake_response.choices = []

    mock_instance = MagicMock()
    mock_instance.chat.completions.create.return_value = fake_response
    mock_groq_class.return_value = mock_instance

    client = GroqClient()
    with pytest.raises(SophiaLLMError, match="empty"):
        client.chat(messages=[{"role": "user", "content": "hi"}])


# ---------------------------------------------------------------------------
# GroqClient.chat_stream — streaming
# ---------------------------------------------------------------------------

def _make_stream_chunk(content):
    """Build a fake Groq streaming chunk whose delta carries `content`."""
    chunk = MagicMock()
    chunk.choices = [MagicMock()]
    chunk.choices[0].delta.content = content
    return chunk


@patch.dict("os.environ", {"GROQ_API_KEY": "test-key-123"})
@patch("sophia.llm.groq_client.Groq")
def test_chat_stream_yields_deltas_in_order(mock_groq_class):
    """chat_stream yields each delta's content in arrival order."""
    mock_instance = MagicMock()
    mock_instance.chat.completions.create.return_value = iter([
        _make_stream_chunk("Wisdom "),
        _make_stream_chunk("is "),
        _make_stream_chunk("love."),
    ])
    mock_groq_class.return_value = mock_instance

    client = GroqClient()
    tokens = list(client.chat_stream(messages=[{"role": "user", "content": "?"}]))

    assert tokens == ["Wisdom ", "is ", "love."]


@patch.dict("os.environ", {"GROQ_API_KEY": "test-key-123"})
@patch("sophia.llm.groq_client.Groq")
def test_chat_stream_skips_none_deltas(mock_groq_class):
    """A final chunk with delta.content=None (stream end) is skipped, not yielded."""
    mock_instance = MagicMock()
    mock_instance.chat.completions.create.return_value = iter([
        _make_stream_chunk("Hello"),
        _make_stream_chunk(None),
    ])
    mock_groq_class.return_value = mock_instance

    client = GroqClient()
    tokens = list(client.chat_stream(messages=[{"role": "user", "content": "hi"}]))

    assert tokens == ["Hello"]


@patch.dict("os.environ", {"GROQ_API_KEY": "test-key-123"})
@patch("sophia.llm.groq_client.Groq")
def test_chat_stream_passes_stream_true(mock_groq_class):
    """chat_stream calls the SDK with stream=True."""
    mock_instance = MagicMock()
    mock_instance.chat.completions.create.return_value = iter([_make_stream_chunk("x")])
    mock_groq_class.return_value = mock_instance

    client = GroqClient()
    list(client.chat_stream(messages=[{"role": "user", "content": "hi"}]))

    call_kwargs = mock_instance.chat.completions.create.call_args.kwargs
    assert call_kwargs["stream"] is True


@patch.dict("os.environ", {"GROQ_API_KEY": "test-key-123"})
@patch("sophia.llm.groq_client.Groq")
def test_chat_stream_raises_on_empty_messages(mock_groq_class):
    """Empty messages list → ValueError, eagerly (before any iteration)."""
    mock_groq_class.return_value = MagicMock()
    client = GroqClient()

    with pytest.raises(ValueError, match="messages"):
        client.chat_stream(messages=[])


@patch.dict("os.environ", {"GROQ_API_KEY": "test-key-123"})
@patch("sophia.llm.groq_client.Groq")
def test_chat_stream_wraps_rate_limit_error(mock_groq_class):
    """A RateLimitError during streaming is wrapped as SophiaLLMError."""
    import groq

    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.headers = {}

    mock_instance = MagicMock()
    mock_instance.chat.completions.create.side_effect = groq.RateLimitError(
        message="rate limited", response=mock_response, body=None,
    )
    mock_groq_class.return_value = mock_instance

    client = GroqClient()
    with pytest.raises(SophiaLLMError, match="rate limit"):
        list(client.chat_stream(messages=[{"role": "user", "content": "hi"}]))


# ---------------------------------------------------------------------------
# Real-API integration test (skips if GROQ_API_KEY is not set)
# ---------------------------------------------------------------------------

import os
from dotenv import load_dotenv

load_dotenv()
_HAS_API_KEY = bool(os.environ.get("GROQ_API_KEY"))


@pytest.mark.skipif(
    not _HAS_API_KEY,
    reason="GROQ_API_KEY not set; skipping live API test.",
)
def test_chat_live_api_returns_nonempty_string():
    """End-to-end: real API key + real Groq endpoint → non-empty response."""
    client = GroqClient()
    result = client.chat(
        messages=[{"role": "user", "content": "Say hello in exactly three words."}]
    )
    assert isinstance(result, str)
    assert len(result) > 0
