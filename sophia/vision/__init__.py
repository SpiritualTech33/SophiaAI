"""
sophia.vision
=============
The vision tool — Sophia's eyes for seeing attached images.

One pure function behind one interface (one-swap-point boundary, CLAUDE.md):
    encode_image_content(data, mime_type) -> dict  # build a multimodal content part

The chat orchestrator wires this deterministically today; the future agent
loop calls the same function as a tool. Nothing else imports the internals.
"""

from __future__ import annotations

from sophia.vision.encoder import (
    ALLOWED_IMAGE_MIME_TYPES,
    MAX_IMAGE_SIZE_BYTES,
    encode_image_content,
)
from sophia.vision.errors import (
    ImageTooLargeError,
    SophiaVisionError,
    UnsupportedImageTypeError,
)

__all__ = [
    "encode_image_content",
    "ALLOWED_IMAGE_MIME_TYPES",
    "MAX_IMAGE_SIZE_BYTES",
    "SophiaVisionError",
    "ImageTooLargeError",
    "UnsupportedImageTypeError",
]
