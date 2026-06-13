"""
generator.py
============
SophiaAI — Image generation tool via the Hugging Face Inference API.

Mental Model:
    One public function, `generate_image(prompt) -> bytes`, turns a text
    prompt into image bytes. A POST to
    `https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell`
    with `{"inputs": prompt}` and a Bearer token returns the generated image
    directly (Content-Type: image/jpeg). Any connection failure, missing
    token, or non-2xx response is wrapped in `ImageGenerationError` so the
    rest of the app has one clean catch target.

Philosophy: ZenCode PRO + CEO of Water — explicit, bulletproof, one job each.
"""

from __future__ import annotations

import logging
import os

import httpx
from dotenv import load_dotenv

# Load .env once at import time so callers can override via os.environ later.
load_dotenv()

logger = logging.getLogger("sophia.image_gen.generator")

HF_INFERENCE_URL = (
    "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
)

# Generous timeout — image generation is slower than a text completion.
_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)


class ImageGenerationError(Exception):
    """
    Mental Model:
        The single exception type that escapes this module. A missing
        HF_TOKEN, a Hugging Face API error, or an HTTP connection error is
        caught here and re-raised as ImageGenerationError, with the original
        exception chained via __cause__ for debugging.
    """


def generate_image(prompt: str) -> bytes:
    """
    Mental Model:
        The single entry point for generating an image from a text prompt.

    Args:
        prompt: A non-empty description of the image to generate.

    Returns:
        bytes: The generated image (JPEG).

    Raises:
        ValueError: prompt is empty or whitespace-only.
        ImageGenerationError: HF_TOKEN is missing, or the request failed or
            returned a non-2xx status.
    """
    if not prompt or not prompt.strip():
        raise ValueError("prompt must be a non-empty string.")

    token = os.environ.get("HF_TOKEN")
    if not token:
        raise ImageGenerationError(
            "HF_TOKEN not found. Set it in your .env file to enable image generation."
        )

    try:
        response = httpx.post(
            HF_INFERENCE_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"inputs": prompt},
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise ImageGenerationError(
            f"Image generation failed for prompt {prompt!r}. Original error: {error}"
        ) from error

    return response.content
