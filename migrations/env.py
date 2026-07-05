"""Alembic environment.

Migrations are the schema source of truth (GRS-0006 retires `create_all` from the app path). This
env supports two callers with one code path:

- **the app / tests** inject a live SQLAlchemy connection via ``config.attributes['connection']``
  (see ``grassmarket.data.database.run_migrations``) so migrations run on the SAME engine —
  the shared in-memory SQLite in the test suite;
- **the CLI** (`alembic upgrade head`) has no connection, so the URL comes from the app settings —
  migrations, the app, and the tests all agree on one schema and one connection string.

`render_as_batch` is on for SQLite so future ALTERs work on a store that lacks native ALTER.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from grassmarket.data import models  # noqa: F401  (register the ORM models on Base.metadata)
from grassmarket.data.database import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _settings_url() -> str:
    # Imported lazily so a connection-injected run never needs app settings (or env vars).
    from grassmarket.config import get_settings

    return get_settings().database_url


def run_migrations_offline() -> None:
    context.configure(
        url=_settings_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _run(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        render_as_batch=connection.dialect.name == "sqlite",
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    injected = config.attributes.get("connection", None)
    if injected is not None:
        _run(injected)
        return
    connectable = engine_from_config(
        {"sqlalchemy.url": _settings_url()}, prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with connectable.connect() as connection:
        _run(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
