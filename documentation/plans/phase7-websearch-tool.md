# Phase 7 — Web Search Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a DuckDuckGo web search wrapper (`web_search()`) that gives Sophia the ability to look beyond the corpus when the RAG pipeline lacks the answer.

**Architecture:** A new Python package `sophia/tools/` containing `web_search.py` with one public function: `web_search(query, max_results) -> list[SearchResult]`. The function calls `DDGS().text()` from the `duckduckgo-search` library, maps raw dicts into `SearchResult` dataclasses, and wraps all network/library failures in `SophiaSearchError`. The orchestrator (Phase 8) calls this function when retrieval confidence is below threshold — it never imports `duckduckgo_search` directly.

**Tech Stack:** `duckduckgo-search` (already in requirements.txt, needs `pip install`), `pytest` for tests. No API key needed. No new dependencies beyond what requirements.txt already lists.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `sophia/tools/__init__.py` | Create | Public exports: `web_search`, `SearchResult`, `SophiaSearchError` |
| `sophia/tools/web_search.py` | Create | `SearchResult` dataclass + `SophiaSearchError` exception + `web_search()` function |
| `tests/test_web_search.py` | Create | Unit tests with mocked DDGS + live integration test |
| `cosmos_log.md` | Modify | Append Phase 7 entry |

---

## Branch Setup

- [ ] **Step 0: Create feature branch**

```powershell
SophiaAI-venv\Scripts\Activate.ps1
git checkout -b feat/phase7-web-search
```

Activates the venv and creates the feature branch. All commits land on `feat/phase7-web-search`; merge to `master` after final verification.

- [ ] **Step 0.5: Install duckduckgo-search**

```powershell
pip install duckduckgo-search>=6.0.0
```

The package is listed in requirements.txt but not yet installed. This installs it into the venv. Verify:

```powershell
pip show duckduckgo-search
```

Expected: version >= 6.0.0 appears. The library exports `DDGS` from `duckduckgo_search`.

---

## Task 1: Write the failing tests

**Files:**
- Create: `tests/test_web_search.py`

- [ ] **Step 1: Write the test file**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```powershell
pytest tests/test_web_search.py -v
```

Expected output: `ModuleNotFoundError: No module named 'sophia.tools'`. Correct — the package does not exist yet. We create it in Task 2.

---

## Task 2: Implement the `sophia/tools/` package

**Files:**
- Create: `sophia/tools/__init__.py`
- Create: `sophia/tools/web_search.py`

- [ ] **Step 3: Create the tools sub-package init**

```python
# sophia/tools/__init__.py
"""
SophiaAI — Tools package.

Public API:
    web_search       — Searches DuckDuckGo and returns structured results.
                       The orchestrator calls this when the corpus lacks
                       the answer. No other module imports duckduckgo_search
                       directly.
    SearchResult     — Dataclass holding one search result (title, url, snippet).
    SophiaSearchError — Custom exception for all web search failures.

Anything else inside this package is implementation detail and may change.

Author: Cosmos De La Cruz — SophiaAI Phase 7
"""

from sophia.tools.web_search import SearchResult, SophiaSearchError, web_search

__all__ = ["web_search", "SearchResult", "SophiaSearchError"]
```

- [ ] **Step 4: Write the web_search module**

