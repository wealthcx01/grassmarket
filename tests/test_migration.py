"""Migration tests (GRS-0006) — Alembic is the schema source of truth and matches the models.

`run_migrations` must build exactly the schema the ORM models declare (tables + columns), so the
migration path the app uses is faithful. `scoring_runs` in particular must exist with its owner
scoping column.
"""

from __future__ import annotations

from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool

from grassmarket.data.database import create_all, run_migrations


def _memory_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )


def _schema(engine) -> dict[str, list[str]]:
    insp = inspect(engine)
    return {
        table: sorted(col["name"] for col in insp.get_columns(table))
        for table in insp.get_table_names()
        if table != "alembic_version"
    }


def test_migration_matches_the_models() -> None:
    migrated = _memory_engine()
    run_migrations(migrated)
    created = _memory_engine()
    create_all(created)
    assert _schema(migrated) == _schema(created)


def test_migration_creates_scoring_runs_with_scoping_column() -> None:
    engine = _memory_engine()
    run_migrations(engine)
    schema = _schema(engine)
    assert "scoring_runs" in schema
    assert "owner_consultant_id" in schema["scoring_runs"]
    assert "content_hash" in schema["scoring_runs"]
    assert {"consultants", "invitations", "prospects"} <= set(schema)
