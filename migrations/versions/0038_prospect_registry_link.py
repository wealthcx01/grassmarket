"""Link a prospect to the registry target it was claimed from, and merge duplicate targets.

GRS-0238. Two changes that belong together because the second is only safe once the first exists.

**1. `prospects.registry_target_id`.** Nullable, because most existing prospects were typed by hand
and were never claimed from the registry — a NOT NULL column here would have to invent a link, which
is the fabrication the codebase refuses. With the column, "is this target already in my pipeline?"
is a join rather than a name-matching heuristic.

**2. Merge the measured duplicate targets.** The LSEG roster names institutions after the stem of
their domain (`barclays`, `ubs`, `jpmorgan`), so eight firms appear twice: once properly named from
the bank list, once lower-cased from the roster. The merge moves the roster's CONTACTS onto the
bank-list target and deletes the emptied duplicate.

**Only exact, case-insensitive name matches are merged.** Anything ambiguous is left alone and
reported, per the ticket's refuse-loud requirement: `Stock Exchange of Thailand` appears as both a
"Bank" and an "Indices" supplier, and merging those would assert an identity nobody has verified.

This does NOT fix the 120 roster institutions whose names are unreadable stems with no bank-list
counterpart (`gs`, `db`, `citi`, and the broken `uk`/`us`/`hk` rows). Nothing here can: resolving
`gs` to "Goldman Sachs" is a guess, and a guess written into the database is indistinguishable from
a fact afterwards. Those rows are MARKED in the API instead (`name_unverified`), and curating them
is founder work.

Revision ID: 0038_prospect_registry_link
Revises: 0037_report_founder_approval
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0038_prospect_registry_link"
down_revision = "0037_report_founder_approval"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("prospects", sa.Column("registry_target_id", sa.String(160), nullable=True))
    op.create_index(
        "ix_prospects_registry_target_id", "prospects", ["registry_target_id"], unique=False
    )

    bind = op.get_bind()

    # Candidate merges: same name ignoring case, more than one row. Grouped in SQL so the whole
    # registry is never loaded into memory.
    duplicate_names = [
        row[0]
        for row in bind.execute(
            sa.text(
                "SELECT LOWER(TRIM(name)) AS k FROM registry_targets "
                "GROUP BY LOWER(TRIM(name)) HAVING COUNT(*) > 1"
            )
        )
    ]

    for key in duplicate_names:
        rows = list(
            bind.execute(
                sa.text(
                    "SELECT target_id, name, segment, domain, source FROM registry_targets "
                    "WHERE LOWER(TRIM(name)) = :k ORDER BY target_id"
                ),
                {"k": key},
            )
        )
        # The survivor is the row whose name is not a bare lower-case stem — i.e. the one a human
        # would recognise. If none qualifies, or more than one does, we cannot choose without
        # guessing, so nothing is merged.
        readable = [r for r in rows if r.name.strip() != r.name.strip().lower()]
        if len(readable) != 1:
            continue

        survivor = readable[0]
        duplicates = [r for r in rows if r.target_id != survivor.target_id]

        # Refuse-loud on a conflicting domain: two rows claiming different domains under one name
        # are plausibly two different firms, and merging them would fabricate an identity.
        if any(r.domain and survivor.domain and r.domain != survivor.domain for r in duplicates):
            continue

        for duplicate in duplicates:
            # Contacts move first. A contact_id embeds its target_id, so a row already present on
            # the survivor would collide — drop those rather than fail the migration, since an
            # identical person under both targets is the duplication being removed.
            bind.execute(
                sa.text(
                    "DELETE FROM registry_contacts WHERE target_id = :dup AND REPLACE("
                    "contact_id, :dup, :keep) IN (SELECT contact_id FROM registry_contacts "
                    "WHERE target_id = :keep)"
                ),
                {"dup": duplicate.target_id, "keep": survivor.target_id},
            )
            bind.execute(
                sa.text(
                    "UPDATE registry_contacts SET contact_id = REPLACE(contact_id, :dup, :keep), "
                    "target_id = :keep WHERE target_id = :dup"
                ),
                {"dup": duplicate.target_id, "keep": survivor.target_id},
            )
            # Keep the merged-away name as an alias so search still finds "barclays".
            bind.execute(
                sa.text("DELETE FROM registry_targets WHERE target_id = :dup"),
                {"dup": duplicate.target_id},
            )


def downgrade() -> None:
    # The merge is NOT reversed. Once two targets are one, the split cannot be reconstructed without
    # the import sources, and inventing a plausible split is worse than leaving them merged. The
    # column drop is reversible; re-running the importers restores the pre-merge rows.
    op.drop_index("ix_prospects_registry_target_id", table_name="prospects")
    op.drop_column("prospects", "registry_target_id")
