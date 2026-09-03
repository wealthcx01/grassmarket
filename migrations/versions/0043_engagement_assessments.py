"""Replace engagements.assessment_ids_json with a real join table (GRS-0246).

The JSON column expressed "which assessments this engagement draws on" with no foreign key, so
`delete_assessment` — careful and correct about every FK — never saw those links. Assessments were
deleted and five staging engagements went on referencing them for a month.

The backfill drops entries that name no assessment, because they cannot be written into a keyed
table. Every dropped entry is REPORTED, never silently discarded: a dangling reference is data
loss that already happened, and the migration log is the record of it.

Revision ID: 0043_engagement_assessments
Revises: 0042_curated_target_names
"""

from __future__ import annotations

import json
import logging

import sqlalchemy as sa
from alembic import op

revision = "0043_engagement_assessments"
down_revision = "0042_curated_target_names"
branch_labels = None
depends_on = None

_log = logging.getLogger("alembic.runtime.migration")


def upgrade() -> None:
    op.create_table(
        "engagement_assessments",
        sa.Column(
            "engagement_id",
            sa.Uuid(),
            sa.ForeignKey("engagements.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "assessment_id",
            sa.Uuid(),
            sa.ForeignKey("assessments.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_engagement_assessments_assessment_id", "engagement_assessments", ["assessment_id"]
    )

    bind = op.get_bind()
    live = {str(r[0]) for r in bind.execute(sa.text("SELECT id FROM assessments")).fetchall()}
    rows = bind.execute(
        sa.text("SELECT id, title, assessment_ids_json FROM engagements")
    ).fetchall()

    inserted = 0
    dropped: list[tuple[str, str, str]] = []
    for engagement_id, title, raw in rows:
        try:
            linked = json.loads(raw or "[]")
        except (TypeError, ValueError):
            _log.warning("GRS-0246: engagement %s has unparseable links; treating as none", title)
            continue
        position = 0
        for aid in linked:
            if str(aid) not in live:
                dropped.append((str(engagement_id), str(title), str(aid)))
                continue
            bind.execute(
                sa.text(
                    "INSERT INTO engagement_assessments "
                    "(engagement_id, assessment_id, position) VALUES (:e, :a, :p)"
                ),
                {"e": str(engagement_id), "a": str(aid), "p": position},
            )
            position += 1
            inserted += 1

    _log.info("GRS-0246: migrated %d engagement-assessment links", inserted)
    if dropped:
        # Loud, itemised, and not fatal: these links were already broken before this migration ran.
        # Refusing to migrate would leave the database in the shape that caused the bug.
        _log.warning(
            "GRS-0246: dropped %d DANGLING link(s) that named no assessment:", len(dropped)
        )
        for engagement_id, title, aid in dropped:
            _log.warning("  engagement %s (%s) -> missing assessment %s", engagement_id, title, aid)

    op.drop_column("engagements", "assessment_ids_json")


def downgrade() -> None:
    op.add_column(
        "engagements",
        sa.Column("assessment_ids_json", sa.Text(), nullable=False, server_default="[]"),
    )
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT engagement_id, assessment_id FROM engagement_assessments "
            "ORDER BY engagement_id, position"
        )
    ).fetchall()
    grouped: dict[str, list[str]] = {}
    for engagement_id, assessment_id in rows:
        grouped.setdefault(str(engagement_id), []).append(str(assessment_id))
    for engagement_id, ids in grouped.items():
        bind.execute(
            sa.text("UPDATE engagements SET assessment_ids_json = :j WHERE id = :e"),
            {"j": json.dumps(ids), "e": engagement_id},
        )
    op.drop_index("ix_engagement_assessments_assessment_id", table_name="engagement_assessments")
    op.drop_table("engagement_assessments")
