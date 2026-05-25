"""
SophiaAI — Core package.

Public API:
    Sophia         — The orchestrator. Ties retrieval, web search, and LLM
                     together into a single ask() method.
    SophiaResponse — Dataclass holding the answer, sources, and search mode.

Author: Cosmos De La Cruz — SophiaAI Phase 8
"""

from sophia.core.orchestrator import Sophia, SophiaResponse

__all__ = ["Sophia", "SophiaResponse"]
