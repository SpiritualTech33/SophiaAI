"""
encoder.py
==========
SophiaAI — Vision tool: turns image bytes into an LLM-ready content part.

Mental Model:
    One public function, `encode_image_content(data, mime_type) -> dict`,
    turns raw image bytes into the OpenAI-format multimodal content part
    (`{"type": "image_url", "image_url": {"url": "data:<mime>;base64,..."}}`)
    that OpenRouter accepts inline in a user message. Validates mime type and
    size up front so a bad attachment fails fast with a precise error.

Philosophy: ZenCode PRO + CEO of Water — explicit, bulletproof, one job each.
"""

from __future__ import annotations

import base64

from sophia.vision.errors import ImageTooLargeError, UnsupportedImageTypeError

# 10 MB ceiling — matches sophia.files.parsers.MAX_UPLOAD_BYTES.
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024

# The only mime types we accept for vision input.
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def encode_image_content(data: bytes, mime_type: str) -> dict:
    """
    Mental Model:
        The single entry point for turning an image upload into a multimodal
        message content part. Validates size and mime type, then base64-encodes
        the bytes into a data URI.

    Args:
        data: Raw image bytes.
        mime_type: The image's mime type (e.g. "image/png").

    Returns:
        dict: An OpenAI-format `image_url` content part.

    Raises:
        ImageTooLargeError: data exceeds MAX_IMAGE_SIZE_BYTES.
        UnsupportedImageTypeError: mime_type is not on the allowlist.
    """
    if len(data) > MAX_IMAGE_SIZE_BYTES:
        raise ImageTooLargeError(
            f"Image exceeds the {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)} MB limit."
        )

    if mime_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise UnsupportedImageTypeError(
            f"Unsupported image type '{mime_type}'. "
            f"Accepted: {', '.join(sorted(ALLOWED_IMAGE_MIME_TYPES))}."
        )

    encoded = base64.b64encode(data).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime_type};base64,{encoded}"},
    }
