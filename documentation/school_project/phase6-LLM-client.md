# Phase 6 — LLM Client Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a clean Groq API wrapper (`GroqClient`) that isolates all LLM-provider details behind a single `chat()` method, so the rest of SophiaAI never imports `groq` directly. Swapping Groq for another provider later changes only this file.

**Architecture:** A new Python package `sophia/llm/` containing `groq_client.py` (class + custom exception) and `__init__.py` (public exports). The class reads `GROQ_API_KEY` from the environment (loaded via `python-dotenv`), instantiates the Groq client once, and exposes one public method: `chat(messages, model) -> str`. All Groq-specific exceptions are caught and re-raised as `SophiaLLMError` so the orchestrator (Phase 8) never has to know which library is underneath.

**Tech Stack:** `groq` (Python client, already in requirements.txt), `python-dotenv` (already in requirements.txt), `pytest` for tests. No new dependencies needed.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `sophia/llm/__init__.py` | Create | Public exports: `GroqClient`, `SophiaLLMError` |
| `sophia/llm/groq_client.py` | Create | `SophiaLLMError` exception + `GroqClient` class |
| `tests/test_groq_client.py` | Create | Unit tests with mocked Groq client |
| `.env.example` | Modify | Add `GROQ_MODEL` entry |
| `cosmos_log.md` | Modify | Append Phase 6 entry |

---

## Branch Setup

- [ ] **Step 0: Create feature branch**

```powershell
SophiaAI-venv\Scripts\Activate.ps1
git checkout -b feat/phase6-llm-client
```

Activates the venv and creates the feature branch. All commits land on `feat/phase6-llm-client`; merge to `master` after final verification.

---

## Task 1: Write the failing tests

**Files:**
- Create: `tests/test_groq_client.py`

- [ ] **Step 1: Write the test file**

```python
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
    """When no model arg given, uses 'llama-3.1-8b-instant'."""
    fake_response = MagicMock()
    fake_response.choices = [MagicMock()]
    fake_response.choices[0].message.content = "answer"

    mock_instance = MagicMock()
    mock_instance.chat.completions.create.return_value = fake_response
    mock_groq_class.return_value = mock_instance

    client = GroqClient()
    client.chat(messages=[{"role": "user", "content": "hi"}])

    call_kwargs = mock_instance.chat.completions.create.call_args
    assert call_kwargs.kwargs["model"] == "llama-3.1-8b-instant"


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
        model="gemma2-9b-it",
    )

    call_kwargs = mock_instance.chat.completions.create.call_args
    assert call_kwargs.kwargs["model"] == "gemma2-9b-it"


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
```

- [ ] **Step 2: Run tests to verify they fail**

```powershell
pytest tests/test_groq_client.py -v
```

Expected output: `ModuleNotFoundError: No module named 'sophia.llm'`. Correct — the package does not exist yet. We create it in Task 2.

---

## Task 2: Implement the `sophia/llm/` package

**Files:**
- Create: `sophia/llm/__init__.py`
- Create: `sophia/llm/groq_client.py`

- [ ] **Step 3: Create the llm sub-package init**

```python
# sophia/llm/__init__.py
"""
SophiaAI — LLM Client package.

Public API:
    GroqClient     — Wraps the Groq API behind a single chat() method.
                     The rest of the app imports this, never the groq
                     library directly.
    SophiaLLMError — Custom exception for all LLM failures. The orchestrator
                     catches this one type instead of knowing about Groq's
                     internal exception hierarchy.

Anything else inside this package is implementation detail and may change.

Author: Cosmos De La Cruz — SophiaAI Phase 6
"""

from sophia.llm.groq_client import GroqClient, SophiaLLMError

__all__ = ["GroqClient", "SophiaLLMError"]
```

- [ ] **Step 4: Write the groq_client module**

