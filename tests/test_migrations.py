"""Verify the Alembic initial migration builds and drops the full schema.

Mental Model
------------
We run the real migration scripts against a throwaway SQLite file, never the
dev database. ``upgrade head`` must create the three live tables; ``downgrade
base`` must remove them again. This proves the migration is reversible and
matches the models.

Isolation note: alembic/env.py reads SOPHIA_DB_URL at run-env time and calls
``config.set_main_option`` — which overwrites whatever URL the caller placed
on the Config object. The fixture therefore sets SOPHIA_DB_URL to the same
tmp-path URL so env.py and the Config agree on the target database.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TABLES = {"users", "conversations", "messages", "user_files"}


@pytest.fixture
def alembic_config(tmp_path: Path) -> Config:
    """Alembic config pointed at a throwaway DB inside the test's tmp dir.

    Also sets SOPHIA_DB_URL so alembic/env.py's os.environ read agrees with
    the URL placed on the Config object. Without this, env.py overwrites the
    fixture URL with the default sophia_memory.db path.
    """
    db_path = tmp_path / "migration_test.db"
    db_url = f"sqlite:///{db_path}"
    cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    os.environ["SOPHIA_DB_URL"] = db_url
    yield cfg
    os.environ.pop("SOPHIA_DB_URL", None)


def _table_names(cfg: Config) -> set[str]:
    """Reflect the migrated DB and return its non-alembic table names."""
    url = cfg.get_main_option("sqlalchemy.url")
    engine = create_engine(url)
    tables = set(inspect(engine).get_table_names())
    engine.dispose()
    return tables - {"alembic_version"}


def test_upgrade_head_creates_all_tables(alembic_config: Config) -> None:
    """upgrade head produces exactly the application tables."""
    command.upgrade(alembic_config, "head")
    assert _table_names(alembic_config) == EXPECTED_TABLES


def test_downgrade_base_drops_all_tables(alembic_config: Config) -> None:
    """downgrade base removes all application tables, leaving a clean slate."""
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "base")
    assert _table_names(alembic_config) == set()