```python
# sophia/tools/web_search.py
"""
web_search.py
=============
SophiaAI — Phase 7: Web Search Tool.

A thin wrapper around the duckduckgo-search library. Exposes one public
function: web_search(query, max_results) -> list[SearchResult].

Mental Model:
    The orchestrator (Phase 8) calls web_search("some question") when
    the RAG retrieval score is below the confidence threshold. It gets
    back a list of SearchResult dataclasses or a SophiaSearchError. It
    never imports duckduckgo_search directly, never handles DDGS internals,
    never parses raw result dicts.

    If DuckDuckGo changes their API tomorrow, you swap this one file.
    Every other module in SophiaAI stays untouched.

Usage:
    from sophia.tools import web_search
    results = web_search("What is the Tao?", max_results=3)
    for r in results:
        print(f"{r.title} — {r.url}")
        print(f"  {r.snippet}")

Author: Cosmos De La Cruz — SophiaAI Phase 7
Philosophy: ZenCode PRO + CEO of Water
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from duckduckgo_search import DDGS


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sophia.tools.web_search")


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class SophiaSearchError(Exception):
    """
    Mental Model:
        The single exception type that escapes this module. Every network
        failure, timeout, or duckduckgo-search internal error is caught
        here and re-raised as SophiaSearchError so the orchestrator has
        one clean catch target.

        The original exception is always chained via __cause__ so you can
        still inspect the root cause in logs or during debugging.

    Usage:
        try:
            results = web_search("query")
        except SophiaSearchError as e:
            logger.error(f"Search failed: {e}")
            # e.__cause__ has the original exception if needed
    """


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SearchResult:
    """
    Mental Model:
        One web search result. Immutable. The orchestrator reads these
        fields to inject web context into the LLM prompt.

        Maps from DuckDuckGo raw dict keys:
            'title' -> title
            'href'  -> url
            'body'  -> snippet
    """

    title: str
    url: str
    snippet: str


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MAX_RESULTS = 5


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def web_search(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> list[SearchResult]:
    """
    Mental Model:
        Send a query to DuckDuckGo and return structured results. All
        network and library exceptions are caught and re-raised as
        SophiaSearchError. Malformed results (missing required keys)
        are silently skipped with a warning — one bad result must not
        kill the search.

    Args:
        query:       The search query string. Must be non-empty after
                     stripping whitespace.
        max_results: Maximum number of results to return. Defaults to 5.

    Returns:
        list[SearchResult]: Zero or more search results. Empty list is
                            valid (no results found, not an error).

    Raises:
        ValueError: query is empty or whitespace-only.
        SophiaSearchError: Any network, timeout, or library failure.
    """
    if not query or not query.strip():
        raise ValueError(
            "query must be a non-empty string, got empty or whitespace-only."
        )

    try:
        ddgs = DDGS()
        raw_results = ddgs.text(query, max_results=max_results)
    except (ConnectionError, OSError) as error:
        raise SophiaSearchError(
            f"Web search failed: network error. Check your internet "
            f"connection and try again. Original error: {error}"
        ) from error
    except TimeoutError as error:
        raise SophiaSearchError(
            f"Web search timed out. DuckDuckGo did not respond in time. "
            f"Try again later. Original error: {error}"
        ) from error
    except Exception as error:
        raise SophiaSearchError(
            f"Web search failed unexpectedly. "
            f"Original error: {type(error).__name__}: {error}"
        ) from error

    results = []
    for raw in raw_results:
        try:
            result = SearchResult(
                title=raw["title"],
                url=raw["href"],
                snippet=raw["body"],
            )
            results.append(result)
        except (KeyError, TypeError) as parse_error:
            logger.warning(
                "Skipping malformed search result: %s — error: %s",
                raw,
                parse_error,
            )

    logger.info(
        "Web search for '%s': %d results returned (requested %d).",
        query,
        len(results),
        max_results,
    )
    return results
```

- [ ] **Step 5: Run tests to verify they pass**

```powershell
pytest tests/test_web_search.py -v
```

Expected output:
```
tests/test_web_search.py::test_search_result_has_required_fields PASSED
tests/test_web_search.py::test_search_result_stores_values PASSED
tests/test_web_search.py::test_sophia_search_error_is_exception PASSED
tests/test_web_search.py::test_sophia_search_error_preserves_cause PASSED
tests/test_web_search.py::test_web_search_raises_on_empty_query PASSED
tests/test_web_search.py::test_web_search_raises_on_whitespace_query PASSED
tests/test_web_search.py::test_web_search_returns_list_of_search_results PASSED
tests/test_web_search.py::test_web_search_uses_default_max_results PASSED
tests/test_web_search.py::test_web_search_uses_custom_max_results PASSED
tests/test_web_search.py::test_web_search_returns_empty_list_when_no_results PASSED
tests/test_web_search.py::test_web_search_skips_malformed_results PASSED
tests/test_web_search.py::test_web_search_wraps_connection_error PASSED
tests/test_web_search.py::test_web_search_wraps_timeout_error PASSED
tests/test_web_search.py::test_web_search_wraps_unexpected_exception PASSED

14 passed in X.XXs
```