```python
# sophia/llm/groq_client.py
"""
groq_client.py
==============
SophiaAI — Phase 6: LLM Client.

A clean wrapper around the Groq Python SDK. Reads the API key from
the environment, instantiates the Groq client once, and exposes a
single public method: chat(messages, model) -> str.

Mental Model:
    The orchestrator (Phase 8) calls client.chat(messages) and either
    gets a string back or gets a SophiaLLMError. It never imports groq
    directly, never handles groq.RateLimitError, never parses the
    ChatCompletion response object. All of that is this file's job.

    If Groq disappears tomorrow, you swap this one file. Every other
    module in SophiaAI stays untouched.

Usage:
    from sophia.llm import GroqClient
    client = GroqClient()
    answer = client.chat([
        {"role": "system", "content": "You are Sophia."},
        {"role": "user", "content": "What is consciousness?"},
    ])
    print(answer)

Author: Cosmos De La Cruz — SophiaAI Phase 6
Philosophy: ZenCode PRO + CEO of Water
"""

from __future__ import annotations

import logging
import os

import groq
from dotenv import load_dotenv
from groq import Groq

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sophia.llm.groq_client")


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class SophiaLLMError(Exception):
    """
    Mental Model:
        The single exception type that escapes this module. Every Groq-specific
        error is caught here and re-raised as SophiaLLMError so the rest of the
        app has one clean catch target.

        The original exception is always chained via __cause__ so you can still
        inspect the root cause in logs or during debugging.

    Usage:
        try:
            answer = client.chat(messages)
        except SophiaLLMError as e:
            logger.error(f"LLM failed: {e}")
            # e.__cause__ has the original groq exception if needed
    """


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "llama-3.1-8b-instant"


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------

class GroqClient:
    """
    Mental Model:
        A thin shell around the Groq Python SDK. Holds one piece of state:
        the authenticated groq.Groq client instance, created once at init.

        The class exists so the orchestrator can call client.chat(messages)
        without knowing anything about Groq's API shape, error types, or
        response parsing. Single responsibility: translate between SophiaAI's
        internal message format and Groq's API.

    Args (constructor):
        api_key: Groq API key. If None, reads from GROQ_API_KEY env var
                 (loaded from .env via python-dotenv). Explicit arg is
                 useful for testing without touching the environment.

    Raises (constructor):
        SophiaLLMError: GROQ_API_KEY not found in environment and no
                        explicit api_key provided.
    """

    def __init__(self, api_key: str | None = None) -> None:
        load_dotenv()

        resolved_key = api_key or os.environ.get("GROQ_API_KEY")
        if not resolved_key:
            raise SophiaLLMError(
                "GROQ_API_KEY not found. Set it in your .env file or pass "
                "api_key= to GroqClient(). See .env.example for the format."
            )

        self._client = Groq(api_key=resolved_key)
        logger.info("GroqClient initialized. Default model: %s", DEFAULT_MODEL)

    def chat(
        self,
        messages: list[dict],
        model: str = DEFAULT_MODEL,
    ) -> str:
        """
        Mental Model:
            Send a conversation to the Groq API and return the assistant's
            reply as a plain string. All Groq exceptions are caught and
            re-raised as SophiaLLMError.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                      Must contain at least one message. Follows the OpenAI
                      chat format: [{"role": "user", "content": "..."}].
            model:    Groq model identifier. Defaults to llama-3.1-8b-instant.
                      Other options: gemma2-9b-it, llama-3.3-70b-versatile.

        Returns:
            str: The assistant's response text.

        Raises:
            ValueError: messages is None or empty.
            SophiaLLMError: Any Groq API failure (connection, rate limit,
                           server error) or unexpected empty response.
        """
        if not messages:
            raise ValueError(
                "messages must be a non-empty list of message dicts, "
                "got empty or None."
            )

        try:
            response = self._client.chat.completions.create(
                messages=messages,
                model=model,
            )
        except groq.APIConnectionError as error:
            raise SophiaLLMError(
                f"Groq API connection failed. Check your network and try "
                f"again. Original error: {error}"
            ) from error
        except groq.RateLimitError as error:
            raise SophiaLLMError(
                f"Groq API rate limit exceeded. The free tier allows limited "
                f"requests per minute. Wait and retry. Original error: {error}"
            ) from error
        except groq.APIStatusError as error:
            raise SophiaLLMError(
                f"Groq API returned status {error.status_code}. "
                f"Original error: {error}"
            ) from error

        if not response.choices or response.choices[0].message.content is None:
            raise SophiaLLMError(
                "Groq API returned an empty response. No choices or content "
                "was None. This is unusual — retry or check the model name."
            )

        return response.choices[0].message.content
```

- [ ] **Step 5: Run tests to verify they pass**

```powershell
pytest tests/test_groq_client.py -v
```

