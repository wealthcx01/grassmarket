"""SQLAlchemy engine/session plumbing.

The app uses managed Postgres on Railway (via `DATABASE_URL`) and SQLite locally / in CI.
**Alembic migrations are the schema source of truth** (GRS-0006): the app applies them at startup
via :func:`run_migrations`. `create_all` remains only for throwaway in-memory test databases where a
migration round-trip would add nothing. Kept deliberately small — the interesting logic is in
`repository.py`, not here.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

_ALEMBIC_INI = Path(__file__).resolve().parents[3] / "alembic.ini"


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def make_engine(database_url: str) -> Engine:
    """Build an engine for the given URL. SQLite needs the single-thread guard relaxed for the
    threaded test/dev server; Postgres uses defaults."""
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(database_url, future=True, connect_args=connect_args)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def create_all(engine: Engine) -> None:
    """Create every table directly from the models. Retained ONLY for throwaway in-memory test
    databases; the app and real deployments apply the schema via :func:`run_migrations`."""
    # Import models for their side effect of registering on Base.metadata.
    from grassmarket.data import models  # noqa: F401

    Base.metadata.create_all(engine)


def run_migrations(engine: Engine) -> None:
    """Bring a database to the latest schema by applying the Alembic migrations — the source of
    truth (GRS-0006, replacing `create_all` on the app path). Runs on the GIVEN engine's connection,
    so it works with any store the app uses, including the shared in-memory SQLite in tests."""
    config = Config(str(_ALEMBIC_INI))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    """A transactional session scope: commit on success, roll back on error, always close."""
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
