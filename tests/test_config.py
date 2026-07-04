"""Config tests — fail-loud behaviour and the managed-Postgres URL normalisation.

The Postgres URLs below are synthetic (`u:p@h/d`); the `# pragma: allowlist secret` markers tell
the secret-scan hook so, since its high-signal Postgres pattern scans test files too.
"""

from __future__ import annotations

import pytest

from grassmarket.config import Settings

_SECRET = "a-strong-enough-secret-for-tests-32chars-minimum-xxxxx"  # pragma: allowlist secret


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("postgres://u:p@h/d", "postgresql+psycopg://u:p@h/d"),  # pragma: allowlist secret
        ("postgresql://u:p@h/d", "postgresql+psycopg://u:p@h/d"),  # pragma: allowlist secret
        # Already-qualified and SQLite URLs are left untouched.
        (
            "postgresql+psycopg://u:p@h/d",
            "postgresql+psycopg://u:p@h/d",
        ),  # pragma: allowlist secret
        ("sqlite+pysqlite:///./local.db", "sqlite+pysqlite:///./local.db"),
    ],
)
def test_database_url_scheme_normalised(given: str, expected: str) -> None:
    settings = Settings(env="ci", jwt_secret=_SECRET, database_url=given)
    assert settings.database_url == expected


def test_production_refuses_sqlite() -> None:
    with pytest.raises(ValueError):
        Settings(env="production", jwt_secret=_SECRET, database_url="sqlite+pysqlite:///./x.db")


def test_production_refuses_short_secret() -> None:
    with pytest.raises(ValueError):
        Settings(
            env="production",
            jwt_secret="too-short",  # pragma: allowlist secret
            database_url="postgresql://u:p@h/d",  # pragma: allowlist secret
        )


def test_production_accepts_postgres_and_strong_secret() -> None:
    settings = Settings(
        env="production",
        jwt_secret=_SECRET,
        database_url="postgresql://u:p@h/d",  # pragma: allowlist secret
    )
    assert settings.is_production
    assert settings.database_url.startswith("postgresql+psycopg://")