Expected output:
```
tests/test_groq_client.py::test_sophia_llm_error_is_exception PASSED
tests/test_groq_client.py::test_sophia_llm_error_preserves_cause PASSED
tests/test_groq_client.py::test_init_creates_client_with_api_key PASSED
tests/test_groq_client.py::test_init_raises_when_api_key_missing PASSED
tests/test_groq_client.py::test_chat_returns_response_content PASSED
tests/test_groq_client.py::test_chat_uses_default_model PASSED
tests/test_groq_client.py::test_chat_uses_custom_model PASSED
tests/test_groq_client.py::test_chat_raises_on_empty_messages PASSED
tests/test_groq_client.py::test_chat_raises_on_none_messages PASSED
tests/test_groq_client.py::test_chat_wraps_api_connection_error PASSED
tests/test_groq_client.py::test_chat_wraps_rate_limit_error PASSED
tests/test_groq_client.py::test_chat_wraps_api_status_error PASSED
tests/test_groq_client.py::test_chat_raises_on_empty_response_content PASSED
tests/test_groq_client.py::test_chat_raises_on_no_choices PASSED

14 passed in X.XXs
```

- [ ] **Step 6: Commit package + tests**

```powershell
git add sophia/llm/__init__.py sophia/llm/groq_client.py tests/test_groq_client.py docs/superpowers/plans/phase6-LLM-client.md
git commit -m "feat(phase6): add GroqClient wrapper with unit tests"
```

---

## Task 3: Integration smoke test + finalize

Verify GroqClient works against the real Groq API with the real key from `.env`.

- [ ] **Step 7: Confirm groq package is installed**

```powershell
pip list | Select-String "groq"
```

Expected: `groq` appears with version >= 0.15.0. If missing, run `pip install groq`.

- [ ] **Step 8: Confirm GROQ_API_KEY is set**

```powershell
python -c "from dotenv import load_dotenv; import os; load_dotenv(); key = os.environ.get('GROQ_API_KEY', ''); print(f'Key present: {bool(key and key != \"your_api_key_here\")}  Length: {len(key)}')"
```

Expected: `Key present: True  Length: <some number>`. If False, edit `.env` and add your real Groq API key.

- [ ] **Step 9: Run the live smoke test**

```powershell
python -c "from sophia.llm import GroqClient; c = GroqClient(); r = c.chat([{'role': 'user', 'content': 'In one sentence, what is wisdom?'}]); print(f'Response ({len(r)} chars): {r[:200]}')"
```

Expected: A coherent one-sentence answer about wisdom, ~50-200 characters. This confirms the API key works, the model responds, and the wrapper returns a clean string.

- [ ] **Step 10: Add integration test to test file**

Append to `tests/test_groq_client.py`:

```python
# ---------------------------------------------------------------------------
# Real-API integration test (skips if GROQ_API_KEY is not set)
# ---------------------------------------------------------------------------

_HAS_API_KEY = bool(os.environ.get("GROQ_API_KEY"))


@pytest.mark.skipif(
    not _HAS_API_KEY,
    reason="GROQ_API_KEY not set; skipping live API test.",
)
def test_chat_live_api_returns_nonempty_string():
    """End-to-end: real API key + real Groq endpoint → non-empty response."""
    load_dotenv()
    client = GroqClient()
    result = client.chat(
        messages=[{"role": "user", "content": "Say hello in exactly three words."}]
    )
    assert isinstance(result, str)
    assert len(result) > 0
```

Also add the required imports at the top of the file (after the existing imports):

```python
import os
from dotenv import load_dotenv
```

Then re-run:

```powershell
pytest tests/test_groq_client.py -v
```

Expected: 15 passed (or 14 passed + 1 skipped if GROQ_API_KEY is not set in the environment).

- [ ] **Step 11: Update .env.example**

Add the model entry so future developers know the option exists:

```
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

The `GROQ_MODEL` line is documentation only — `GroqClient` uses a default constant, not an env var for the model. This tells people which model the system defaults to.

- [ ] **Step 12: Run all existing tests to verify no regressions**

```powershell
pytest tests/ -v
```

Expected: All tests pass — Phase 3 (7), Phase 4 (9), Phase 5 (13), Phase 6 (15). Total: 44 tests, 0 failures. The Phase 5 integration test may skip if FAISS artifacts are missing, and the Phase 6 integration test may skip if GROQ_API_KEY is not set.

- [ ] **Step 13: Update cosmos_log.md**

Append to `cosmos_log.md`:

```markdown
## Phase 6 — LLM Client

**Date:** 2026-05-23

**What was built:** Package `sophia/llm/` with class `GroqClient` and custom
exception `SophiaLLMError`. The class reads GROQ_API_KEY from the environment
(via python-dotenv), instantiates the Groq Python SDK client once, and exposes
one method: `chat(messages, model) -> str`. All Groq-specific exceptions
(connection failures, rate limits, HTTP errors) are caught and re-raised as
`SophiaLLMError` so the orchestrator never imports the groq library directly.

