"""
orchestrator.py
===============
SophiaAI — Phase 8: The Sophia Orchestrator.

The brain of SophiaAI. Receives a user query, retrieves relevant corpus
passages, optionally searches the web, builds a prompt with Sophia's voice,
and returns a cited answer via the LLM.

Usage:
    from sophia.core import Sophia
    sophia = Sophia(retriever=retriever, llm_client=client)
    response = sophia.ask("What is consciousness?")
    print(response.answer)

Author: Cosmos De La Cruz — SophiaAI Phase 8
Philosophy: ZenCode PRO + CEO of Water
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sophia.rag.retriever import Chunk
from sophia.tools.web_search import SearchResult


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sophia.core.orchestrator")


DEFAULT_CONFIDENCE_THRESHOLD = 0.45


@dataclass
class SophiaResponse:
    answer: str
    chunks: list[Chunk] = field(default_factory=list)
    web_results: list[SearchResult] = field(default_factory=list)
    search_mode: str = "corpus"


class Sophia:

    def __init__(
        self,
        retriever,
        llm_client,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> None:
        self._retriever = retriever
        self._llm_client = llm_client
        self._confidence_threshold = confidence_threshold
        logger.info(
            "Sophia initialized. Confidence threshold: %.2f",
            confidence_threshold,
        )
