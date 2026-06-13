"""
Endpoint tests for image generation.

Strategy: mock sophia.app.routers.images.generate_image so no network call is
made. Generated images are stored as UserFile records and served via
/api/files/{id}/raw, exactly like uploads.

Run: pytest tests/test_app_images.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.image_gen import ImageGenerationError
from tests.conftest import register_and_get_token


@pytest.fixture()
def auth_client(client):
    token = register_and_get_token(client)
    return client, token


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@patch("sophia.app.routers.images.generate_image")
def test_generate_image_returns_file_metadata(mock_generate, auth_client):
    client, token = auth_client
    mock_generate.return_value = b"\xff\xd8\xff\xe0fake-jpeg-bytes"

    response = client.post(
        "/api/images/generate",
        json={"prompt": "a cosmic owl made of stars"},
        headers=_auth_header(token),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["mime"] == "image/jpeg"
    assert data["url"] == f"/api/files/{data['id']}/raw"
    mock_generate.assert_called_once_with("a cosmic owl made of stars")


@patch("sophia.app.routers.images.generate_image")
def test_generate_image_result_is_servable_via_raw(mock_generate, auth_client):
    client, token = auth_client
    mock_generate.return_value = b"\xff\xd8\xff\xe0fake-jpeg-bytes"

    file_id = client.post(
        "/api/images/generate",
        json={"prompt": "a cosmic owl"},
        headers=_auth_header(token),
    ).json()["id"]

    raw = client.get(f"/api/files/{file_id}/raw", headers=_auth_header(token))
    assert raw.status_code == 200
    assert raw.headers["content-type"] == "image/jpeg"
    assert raw.content == b"\xff\xd8\xff\xe0fake-jpeg-bytes"


@patch("sophia.app.routers.images.generate_image")
def test_generate_image_provider_error_returns_502(mock_generate, auth_client):
    client, token = auth_client
    mock_generate.side_effect = ImageGenerationError("Hugging Face is down")

    response = client.post(
        "/api/images/generate",
        json={"prompt": "a cosmic owl"},
        headers=_auth_header(token),
    )
    assert response.status_code == 502


def test_generate_image_requires_auth(client):
    response = client.post("/api/images/generate", json={"prompt": "a cosmic owl"})
    assert response.status_code == 401


def test_generate_image_rejects_empty_prompt(auth_client):
    client, token = auth_client
    response = client.post(
        "/api/images/generate",
        json={"prompt": "   "},
        headers=_auth_header(token),
    )
    assert response.status_code == 422
