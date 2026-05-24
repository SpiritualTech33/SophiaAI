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