- [ ] **Step 6: Commit package + tests**

```powershell
git add sophia/tools/__init__.py sophia/tools/web_search.py tests/test_web_search.py docs/superpowers/plans/phase7-websearch-tool.md
git commit -m "feat(phase7): add web_search wrapper with unit tests"
```

---

## Task 3: Integration smoke test + finalize

Verify web_search works against the real DuckDuckGo endpoint.

- [ ] **Step 7: Run the live smoke test**

```powershell
python -c "from sophia.tools import web_search; results = web_search('What is the Tao Te Ching', max_results=3); [print(f'{r.title} | {r.url[:60]} | {r.snippet[:80]}') for r in results]"
```

Expected: 2-3 results about the Tao Te Ching with titles, URLs, and snippets. Confirms DuckDuckGo responds and the wrapper maps fields correctly.

- [ ] **Step 8: Add integration test to test file**

Append to `tests/test_web_search.py`:

```python
# ---------------------------------------------------------------------------
# Real-network integration test (skips in CI / offline environments)
# ---------------------------------------------------------------------------

import os

_RUN_LIVE_SEARCH = os.environ.get("SOPHIA_LIVE_SEARCH", "1") == "1"


@pytest.mark.skipif(
    not _RUN_LIVE_SEARCH,
    reason="SOPHIA_LIVE_SEARCH != 1; skipping live search test.",
)
def test_web_search_live_returns_results():
    """End-to-end: real DuckDuckGo query -> non-empty list of SearchResult."""
    results = web_search(query="Python programming language", max_results=3)
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(r, SearchResult) for r in results)
    assert all(r.title for r in results)
    assert all(r.url.startswith("http") for r in results)
    assert all(r.snippet for r in results)
```

Then re-run:

```powershell
pytest tests/test_web_search.py -v
```

Expected: 15 passed (14 mocked + 1 live). If offline, the live test can be skipped by setting `SOPHIA_LIVE_SEARCH=0`.

- [ ] **Step 9: Run all existing tests to verify no regressions**

```powershell
pytest tests/ -v
```

Expected: All tests pass — Phase 3 (7), Phase 4 (9), Phase 5 (13), Phase 6 (15), Phase 7 (15). Total: 59 tests, 0 failures. Integration tests may skip depending on environment (FAISS artifacts, GROQ_API_KEY, network).

- [ ] **Step 10: Update cosmos_log.md**

Append to `cosmos_log.md`:

```markdown
## Phase 7 — Web Search Tool

**Date:** 2026-05-24

**What was built:** Package `sophia/tools/` with function `web_search()`, dataclass
`SearchResult`, and custom exception `SophiaSearchError`. The function calls
`DDGS().text()` from the duckduckgo-search library, maps raw result dicts into
immutable SearchResult dataclasses (title, url, snippet), and wraps all network
and library failures in SophiaSearchError. Malformed results are silently skipped
with a warning — one bad result never crashes the search.

**Artifacts:**
- `sophia/tools/__init__.py` — public exports: web_search, SearchResult, SophiaSearchError
- `sophia/tools/web_search.py` — function + dataclass + exception
- `tests/test_web_search.py` — 14 mocked unit tests + 1 live integration test

**Why a function and not a class:** Unlike the retriever or LLM client, web_search
has no expensive initialization. No model to load, no index to read, no API key to
validate at startup. A stateless function is simpler and sufficient. The orchestrator
calls web_search(query) and gets results or an error. No state, no lifecycle.

**Why SophiaSearchError:** Same pattern as SophiaLLMError in Phase 6. The orchestrator
catches one exception type per capability. It does not need to know whether the failure
was a DNS timeout, a DuckDuckGo rate limit, or a parsing bug — it needs to know the
search failed and fall back gracefully.

**Field mapping from DuckDuckGo:** The raw API returns dicts with keys 'title', 'href',
'body'. SearchResult maps these to 'title', 'url', 'snippet' — names that make sense
in the context of SophiaAI's prompt construction.

**Next step:** Phase 8 — `sophia/core/orchestrator.py` with class Sophia. The brain
that ties retrieval, web search, and LLM together.
```

