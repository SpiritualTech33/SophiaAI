"""
Unit tests for sophia.db.

Strategy: every test uses an in-memory SQLite database via a fresh engine.
No disk I/O, no leftover files. Each test is fully isolated.

Run: pytest tests/test_database.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import inspect, text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sophia.db.database import Base, build_engine, build_session_factory


def test_build_engine_creates_working_engine():
    """build_engine returns an engine that can connect to in-memory SQLite."""
    engine = build_engine("sqlite:///:memory:")
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar() == 1
    engine.dispose()


def test_build_session_factory_returns_callable():
    """build_session_factory returns a sessionmaker bound to the engine."""
    engine = build_engine("sqlite:///:memory:")
    session_factory = build_session_factory(engine)
    session = session_factory()
    assert session.bind is engine
    session.close()
    engine.dispose()


def test_base_has_metadata():
    """Base class exposes metadata for create_all."""
    assert Base.metadata is not None
