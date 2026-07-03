"""SQLAlchemy engine/session plumbing.

The app uses managed Postgres on Railway (via `DATABASE_URL`) and SQLite locally / in CI.
Schema for Loop 0 is created with `create_all`; Alembic migrations become the source of truth
as the schema grows (Loop 1+). Kept deliberately small — the interesting logic is in
`repository.py`, not here.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


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
    """Create every table. Loop 0 bootstrap and the test fixture path."""
    # Import models for their side effect of registering on Base.metadata.
    from grassmarket.data import models  # noqa: F401

    Base.metadata.create_all(engine)


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
