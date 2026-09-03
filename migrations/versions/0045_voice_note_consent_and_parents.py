"""Voice notes: recording kind, the consent gate, the kept audio, and the missing parents
(GRS-0249; absorbs GRS-0254 build 1).

Three things arrive together because the recorder needs all three to exist honestly.

**Parents.** A voice note recorded in a car park after a pitch belongs to a *prospect* — there is
no engagement yet, and that is the one moment the recorder is for. `meeting_transcripts` gains
`prospect_id` and `workshop_id` beside `engagement_id`, matching `documents`. `engagement_id` was a
bare Uuid with no key; it becomes one here, because leaving one of three parents unenforced is the
dangling reference GRS-0246 made structurally impossible everywhere else.

**Consent.** A recorded session must carry `consent_confirmed_at` and `consent_wording` — the exact
text the client agreed to, in full, never a reference to it. A voice note must carry neither: the
advisor was alone and there was nobody to ask. Both directions are a CHECK, so neither is merely
refused at the door.

**The audio.** `recording_document_id` points at the stored recording (GRS-0247). Media bytes used
to be discarded after transcription, which left a disputed extraction with nothing to re-check.

SQLite cannot ALTER a table to add a key or a CHECK, so this runs in batch mode — the table is
rebuilt. Postgres validates the new keys against existing rows, so a dangling engagement_id would
fail the migration; it is checked first and reported by count rather than left to surface as a
constraint error nobody can read.

Revision ID: 0045_voice_note_consent_and_parents
Revises: 0044_documents
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0045_voice_note_consent_and_parents"
down_revision = "0044_documents"
branch_labels = None
depends_on = None

_CONSENT_CHECK = (
    "(recording_kind = 'recorded_session' "
    " AND consent_confirmed_at IS NOT NULL AND consent_wording IS NOT NULL) "
    "OR (recording_kind <> 'recorded_session' "
    " AND consent_confirmed_at IS NULL AND consent_wording IS NULL)"
)


def _refuse_on_dangling_engagement_ids() -> None:
    """Refuse to add the key while a transcript points at an engagement that is not there.

    Nulling them would be a quiet edit of somebody's records — the thing this codebase refuses
    elsewhere. Reported by count so the operator can look before deciding.
    """
    dangling = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT COUNT(*) FROM meeting_transcripts t "
                "WHERE t.engagement_id IS NOT NULL AND NOT EXISTS "
                "(SELECT 1 FROM engagements e WHERE e.id = t.engagement_id)"
            )
        )
        .scalar_one()
    )
    if dangling:
        raise RuntimeError(
            f"{dangling} meeting_transcripts row(s) point at an engagement that no longer exists. "
            f"Adding the foreign key would fail. Decide what those transcripts belong to before "
            f"re-running this migration — do not null the column to get past it."
        )


def upgrade() -> None:
    _refuse_on_dangling_engagement_ids()
    with op.batch_alter_table("meeting_transcripts") as batch:
        batch.add_column(sa.Column("prospect_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("workshop_id", sa.Uuid(), nullable=True))
        batch.add_column(
            sa.Column(
                "recording_kind",
                sa.String(length=24),
                nullable=False,
                server_default="not_recorded",
            )
        )
        batch.add_column(
            sa.Column("consent_confirmed_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch.add_column(sa.Column("consent_wording", sa.Text(), nullable=True))
        batch.add_column(sa.Column("recording_document_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_meeting_transcripts_prospect_id",
            "prospects",
            ["prospect_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch.create_foreign_key(
            "fk_meeting_transcripts_workshop_id",
            "workshops",
            ["workshop_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch.create_foreign_key(
            "fk_meeting_transcripts_engagement_id",
            "engagements",
            ["engagement_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch.create_foreign_key(
            "fk_meeting_transcripts_recording_document_id",
            "documents",
            ["recording_document_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch.create_check_constraint(
            "ck_meeting_transcripts_consent_matches_recording_kind", _CONSENT_CHECK
        )
    for column in ("prospect_id", "workshop_id", "recording_document_id"):
        op.create_index(f"ix_meeting_transcripts_{column}", "meeting_transcripts", [column])


def downgrade() -> None:
    for column in ("prospect_id", "workshop_id", "recording_document_id"):
        op.drop_index(f"ix_meeting_transcripts_{column}", table_name="meeting_transcripts")
    with op.batch_alter_table("meeting_transcripts") as batch:
        batch.drop_constraint(
            "ck_meeting_transcripts_consent_matches_recording_kind", type_="check"
        )
        for name in (
            "fk_meeting_transcripts_prospect_id",
            "fk_meeting_transcripts_workshop_id",
            "fk_meeting_transcripts_engagement_id",
            "fk_meeting_transcripts_recording_document_id",
        ):
            batch.drop_constraint(name, type_="foreignkey")
        for column in (
            "recording_document_id",
            "consent_wording",
            "consent_confirmed_at",
            "recording_kind",
            "workshop_id",
            "prospect_id",
        ):
            batch.drop_column(column)
