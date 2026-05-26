"""
SophiaAI — Database package.

Public API:
    Base                 — SQLAlchemy DeclarativeBase for all models.
    build_engine         — Creates a SQLAlchemy engine from a URL.
    build_session_factory — Creates a sessionmaker bound to an engine.

Author: Cosmos De La Cruz — SophiaAI Phase 9
"""

from sophia.db.database import Base, build_engine, build_session_factory

__all__ = ["Base", "build_engine", "build_session_factory"]
