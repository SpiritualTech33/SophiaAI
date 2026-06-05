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

DEFAULT_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash")
DEFAULT_MAX_TOKENS = int(os.environ.get("OPENROUTER_MAX_TOKENS", "4096"))


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
        self._client = httpx.Client(base_url=self.base_url, timeout=60.0)
        logger.info("OpenRouterClient initialized. Default model: %s", DEFAULT_MODEL)

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

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/SpiritualTech33/SophiaAI",
            "X-Title": "SophiaAI",
        }
        json_body = {
            "model": model,
            "messages": messages,
            "max_tokens": DEFAULT_MAX_TOKENS,
        }

        try:
            response = self._client.post(
                "chat/completions",
                headers=headers,
                json=json_body,
            )
            if response.status_code == 429:
                raise SophiaLLMError(
                    "OpenRouter API rate limit exceeded. Wait and retry."
                )
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    msg = error_data.get("error", {}).get("message", response.text)
                except Exception:
                    msg = response.text
                raise SophiaLLMError(
                    f"OpenRouter API returned status {response.status_code}. "
                    f"Details: {msg}"
                )

            data = response.json()
            if not data.get("choices") or data["choices"][0].get("message", {}).get("content") is None:
                raise SophiaLLMError(
                    "OpenRouter API returned an empty response. No choices or content was None."
                )

            return data["choices"][0]["message"]["content"]
        except httpx.HTTPError as error:
            raise SophiaLLMError(
                f"OpenRouter API connection failed. Original error: {error}"
            ) from error

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
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/SpiritualTech33/SophiaAI",
            "X-Title": "SophiaAI",
        }
        json_body = {
            "model": model,
            "messages": messages,
            "stream": True,
            "max_tokens": DEFAULT_MAX_TOKENS,
        }

        try:
            with self._client.stream(
                "POST",
                "chat/completions",
                headers=headers,
                json=json_body,
            ) as response:
                if response.status_code == 429:
                    raise SophiaLLMError(
                        "OpenRouter API rate limit exceeded during streaming. Wait and retry."
                    )
                if response.status_code != 200:
                    try:
                        error_body = response.read().decode("utf-8")
                        error_data = json.loads(error_body)
                        msg = error_data.get("error", {}).get("message", error_body)
                    except Exception:
                        msg = f"HTTP error {response.status_code}"
                    raise SophiaLLMError(
                        f"OpenRouter API streaming error: {msg}"
                    )

                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[len("data: "):].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content")
                                if content is not None:
                                    yield content
                        except json.JSONDecodeError:
                            pass
        except httpx.HTTPError as error:
            raise SophiaLLMError(
                f"OpenRouter API connection failed during streaming. "
                f"Original error: {error}"
            ) from error
