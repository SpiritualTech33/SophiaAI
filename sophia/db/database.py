"""
Database engine, session factory, and declarative base.

Executive Brief:
    Single source of truth for SQLAlchemy configuration.
    All database access in the project flows through the engine
    and session factory created here.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DEFAULT_DATABASE_URL = "sqlite:///./sophia_memory.db"


class Base(DeclarativeBase):
    """Base class for all ORM models in SophiaAI."""


def build_engine(database_url: str = DEFAULT_DATABASE_URL, echo: bool = False) -> Engine:
    """
    Executive Brief:
        Create a SQLAlchemy engine for the given database URL.

    Args:
        database_url: SQLAlchemy connection string. Defaults to local SQLite file.
        echo: If True, log all SQL statements to stdout. Use only during development.

    Returns:
        Engine: A configured SQLAlchemy engine.
    """
    return create_engine(
        database_url,
        echo=echo,
        connect_args={"check_same_thread": False},
    )


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    """
    Executive Brief:
        Create a session factory bound to the given engine.

    Args:
        engine: The SQLAlchemy engine to bind sessions to.

    Returns:
        sessionmaker: A callable that produces new Session instances.
    """
    return sessionmaker(bind=engine)
