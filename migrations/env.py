"""Alembic environment.

The URL and target metadata come from the app itself — `grassmarket.config.get_settings()` and
`grassmarket.data.database.Base` — so migrations, the app, and the tests all agree on one schema
and one connection string. Loop 1 authors the first migration with `alembic revision
--autogenerate`; Loop 0 ships the machinery (closing feasibility defect D8's "no Alembic").
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from grassmarket.config import get_settings
from grassmarket.data import models  # noqa: F401  (register the ORM models on Base.metadata)
from grassmarket.data.database import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
