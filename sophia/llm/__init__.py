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

from sophia.llm.openrouter_client import OpenRouterClient, SophiaLLMError

__all__ = ["OpenRouterClient", "SophiaLLMError"]
