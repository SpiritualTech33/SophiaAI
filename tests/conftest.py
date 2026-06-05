"""
Shared test fixtures for SophiaAI endpoint tests.

Executive Brief:
    Builds a lightweight FastAPI test app with in-memory SQLite,
    no heavy AI objects, and a known JWT secret. Every endpoint
    test file imports these fixtures via pytest auto-discovery.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from sophia.app.schemas import TokenResponse
from sophia.db.database import Base, build_session_factory
import sophia.db.models  # noqa: F401 — registers ORM models on Base.metadata

TEST_JWT_SECRET = "test-secret-for-sophia-phase-11"


@pytest.fixture()
def test_app(tmp_path):
    """Create a FastAPI app with in-memory SQLite and no AI objects."""
    # StaticPool ensures all connections share the same in-memory database
    # so the schema created by create_all is visible to every session.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = build_session_factory(engine)

    app = FastAPI()
    app.state.session_factory = session_factory
    app.state.jwt_secret = TEST_JWT_SECRET
    # Uploads land in a per-test temp dir so the repo is never touched.
    app.state.upload_dir = str(tmp_path / "uploads")

    from sophia.core.corpus import CorpusLibrary
    app.state.corpus = CorpusLibrary()

    from sophia.app.routers import auth, chat, corpus, files
    app.include_router(auth.router)
    app.include_router(chat.router)
    app.include_router(corpus.router)
    app.include_router(files.router)

    yield app

    engine.dispose()


@pytest.fixture()
def client(test_app):
    """TestClient bound to the test app."""
    with TestClient(test_app) as c:
        yield c


def register_and_get_token(client: TestClient, email: str = "test@sophia.ai", password: str = "wisdom123") -> str:
    """Helper: register a user and return the access token."""
    response = client.post("/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201
    return response.json()["access_token"]
