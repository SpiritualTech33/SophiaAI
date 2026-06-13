"""
Unit tests for sophia.vision.encoder.

Strategy: pure-function tests, no network, no DB. Mirrors
tests/test_files_module.py in shape.

Run: pytest tests/test_vision_module.py -v
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.vision import (
    MAX_IMAGE_SIZE_BYTES,
    ImageTooLargeError,
    UnsupportedImageTypeError,
    encode_image_content,
)


def test_encode_image_content_returns_data_uri():
    data = b"\x89PNG\r\n\x1a\nfake-png-bytes"
    content = encode_image_content(data, "image/png")

    expected_b64 = base64.b64encode(data).decode("ascii")
    assert content == {
        "type": "image_url",
        "image_url": {"url": f"data:image/png;base64,{expected_b64}"},
    }


def test_encode_image_content_accepts_jpeg_webp_gif():
    data = b"bytes"
    for mime in ("image/jpeg", "image/webp", "image/gif"):
        content = encode_image_content(data, mime)
        assert content["image_url"]["url"].startswith(f"data:{mime};base64,")


def test_encode_image_content_rejects_unsupported_mime():
    with pytest.raises(UnsupportedImageTypeError):
        encode_image_content(b"data", "application/pdf")


def test_encode_image_content_rejects_oversize():
    big = b"x" * (MAX_IMAGE_SIZE_BYTES + 1)
    with pytest.raises(ImageTooLargeError):
        encode_image_content(big, "image/png")
