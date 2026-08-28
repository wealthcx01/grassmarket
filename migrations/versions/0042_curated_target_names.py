"""Curated display names for registry targets whose import stored a domain stem.

GRS-0238 residue / founder decision D8. The LSEG roster's `inferred_institution` column holds the
stem of each firm's domain, so 128 institutions imported as `gs`, `db`, `citi`, and — from regional
subdomains — `uk`, `us`, `hk`. An advisor browsing Prospecting cannot act on those.

**A separate table, not a column on `registry_targets`.** That is the whole design:

- Re-running an importer upserts `registry_targets` by `target_id`. A curated name stored there
  would be silently overwritten by the next import, which is exactly how curation work gets lost.
- The imported value stays visible and unchanged, so the provenance chain from source file to row
  is never rewritten. What a human decided sits *beside* what the file said, not on top of it.
- Every override carries who set it and on what basis, because a name asserted with no reason is
  the same class of claim as a coefficient with no provenance (#3).

Revision ID: 0042_curated_target_names
Revises: 0041_checkpoint_confirmations
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0042_curated_target_names"
down_revision = "0041_checkpoint_confirmations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "registry_target_name_overrides",
        sa.Column(
            "target_id",
            sa.String(160),
            sa.ForeignKey("registry_targets.target_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("display_name", sa.String(300), nullable=False),
        # "high" | "medium" — a low-confidence name is not stored at all. An override exists to
        # remove doubt; one that carries doubt is worse than the stem, because the stem at least
        # looks wrong.
        sa.Column("confidence", sa.String(16), nullable=False),
        # Why this name. "domain", "known-abbreviation", "web-search", "founder". Free text so a
        # curator can be specific, required so nobody can assert a name with no reason.
        sa.Column("basis", sa.String(300), nullable=False),
        sa.Column("set_by", sa.String(160), nullable=False),
        sa.Column("set_on", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("registry_target_name_overrides")