- [ ] **Step 11: Final commit**

```powershell
git add cosmos_log.md tests/test_web_search.py
git commit -m "feat(phase7): web_search verified against live DuckDuckGo"
```

- [ ] **Step 12: Merge to master**

```powershell
git checkout master
git merge --no-ff feat/phase7-web-search -m "merge: Phase 7 — Web Search Tool"
```

Switches to master and merges the feature branch with a merge commit so the phase boundary is visible in `git log --graph`.

---

## Self-Review

**Spec coverage (from `developing_plan.md` Phase 7 + `MEMORY.md` Phase 7 preview):**
- Function `web_search(query, max_results)` — Step 4
- Returns `list[SearchResult]` dataclass with fields: title, url, snippet — Step 4
- Uses `duckduckgo-search` v8.x: `DDGS().text(query, max_results)` — Step 4
- Wraps network calls in try/except — three except clauses in `web_search()`
- No API key needed — confirmed, no env var required
- Package layout `sophia/tools/__init__.py` + `sophia/tools/web_search.py` — File Structure table
- Branch `feat/phase7-web-search` -> merge to `master` — Steps 0 and 12
- ZenCode PRO docstrings with Mental Model sections — every public symbol
- Library code raises, never sys.exit — every error path
- Single file swap-point: only `web_search.py` imports `duckduckgo_search`

**Test coverage matrix:**

| Behavior | Test |
|---|---|
| SearchResult has correct fields | `test_search_result_has_required_fields` |
| SearchResult stores values | `test_search_result_stores_values` |
| SophiaSearchError is Exception | `test_sophia_search_error_is_exception` |
| SophiaSearchError chains cause | `test_sophia_search_error_preserves_cause` |
| Empty query rejected | `test_web_search_raises_on_empty_query` |
| Whitespace query rejected | `test_web_search_raises_on_whitespace_query` |
| Returns list of SearchResult | `test_web_search_returns_list_of_search_results` |
| Default max_results = 5 | `test_web_search_uses_default_max_results` |
| Custom max_results passed through | `test_web_search_uses_custom_max_results` |
| Empty results = empty list | `test_web_search_returns_empty_list_when_no_results` |
| Malformed results skipped | `test_web_search_skips_malformed_results` |
| ConnectionError wrapped | `test_web_search_wraps_connection_error` |
| TimeoutError wrapped | `test_web_search_wraps_timeout_error` |
| Unexpected error wrapped + chained | `test_web_search_wraps_unexpected_exception` |
| Live DuckDuckGo round-trip | `test_web_search_live_returns_results` |

**Placeholder scan:** No TBD, TODO, or vague steps. All code, commands, and expected output shown literally.

**Type consistency:**
- `SophiaSearchError(str)` — standard Exception subclass, no custom __init__ needed.
- `SearchResult(title: str, url: str, snippet: str)` — frozen dataclass, used consistently across all tests.
- `web_search(query: str, max_results: int = 5) -> list[SearchResult]` — matches every test call.
- `DEFAULT_MAX_RESULTS = 5` — referenced in tests and docstrings consistently.

**What Phase 7 unlocks:**
- Phase 8 (Orchestrator) imports `from sophia.tools import web_search, SophiaSearchError` and calls `web_search(query)` when retrieval confidence is low.
- Combined with Phase 5 (retriever) and Phase 6 (LLM client), we now have all three capabilities the orchestrator needs: retrieve from corpus, search the web, generate answers. Phase 8 wires them together.
