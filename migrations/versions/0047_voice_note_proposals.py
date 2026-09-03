"""Voice note → pipeline proposals, gated (GRS-0249 scope 4).

The Path B extraction tables, one level down. `extractions` proposes an assessment; these propose a
pipeline update — stage, next action, its date, a comms-log line. The proposed values live here and
never on the prospect until an advisor confirms, so a voice note cannot move a stage on its own
(non-negotiable #8).

`voice_note_proposed_fields` keeps `proposed_value` **and** `confirmed_value` side by side. What the
machine said and what a person agreed to are different facts, and collapsing them would destroy the
only evidence that the approval gate does anything: afterwards nobody could tell a corrected field
from an accepted one.

Fields CASCADE from their proposal — they have no meaning without it. Both parents of a proposal
RESTRICT: deleting a prospect or a transcript out from under a proposal that cites it is refused
rather than left dangling (the GRS-0246 rule).

Revision ID: 0047_voice_note_proposals
Revises: 0046_prospect_next_action
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0047_voice_note_proposals"
down_revision = "0046_prospect_next_action"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "voice_note_proposals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column(
            "prospect_id",
            sa.Uuid(),
            sa.ForeignKey("prospects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "transcript_id",
            sa.Uuid(),
            sa.ForeignKey("meeting_transcripts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("extractor_version", sa.String(length=64), nullable=False),
        sa.Column("gaps_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discarded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in ("owner_consultant_id", "prospect_id", "transcript_id"):
        op.create_index(f"ix_voice_note_proposals_{column}", "voice_note_proposals", [column])

    op.create_table(
        "voice_note_proposed_fields",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column(
            "proposal_id",
            sa.Uuid(),
            sa.ForeignKey("voice_note_proposals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("transcript_id", sa.Uuid(), nullable=False),
        sa.Column("field", sa.String(length=32), nullable=False),
        sa.Column("proposed_value", sa.Text(), nullable=True),
        sa.Column("confidence", sa.String(length=8), nullable=False),
        sa.Column("span_start", sa.Integer(), nullable=False),
        sa.Column("span_end", sa.Integer(), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("confirmed_value", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    for column in ("owner_consultant_id", "proposal_id"):
        op.create_index(
            f"ix_voice_note_proposed_fields_{column}", "voice_note_proposed_fields", [column]
        )


def downgrade() -> None:
    for column in ("owner_consultant_id", "proposal_id"):
        op.drop_index(
            f"ix_voice_note_proposed_fields_{column}", table_name="voice_note_proposed_fields"
        )
    op.drop_table("voice_note_proposed_fields")
    for column in ("owner_consultant_id", "prospect_id", "transcript_id"):
        op.drop_index(f"ix_voice_note_proposals_{column}", table_name="voice_note_proposals")
    op.drop_table("voice_note_proposals")