**Artifacts:**
- `sophia/llm/__init__.py` — public exports: GroqClient, SophiaLLMError
- `sophia/llm/groq_client.py` — class + exception + constants
- `tests/test_groq_client.py` — 14 mocked unit tests + 1 live-API integration test

**Why a wrapper:** Single responsibility. The orchestrator asks for an answer
and gets a string or a SophiaLLMError. It does not know about groq.RateLimitError,
ChatCompletion objects, or response.choices[0].message.content parsing. If Groq
shuts down tomorrow, you change one file and the rest of SophiaAI keeps running.

**Why SophiaLLMError:** The alternative is letting groq exceptions leak into
the orchestrator, which then needs to import groq just to catch them. That
defeats the purpose of the wrapper. One custom exception = one clean catch target.

**Default model:** llama-3.1-8b-instant (Groq free tier, fast, good enough for
a RAG assistant). The model argument is explicit so Phase 8 can experiment with
other models without touching this file.

**Next step:** Phase 7 — `sophia/tools/web_search.py` with function web_search().
DuckDuckGo wrapper for when the corpus does not have the answer.
```

- [ ] **Step 14: Final commit**

```powershell
git add cosmos_log.md tests/test_groq_client.py .env.example
git commit -m "feat(phase6): GroqClient verified against live API"
```

- [ ] **Step 15: Merge to master**

```powershell
git checkout master
git merge --no-ff feat/phase6-llm-client -m "merge: Phase 6 — LLM Client"
```

Switches to master and merges the feature branch with a merge commit so the phase boundary is visible in `git log --graph`.

---

## Self-Review

**Spec coverage (from `developing_plan.md` Phase 6 + `MEMORY.md` Phase 6 preview):**
- Read GROQ_API_KEY from .env via python-dotenv — `__init__` with `load_dotenv()` + `os.environ.get`
- One public method: `chat(messages, model) -> str` — `chat()`
- Default model `llama-3.1-8b-instant` — `DEFAULT_MODEL` constant
- Wrap Groq exceptions in custom SophiaLLMError — three `except` clauses in `chat()`
- Library code raises, never sys.exit — every error path
- Single file swap-point for provider change — `groq_client.py` is the only file importing `groq`
- Package layout matches `sophia/llm/__init__.py` + `sophia/llm/groq_client.py` — File Structure table
- Branch `feat/phase6-llm-client` → merge to `master` — Steps 0 and 15
- ZenCode PRO docstrings with Mental Model sections — every public symbol

**Test coverage matrix:**

| Behavior | Test |
|---|---|
| SophiaLLMError is Exception | `test_sophia_llm_error_is_exception` |
| SophiaLLMError chains cause | `test_sophia_llm_error_preserves_cause` |
| Init with valid API key | `test_init_creates_client_with_api_key` |
| Init without API key | `test_init_raises_when_api_key_missing` |
| Chat returns string | `test_chat_returns_response_content` |
| Default model used | `test_chat_uses_default_model` |
| Custom model used | `test_chat_uses_custom_model` |
| Empty messages list | `test_chat_raises_on_empty_messages` |
| None messages | `test_chat_raises_on_none_messages` |
| Connection error wrapped | `test_chat_wraps_api_connection_error` |
| Rate limit error wrapped | `test_chat_wraps_rate_limit_error` |
| API status error wrapped | `test_chat_wraps_api_status_error` |
| Empty response content | `test_chat_raises_on_empty_response_content` |
| No choices in response | `test_chat_raises_on_no_choices` |
| Live API round-trip | `test_chat_live_api_returns_nonempty_string` |

**Placeholder scan:** No TBD, TODO, or vague steps. All code, commands, and expected output shown literally.

**Type consistency:**
- `SophiaLLMError(str)` — standard Exception subclass, no custom __init__ needed.
- `GroqClient.__init__(api_key: str | None = None) -> None` — matches every test call.
- `GroqClient.chat(messages: list[dict], model: str = DEFAULT_MODEL) -> str` — matches every test call.
- `DEFAULT_MODEL = "llama-3.1-8b-instant"` — referenced in tests and docstrings consistently.

**What Phase 6 unlocks:**
- Phase 8 (Orchestrator) imports `from sophia.llm import GroqClient, SophiaLLMError` and calls `client.chat(messages)` to get the LLM response.
- The `sophia/llm/` package now exists. If we ever add a second LLM provider, it becomes a sibling module (e.g., `sophia/llm/openai_client.py`) behind the same interface.
- Combined with Phase 5 (retriever), we now have both halves of the RAG pipeline: retrieve passages + generate answers. Phase 7 adds the web search fallback, then Phase 8 wires them together.
