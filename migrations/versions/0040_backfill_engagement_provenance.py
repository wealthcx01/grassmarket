"""Derive provenance for engagements that predate the column.

GRS-0241. Migration `0039` added `engagements.provenance` defaulting to `production`, which is the
right default for a new column and the wrong answer for rows that already existed: on staging it
made all 12 engagements production, including the seeded showcase ones, so the cleanup script
correctly refused to touch a single duplicate. The seed could not fix it either — it is idempotent
and skips anything already seeded, so it never restamps.

**This is a derivation, not a guess.** `create_engagement` already computes an engagement's
provenance from its linked assessments: an engagement drawing on a non-production assessment is
itself non-production. Assessment provenance is immutable and was recorded at creation. Applying the
same function to existing rows therefore uses facts the database already holds — it does not infer
anything from titles, dates, or which environment this happens to be running in.

An engagement with no linked assessment, or only production ones, **stays production** and stays
undeletable. That is the safe direction and the whole point: ADR-0047 forbids deleting production
records, and a row we cannot show to be demo data must keep being treated as real work.

Revision ID: 0040_backfill_engagement_provenance
Revises: 0039_engagement_provenance
"""

from __future__ import annotations

import json

import sqlalchemy as sa
from alembic import op

revision = "0040_backfill_engagement_provenance"
down_revision = "0039_engagement_provenance"
branch_labels = None
depends_on = None

#: Weakest first. A row takes the strongest marker among its assessments, mirroring the
#: one-directional rule in `create_engagement` — a marker may be strengthened, never weakened.
_STRENGTH = {"production": 0, "sandbox": 1, "demo": 2}


def upgrade() -> None:
    bind = op.get_bind()

    engagements = list(bind.execute(sa.text("SELECT id, assessment_ids_json FROM engagements")))
    if not engagements:
        return

    assessment_provenance = {
        str(row.id): row.provenance
        for row in bind.execute(sa.text("SELECT id, provenance FROM assessments"))
    }

    for engagement in engagements:
        # The column is JSON text holding a list of assessment id strings. Parsed rather than
        # LIKE-matched: a substring match on raw JSON would happily match a partial UUID.
        try:
            linked = json.loads(engagement.assessment_ids_json or "[]")
        except (TypeError, ValueError):
            continue  # unreadable JSON is left alone rather than guessed at

        strongest = "production"
        for assessment_id in linked:
            provenance = assessment_provenance.get(str(assessment_id), "production")
            if _STRENGTH.get(provenance, 0) > _STRENGTH[strongest]:
                strongest = provenance

        if strongest != "production":
            bind.execute(
                sa.text("UPDATE engagements SET provenance = :p WHERE id = :i"),
                {"p": strongest, "i": engagement.id},
            )


def downgrade() -> None:
    # Deliberately NOT reversed. Setting every engagement back to `production` would re-mark demo
    # records as real client work, which is the failure ADR-0029 exists to prevent — a far worse
    # state than the one this migration corrected. Re-running `upgrade` is idempotent.
    pass
