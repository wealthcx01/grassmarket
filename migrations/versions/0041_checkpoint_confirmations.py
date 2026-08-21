"""An advisor can confirm they did a checkpoint.

GRS-0239 scope 3. CHECKPOINT slides render "Do this now:" and then do nothing — no control, no
state, no record — although the content contract promises "the advisor produces something and
confirms they did". Ticking through a lesson has therefore meant scrolling past its checkpoints.

The key is `(owner_consultant_id, lesson_id, slide_order)`. Lesson ids are deterministic (derived
from the course slug and lesson key), so they survive a re-publish; `slide_order` does not carry the
same guarantee, and that is a real limitation rather than an oversight:

**re-ordering a lesson's slides moves a confirmation to whichever slide now holds that position.**

The alternatives were worse. Adding a stable id to `Slide` changes a frozen contract every course
already validates against, and hashing the slide body would silently drop every confirmation the
moment an author fixed a typo. Position is the only key the content model actually offers today. A
confirmation is a self-reported training signal, not an approval record or anything a client sees,
so a mis-attributed one costs an advisor a re-tick — noted in the repository method so nobody later
mistakes this for a guarantee it does not make.

Revision ID: 0041_checkpoint_confirmations
Revises: 0040_backfill_engagement_provenance
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0041_checkpoint_confirmations"
down_revision = "0040_backfill_engagement_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "checkpoint_confirmations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "owner_consultant_id",
            sa.Uuid(),
            sa.ForeignKey("consultants.id"),
            index=True,
            nullable=False,
        ),
        sa.Column("course_id", sa.Uuid(), sa.ForeignKey("courses.id"), index=True, nullable=False),
        sa.Column("lesson_id", sa.Uuid(), nullable=False),
        sa.Column("slide_order", sa.Integer(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "owner_consultant_id",
            "lesson_id",
            "slide_order",
            name="uq_checkpoint_confirmation",
        ),
    )
    op.create_index(
        "ix_checkpoint_confirmations_lesson",
        "checkpoint_confirmations",
        ["owner_consultant_id", "lesson_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_checkpoint_confirmations_lesson", table_name="checkpoint_confirmations")
    op.drop_table("checkpoint_confirmations")
