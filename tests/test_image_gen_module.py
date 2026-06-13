"""
Unit tests for sophia.image_gen.generator.

Strategy: mock httpx.post so no network call is made, and set HF_TOKEN in the
environment so the token guard passes.

Run: pytest tests/test_image_gen_module.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.image_gen import ImageGenerationError, generate_image


@pytest.fixture(autouse=True)
def _hf_token(monkeypatch):
    """Every test runs with a token present unless it overrides this."""
    monkeypatch.setenv("HF_TOKEN", "hf_test_token")


@patch("sophia.image_gen.generator.httpx.post")
def test_generate_image_returns_bytes(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"\xff\xd8\xff\xe0fake-jpeg-bytes"
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    result = generate_image("a cosmic owl made of stars")

    assert result == b"\xff\xd8\xff\xe0fake-jpeg-bytes"
    called_url = mock_post.call_args[0][0]
    assert "FLUX.1-schnell" in called_url
    # The prompt rides in the JSON body, and the token in the Authorization header.
    assert mock_post.call_args.kwargs["json"] == {"inputs": "a cosmic owl made of stars"}
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer hf_test_token"


@patch("sophia.image_gen.generator.httpx.post")
def test_generate_image_raises_on_http_error(mock_post):
    mock_post.side_effect = httpx.HTTPError("boom")

    with pytest.raises(ImageGenerationError):
        generate_image("a cosmic owl")


@patch("sophia.image_gen.generator.httpx.post")
def test_generate_image_raises_on_non_200(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "server error", request=MagicMock(), response=mock_response
    )
    mock_post.return_value = mock_response

    with pytest.raises(ImageGenerationError):
        generate_image("a cosmic owl")


def test_generate_image_raises_when_token_missing(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)

    with pytest.raises(ImageGenerationError):
        generate_image("a cosmic owl")


def test_generate_image_rejects_empty_prompt():
    with pytest.raises(ValueError):
        generate_image("")
