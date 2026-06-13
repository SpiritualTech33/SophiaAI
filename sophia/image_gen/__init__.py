"""
sophia.image_gen
================
The image generation tool — Sophia's hands for painting pictures.

One pure function behind one interface (one-swap-point boundary, CLAUDE.md):
    generate_image(prompt) -> bytes  # text prompt -> PNG bytes

The images router wires this deterministically today; the future agent loop
calls the same function as a tool. Nothing else imports the internals.
"""

from __future__ import annotations

from sophia.image_gen.generator import ImageGenerationError, generate_image

__all__ = [
    "generate_image",
    "ImageGenerationError",
]
