"""
SophiaAI — Retrieval-Augmented Generation package.

Public API:
    SophiaRetriever — loads FAISS index + embedding model + chunk metadata
                      once at startup and exposes .retrieve(query, top_k).
    Chunk          — dataclass describing a single retrieval result
                      (text + source file + pillar + chunk_id + score).

Anything else inside this package is implementation detail and may change.

Author: Cosmos De La Cruz — SophiaAI Phase 5
"""

from sophia.rag.retriever import Chunk, SophiaRetriever

__all__ = ["Chunk", "SophiaRetriever"]
