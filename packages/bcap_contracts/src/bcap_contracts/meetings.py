"""Path B meeting-intelligence ingestion (GRS-0029, PRD §3.3).

A meeting enters the system as a pasted transcript or an uploaded audio/video file; the media is
transcribed (behind a swappable adapter) and the transcript is stored **scoped to the owning
consultant and encrypted at rest**. NO AI extraction happens here — that is GRS-0030. Retention
fields are carried for the GDPR groundwork (GRS-0032). The `text` on this resource is the plaintext
the owner reads back; the storage layer holds only ciphertext.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from bcap_contracts.base import OwnedResource


class MediaKind(StrEnum):
    """How the transcript entered the system."""

    TRANSCRIPT_TEXT = "transcript_text"  # pasted text — no transcription needed
    AUDIO = "audio"
    VIDEO = "video"


class RecordingKind(StrEnum):
    """Who was in the room when this was recorded — which decides whether consent applies.

    The distinction is not bureaucracy. An advisor dictating a note alone in a car park has nobody
    to ask for consent; a session with a client in the room has somebody who must be asked. One
    flow cannot serve both honestly, so the advisor states which it is and the record keeps the
    answer (GRS-0249 scope 1, GRS-0255).
    """

    #: The advisor speaking alone. No second party, so no consent line — see the module note.
    VOICE_NOTE = "voice_note"
    #: Someone else was present. The consent gate applies and refuses without it.
    RECORDED_SESSION = "recorded_session"
    #: Pasted text, or media ingested before recording kinds existed. Neither was recorded here,
    #: so neither carries a consent claim.
    NOT_RECORDED = "not_recorded"


#: The consent line, **founder-approved 2026-09-03** (GRS-0255). This constant is the only copy in
#: the system: the recorder shows it, the gate checks against it, and the stored `consent_wording`
#: is the text itself rather than a reference to it, because wording changes over time and a record
#: that cannot say what was actually agreed is not a record.
#:
#: **Changing this string is a founder decision, not an engineering one.** UK rules make participant
#: consent the safe rule for confidential business meetings, and rules vary by jurisdiction.
#:
#: **Revised 2026-09-04 (founder).** The first version told the client the recording "stays in the
#: Bruntsfield advisor system" and "isn't shared outside the engagement team". Both were untrue:
#: the transcriber is hosted OpenAI Whisper (GRS-0251), so the audio leaves our infrastructure.
#: Changing it does **not** rewrite consents already given — a stored `consent_wording` is the text
#: that was actually shown to that client, and editing history to match a new promise would destroy
#: the only thing the field is for.
FOUNDER_APPROVED_CONSENT_WORDING = (
    "I'd like to record this session so I can write it up accurately. The recording is stored in "
    "the Bruntsfield advisor system and sent to OpenAI to be transcribed. Beyond that it isn't "
    "shared outside the engagement team. Are you happy for me to record?"
)


class MeetingTranscript(OwnedResource):
    """A stored meeting transcript owned by the consultant who ingested it. The text is sensitive:
    it is stored encrypted at rest and only ever returned to its owner. `transcriber_ref` records
    which adapter produced it ('pasted' for text) so a re-transcription is traceable."""

    model_config = ConfigDict(extra="forbid")

    #: A transcript may hang off a prospect, a workshop or an engagement. A voice note recorded in
    #: a car park after a pitch belongs to a **prospect** — there is no engagement yet, and that is
    #: the moment the recorder exists for (GRS-0249 scope 1; GRS-0254 build 1-2, following the
    #: `documents` shape rather than inventing a second one). None of the three is required: a
    #: transcript filed against nothing yet is a note the advisor has not yet placed.
    prospect_id: UUID | None = Field(
        default=None, description="The prospect this meeting belongs to, if any."
    )
    workshop_id: UUID | None = Field(
        default=None, description="The workshop this meeting belongs to, if any."
    )
    engagement_id: UUID | None = Field(
        default=None, description="The engagement this meeting belongs to, if linked."
    )
    source_kind: MediaKind
    source_filename: str = Field(min_length=1)
    text: str = Field(description="Transcript plaintext (owner-only; stored encrypted at rest).")
    transcriber_ref: str = Field(
        min_length=1, description="The adapter/version that produced the text ('pasted' for text)."
    )
    recording_kind: RecordingKind = Field(
        default=RecordingKind.NOT_RECORDED,
        description="Who was in the room — which decides whether the consent gate applies.",
    )
    consent_confirmed_at: datetime | None = Field(
        default=None,
        description="When the advisor confirmed the client agreed. Required for a recorded "
        "session.",
    )
    consent_wording: str | None = Field(
        default=None,
        description="The exact text the client agreed to, stored in full rather than referenced — "
        "wording changes over time and a record that cannot say what was agreed is not a record.",
    )
    #: The stored audio this transcript came from (GRS-0247 document). Kept alongside the text,
    #: always: a corrected transcript whose recording was thrown away cannot be re-checked when the
    #: extraction is disputed, and disputes are the whole reason to keep provenance (GRS-0249).
    recording_document_id: UUID | None = Field(
        default=None, description="The stored audio this transcript was produced from, if kept."
    )
    retention_until: date | None = Field(
        default=None, description="Delete-after date — GDPR retention groundwork (GRS-0032)."
    )

    @model_validator(mode="after")
    def _consent_matches_the_recording_kind(self) -> MeetingTranscript:
        """**No consent, no recording kept** (GRS-0255) — and no consent claimed where none
        was asked.

        Both directions are refused. A recorded session without consent must never exist as a
        record — the gate refuses rather than storing and flagging. A voice note carrying a consent
        timestamp would be a claim that somebody agreed to something when the advisor was alone,
        which is the quieter and worse failure of the two.
        """
        has_consent = self.consent_confirmed_at is not None or self.consent_wording is not None
        if self.recording_kind is RecordingKind.RECORDED_SESSION:
            if self.consent_confirmed_at is None or self.consent_wording is None:
                raise ValueError(
                    "A recorded session must carry both consent_confirmed_at and consent_wording. "
                    "No consent, no recording kept."
                )
        elif has_consent:
            raise ValueError(
                f"A {self.recording_kind.value} carries no consent: there was nobody present to "
                f"agree. Only a recorded session may set consent_confirmed_at/consent_wording."
            )
        return self
