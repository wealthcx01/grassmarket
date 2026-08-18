"""report-scoped founder approvals (GRS-0245)

Two nullable columns on `founder_approvals`, so an approval can name a client report as well as an
assessment document. Nullable on purpose: every pre-existing row is an assessment approval and stays
valid unchanged — this widens the table's meaning rather than migrating its contents.

Revision ID: 0037_report_founder_approval
Revises: 0036_client_report_prose
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0037_report_founder_approval"
down_revision = "0036_client_report_prose"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "founder_approvals",
        sa.Column("deliverable_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "founder_approvals",
        sa.Column("content_json", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_founder_approvals_deliverable_id",
        "founder_approvals",
        ["deliverable_id"],
    )
    # Named explicitly so the downgrade can drop it on every backend; SQLite in particular will not
    # find an unnamed constraint.
    with op.batch_alter_table("founder_approvals") as batch:
        batch.create_foreign_key(
            "fk_founder_approvals_deliverable_id",
            "deliverables",
            ["deliverable_id"],
            ["id"],
        )
    # The report's own "please look at this" timestamp. An assessment has one on its row; the
    # report needs its own rather than borrowing the assessment's, because the two are reviewed at
    # different moments — the prose is written after the assessment is already approved.
    op.add_column(
        "client_report_prose",
        sa.Column("review_requested_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("client_report_prose", "review_requested_at")
    with op.batch_alter_table("founder_approvals") as batch:
        batch.drop_constraint("fk_founder_approvals_deliverable_id", type_="foreignkey")
    op.drop_index("ix_founder_approvals_deliverable_id", table_name="founder_approvals")
    op.drop_column("founder_approvals", "content_json")
    op.drop_column("founder_approvals", "deliverable_id")
