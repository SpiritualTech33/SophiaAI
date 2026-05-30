"""
Endpoint tests for the corpus browsing API (Phase 15).

Strategy: the test app attaches a real CorpusLibrary (cheap JSON read) in
conftest, so these exercise the HTTP + auth layer against the actual manifest.

Run: pytest tests/test_app_corpus.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.conftest import register_and_get_token


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_list_corpus_requires_auth(client):
    """GET /api/corpus without a token returns 401."""
    assert client.get("/api/corpus").status_code == 401


def test_list_corpus_returns_documents(client):
    """GET /api/corpus returns the document metadata list."""
    token = register_and_get_token(client)
    response = client.get("/api/corpus", headers=_auth_header(token))
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 137
    assert {"id", "title", "author", "year", "words", "pillar"} <= docs[0].keys()


def test_get_document_returns_text(client):
    """GET /api/corpus/{id} returns the full markdown of a document."""
    token = register_and_get_token(client)
    headers = _auth_header(token)

    listing = client.get("/api/corpus", headers=headers).json()
    doc_id = listing[0]["id"]

    response = client.get(f"/api/corpus/{doc_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id
    assert len(data["text"]) > 0


def test_get_unknown_document_returns_404(client):
    """GET /api/corpus/{unknown} returns 404."""
    token = register_and_get_token(client)
    response = client.get("/api/corpus/not-a-real-id", headers=_auth_header(token))
    assert response.status_code == 404
