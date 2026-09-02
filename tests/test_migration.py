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


# --- GRS-0246: the JSON column becomes a keyed join table --------------------------------------


def _at_revision(engine, revision: str) -> list[str]:
    """Bring a database to one specific migration rather than to head, returning its log messages.

    `configure_logger=False` stops `env.py` calling `fileConfig`, which would otherwise replace the
        process's logging configuration mid-upgrade and discard the handler below. Without it this
        captures nothing and every assertion against the result passes vacuously.
    """
    import logging
    from pathlib import Path

    from alembic import command
    from alembic.config import Config

    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.attributes["configure_logger"] = False

    captured: list[str] = []

    class _Collect(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured.append(record.getMessage())

    handler = _Collect(level=logging.INFO)
    logger = logging.getLogger("alembic.runtime.migration")
    logger.addHandler(handler)
    try:
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, revision)
    finally:
        logger.removeHandler(handler)
    return captured


def _insert(c, table: str, **values) -> None:
    """Insert a row, filling every other NOT NULL column with a benign placeholder.

    The schema at revision 0042 is large and this test cares about one column, so listing the rest
    by hand would make it brittle to unrelated schema changes.
    """
    from sqlalchemy import text

    info = c.execute(text(f"PRAGMA table_info({table})")).fetchall()
    for _cid, name, coltype, notnull, default, _pk in info:
        if name in values or not notnull or default is not None:
            continue
        t = (coltype or "").upper()
        if "INT" in t:
            values[name] = 0
        elif "BOOL" in t:
            values[name] = 1
        elif "DATE" in t or "TIME" in t:
            values[name] = "2026-01-01 00:00:00"
        else:
            values[name] = "x"
    cols = ", ".join(values)
    binds = ", ".join(f":{k}" for k in values)
    c.execute(text(f"INSERT INTO {table} ({cols}) VALUES ({binds})"), values)


def _seed_legacy_engagement(engine, *, dead_ids: list[str]) -> tuple[str, str]:
    """One consultant, prospect, assessment and engagement in the pre-0043 shape.

    The engagement's JSON column lists the live assessment followed by `dead_ids` — ids naming no
    assessment, exactly what five staging engagements carried.
    """
    import json
    import uuid

    cid, aid, pid, eid = (uuid.uuid4().hex for _ in range(4))
    with engine.begin() as c:
        _insert(c, "consultants", id=cid, email="legacy@b.c", full_name="Legacy")
        _insert(c, "assessments", id=aid, owner_consultant_id=cid, subject="Live Co")
        _insert(c, "prospects", id=pid, owner_consultant_id=cid, company_name="Live Co")
        _insert(
            c,
            "engagements",
            id=eid,
            owner_consultant_id=cid,
            prospect_id=pid,
            title="Legacy — delivery",
            assessment_ids_json=json.dumps([aid, *dead_ids]),
            deliverables_json="[]",
        )
    return eid, aid


def test_0043_migrates_good_links_and_drops_dangling_ones() -> None:
    """Scope 3. A live link survives; a link naming a deleted assessment is dropped and REPORTED.

    Data written before the foreign key existed is the only way a dangling reference can still
    arise, so this is where that case is tested.
    """
    import uuid

    from sqlalchemy import text

    engine = _memory_engine()
    _at_revision(engine, "0042_curated_target_names")
    dead = uuid.uuid4().hex
    engagement_id, live = _seed_legacy_engagement(engine, dead_ids=[dead])

    messages = _at_revision(engine, "head")

    with engine.begin() as c:
        rows = c.execute(
            text(
                "SELECT assessment_id FROM engagement_assessments WHERE engagement_id = :e "
                "ORDER BY position"
            ),
            {"e": engagement_id},
        ).fetchall()
    assert [r[0] for r in rows] == [live], (
        "the live link must survive and the dangling one must not be written — a keyed table "
        "cannot hold it"
    )

    joined = " ".join(messages)
    assert "dropped 1 DANGLING" in joined
    assert dead in joined, "a dropped link must be named, not merely counted"


def test_0043_removes_the_json_column() -> None:
    engine = _memory_engine()
    run_migrations(engine)
    assert "assessment_ids_json" not in _schema(engine)["engagements"]
    assert "engagement_assessments" in _schema(engine)
