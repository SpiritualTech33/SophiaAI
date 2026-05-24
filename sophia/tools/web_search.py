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

from ddgs import DDGS


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
