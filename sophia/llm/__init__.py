"""
SophiaAI — LLM Client package.

Public API:
    OpenRouterClient — Wraps the OpenRouter API behind chat() and chat_stream().
                       The rest of the app imports this boundary instead of
                       provider-specific HTTP details.
    SophiaLLMError   — Custom exception for all LLM failures. The orchestrator
                       catches this one type instead of knowing about provider
                       internals.

Anything else inside this package is implementation detail and may change.

Author: Cosmos De La Cruz — SophiaAI Phase 6
"""

from sophia.llm.openrouter_client import OpenRouterClient, SophiaLLMError

__all__ = ["OpenRouterClient", "SophiaLLMError"]
