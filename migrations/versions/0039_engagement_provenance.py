"""Give an engagement the record provenance every other record already has.

GRS-0241 scope 1. The founder asked twice — 23/07 and again 31/07 — for the duplicate demo rows on
the Engagements page to go. It was never done, and the reason turns out to be structural rather
than neglect:

**an engagement has no provenance.** Assessments and deliverables carry `RecordProvenance`
(ADR-0029), set at creation and immutable, which is how every other surface knows to badge a record
as demo or sandbox and how ADR-0047 knows what may be deleted. Engagements were missed. So nothing
could badge them, and nothing could safely delete a duplicate: ADR-0047 forbids deleting a
production record, and without provenance no engagement can be *shown* to be non-production.

This adds the column, defaulting to `production` — the safe direction, and the same default the
other tables use. Existing rows are therefore production and remain undeletable, which is correct:
we cannot retroactively prove that a row created before this column was demo data.

**The staging duplicates are not fixed by this migration**, and that is deliberate. They are fixed
by re-running the demo seed (which now stamps `demo`) and then running
`scripts/staging_cleanup_grs0241.py`, which will only ever remove rows the database itself says are
non-production. A migration that guessed at which historical rows were demo would be doing exactly
the thing ADR-0047 exists to prevent.

Revision ID: 0039_engagement_provenance
Revises: 0038_prospect_registry_link
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0039_engagement_provenance"
down_revision = "0038_prospect_registry_link"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "engagements",
        sa.Column(
            "provenance",
            sa.String(16),
            nullable=False,
            server_default="production",
        ),
    )
    op.create_index("ix_engagements_provenance", "engagements", ["provenance"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_engagements_provenance", table_name="engagements")
    op.drop_column("engagements", "provenance")
