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

# Load .env once at import time so callers can override via os.environ later.
load_dotenv()


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

DEFAULT_MODEL = "openai/gpt-oss-20b"


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
            model:    Groq model identifier. Defaults to openai/gpt-oss-20b.
                      Other options: llama-3.1-8b-instant, llama-3.3-70b-versatile.

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

    def chat_stream(self, messages: list[dict], model: str = DEFAULT_MODEL):
        """
        Mental Model:
            The streaming twin of chat(). Instead of one blocking string, it
            yields the assistant's reply token-by-token as the model produces
            it, so the UI can paint the answer as it arrives. Same single
            responsibility: translate Groq's stream into plain text deltas and
            funnel every Groq error into SophiaLLMError.

            Input validation is eager (a regular method call), but the actual
            network call lives in the inner generator, so streaming errors are
            wrapped when the caller iterates — exactly when they occur.

        Args:
            messages: Non-empty list of OpenAI-format message dicts.
            model:    Groq model identifier. Defaults to openai/gpt-oss-20b.

        Returns:
            Iterator[str]: Successive content deltas. None deltas (the final
            end-of-stream chunk) are skipped.

        Raises:
            ValueError: messages is None or empty (raised eagerly).
            SophiaLLMError: Any Groq API failure during streaming.
        """
        if not messages:
            raise ValueError(
                "messages must be a non-empty list of message dicts, "
                "got empty or None."
            )

        return self._stream_tokens(messages, model)

    def _stream_tokens(self, messages: list[dict], model: str):
        """Inner generator: open the Groq stream and yield content deltas."""
        try:
            stream = self._client.chat.completions.create(
                messages=messages,
                model=model,
                stream=True,
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta is not None:
                    yield delta
        except groq.APIConnectionError as error:
            raise SophiaLLMError(
                f"Groq API connection failed during streaming. Check your "
                f"network and try again. Original error: {error}"
            ) from error
        except groq.RateLimitError as error:
            raise SophiaLLMError(
                f"Groq API rate limit exceeded during streaming. The free tier "
                f"allows limited requests per minute. Wait and retry. "
                f"Original error: {error}"
            ) from error
        except groq.APIStatusError as error:
            raise SophiaLLMError(
                f"Groq API returned status {error.status_code} during "
                f"streaming. Original error: {error}"
            ) from error
