"""
openrouter_client.py
====================
SophiaAI — Phase 6: LLM Client.

A clean wrapper around the OpenRouter API using httpx. Reads the API key
from the environment, instantiates the HTTP client, and exposes two public
methods: chat(messages, model) -> str and chat_stream(messages, model) -> Iterator[str].

Philosophy: ZenCode PRO + CEO of Water
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections.abc import Iterator

import httpx
from dotenv import load_dotenv

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
logger = logging.getLogger("sophia.llm.openrouter_client")


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class SophiaLLMError(Exception):
    """
    Mental Model:
        The single exception type that escapes this module. Every OpenRouter-specific
        or HTTP connection error is caught here and re-raised as SophiaLLMError so the rest of the
        app has one clean catch target.

        The original exception is always chained via __cause__ so you can still
        inspect the root cause in logs or during debugging.
    """


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")
DEFAULT_MAX_TOKENS = int(os.environ.get("OPENROUTER_MAX_TOKENS", "4096"))

# Free-tier resilience. The free Gemma endpoint throttles hard (429) and can
# stall before the first token; a single failure used to kill the whole answer.
# We now retry transient failures with exponential back-off.
DEFAULT_MAX_RETRIES = int(os.environ.get("OPENROUTER_MAX_RETRIES", "3"))
DEFAULT_BACKOFF_BASE = float(os.environ.get("OPENROUTER_BACKOFF_BASE", "1.0"))


def _is_retryable_status(status_code: int) -> bool:
    """
    Mental Model:
        Which HTTP statuses are worth retrying. Transient server/throttle
        errors (408 timeout, 429 rate limit, any 5xx) are retryable; caller
        errors (400/401/403/404) are not — retrying them only wastes time.
    """
    return status_code == 408 or status_code == 429 or status_code >= 500


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------

class OpenRouterClient:
    """
    Mental Model:
        A wrapper around the OpenRouter API. Exposes standard chat and chat_stream.
        Isolates HTTP connection and streaming details, converting errors into SophiaLLMError.
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise SophiaLLMError(
                "OPENROUTER_API_KEY not found. Set it in your .env file or pass "
                "api_key= to OpenRouterClient(). See .env.example for the format."
            )
        self.base_url = base_url or os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        # Granular timeouts: fail fast on a dead connection (10s connect) but
        # stay patient while a slow free-tier model generates (90s read).
        timeout = httpx.Timeout(connect=10.0, read=90.0, write=10.0, pool=10.0)
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)
        logger.info("OpenRouterClient initialized. Default model: %s", DEFAULT_MODEL)

    # -- internal helpers --------------------------------------------------

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/SpiritualTech33/SophiaAI",
            "X-Title": "SophiaAI",
        }

    def _sleep_backoff(self, attempt: int) -> None:
        """Exponential back-off: base * 2**attempt (1s, 2s, 4s, ...)."""
        time.sleep(DEFAULT_BACKOFF_BASE * (2 ** attempt))

    def chat(
        self,
        messages: list[dict],
        model: str = DEFAULT_MODEL,
    ) -> str:
        """
        Send a conversation to the OpenRouter API and return the assistant's reply.
        """
        if not messages:
            raise ValueError(
                "messages must be a non-empty list of message dicts, got empty or None."
            )

        json_body = {
            "model": model,
            "messages": messages,
            "max_tokens": DEFAULT_MAX_TOKENS,
        }

        # Retry transient failures (429 / 5xx / timeout / empty) with back-off.
        for attempt in range(DEFAULT_MAX_RETRIES + 1):
            last = attempt == DEFAULT_MAX_RETRIES
            try:
                response = self._client.post(
                    "chat/completions",
                    headers=self._headers(),
                    json=json_body,
                )
            except httpx.HTTPError as error:
                if last:
                    raise SophiaLLMError(
                        f"OpenRouter API connection failed. Original error: {error}"
                    ) from error
                logger.warning(
                    "OpenRouter request error, retrying (attempt %d/%d): %s",
                    attempt + 1, DEFAULT_MAX_RETRIES, error,
                )
                self._sleep_backoff(attempt)
                continue

            if response.status_code == 200:
                data = response.json()
                content = None
                if data.get("choices"):
                    content = data["choices"][0].get("message", {}).get("content")
                if content is not None:
                    return content
                # Empty 200 — the free model sometimes returns no content. Retry.
                if last:
                    raise SophiaLLMError(
                        "OpenRouter API returned an empty response. No choices or content was None."
                    )
                logger.warning(
                    "OpenRouter empty response, retrying (attempt %d/%d).",
                    attempt + 1, DEFAULT_MAX_RETRIES,
                )
                self._sleep_backoff(attempt)
                continue

            # Non-200. Retry transient statuses; fail fast on caller errors.
            if _is_retryable_status(response.status_code) and not last:
                logger.warning(
                    "OpenRouter status %d, retrying (attempt %d/%d).",
                    response.status_code, attempt + 1, DEFAULT_MAX_RETRIES,
                )
                self._sleep_backoff(attempt)
                continue
            raise self._status_error(response)

        # Defensive: the loop always returns or raises above.
        raise SophiaLLMError("OpenRouter API failed after all retries.")

    def _status_error(self, response) -> SophiaLLMError:
        """Build a SophiaLLMError from a non-200 non-streaming response."""
        if response.status_code == 429:
            return SophiaLLMError(
                "OpenRouter API rate limit exceeded. Wait and retry."
            )
        try:
            error_data = response.json()
            msg = error_data.get("error", {}).get("message", response.text)
        except Exception:
            msg = response.text
        return SophiaLLMError(
            f"OpenRouter API returned status {response.status_code}. Details: {msg}"
        )

    def chat_stream(
        self,
        messages: list[dict],
        model: str = DEFAULT_MODEL,
    ) -> Iterator[str]:
        """
        Stream the assistant's reply token-by-token.
        """
        if not messages:
            raise ValueError(
                "messages must be a non-empty list of message dicts, got empty or None."
            )

        return self._stream_tokens(messages, model)

    def _stream_tokens(self, messages: list[dict], model: str) -> Iterator[str]:
        """
        Mental Model:
            Stream tokens, retrying transient failures with back-off — but
            ONLY before the first token is yielded. Once tokens have reached
            the caller, re-issuing the request would duplicate text, so a
            late failure is raised instead of retried. An empty completion
            (clean end with zero content) is treated as a transient failure
            and retried, since the free model occasionally returns nothing.
        """
        json_body = {
            "model": model,
            "messages": messages,
            "stream": True,
            "max_tokens": DEFAULT_MAX_TOKENS,
        }

        for attempt in range(DEFAULT_MAX_RETRIES + 1):
            last = attempt == DEFAULT_MAX_RETRIES
            tokens_yielded = 0
            retry_status = False
            try:
                with self._client.stream(
                    "POST",
                    "chat/completions",
                    headers=self._headers(),
                    json=json_body,
                ) as response:
                    if response.status_code != 200:
                        if _is_retryable_status(response.status_code) and not last:
                            logger.warning(
                                "OpenRouter stream status %d, retrying (attempt %d/%d).",
                                response.status_code, attempt + 1, DEFAULT_MAX_RETRIES,
                            )
                            retry_status = True
                        else:
                            raise self._stream_status_error(response)
                    else:
                        finish_reason = None
                        for line in response.iter_lines():
                            if not line.startswith("data: "):
                                continue
                            data_str = line[len("data: "):].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue
                            if not data.get("choices"):
                                continue
                            choice = data["choices"][0]
                            if choice.get("finish_reason") is not None:
                                finish_reason = choice["finish_reason"]
                            content = choice.get("delta", {}).get("content")
                            if content is not None:
                                tokens_yielded += 1
                                yield content
                        if finish_reason and finish_reason != "stop":
                            logger.info("Stream finished with reason=%s", finish_reason)
            except httpx.HTTPError as error:
                # A drop after tokens streamed can't be safely retried.
                if tokens_yielded == 0 and not last:
                    logger.warning(
                        "OpenRouter stream connection error, retrying (attempt %d/%d): %s",
                        attempt + 1, DEFAULT_MAX_RETRIES, error,
                    )
                    self._sleep_backoff(attempt)
                    continue
                raise SophiaLLMError(
                    f"OpenRouter API connection failed during streaming. "
                    f"Original error: {error}"
                ) from error

            if retry_status:
                self._sleep_backoff(attempt)
                continue

            if tokens_yielded == 0:
                # Clean end but no content — transient on the free tier. Retry.
                if not last:
                    logger.warning(
                        "OpenRouter empty stream, retrying (attempt %d/%d).",
                        attempt + 1, DEFAULT_MAX_RETRIES,
                    )
                    self._sleep_backoff(attempt)
                    continue
                raise SophiaLLMError(
                    f"OpenRouter API returned an empty response after "
                    f"{DEFAULT_MAX_RETRIES + 1} attempts."
                )
            return

    def _stream_status_error(self, response) -> SophiaLLMError:
        """Build a SophiaLLMError from a non-200 streaming response."""
        if response.status_code == 429:
            return SophiaLLMError(
                "OpenRouter API rate limit exceeded during streaming. Wait and retry."
            )
        try:
            error_body = response.read().decode("utf-8")
            error_data = json.loads(error_body)
            msg = error_data.get("error", {}).get("message", error_body)
        except Exception:
            msg = f"HTTP error {response.status_code}"
        return SophiaLLMError(f"OpenRouter API streaming error: {msg}")
