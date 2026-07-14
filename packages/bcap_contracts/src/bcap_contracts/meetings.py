"""Path B meeting-intelligence ingestion (GRS-0029, PRD §3.3).

A meeting enters the system as a pasted transcript or an uploaded audio/video file; the media is
transcribed (behind a swappable adapter) and the transcript is stored **scoped to the owning
consultant and encrypted at rest**. NO AI extraction happens here — that is GRS-0030. Retention
fields are carried for the GDPR groundwork (GRS-0032). The `text` on this resource is the plaintext
the owner reads back; the storage layer holds only ciphertext.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from uuid import UUID

from pydantic import ConfigDict, Field

from bcap_contracts.base import OwnedResource


class MediaKind(StrEnum):
    """How the transcript entered the system."""

    TRANSCRIPT_TEXT = "transcript_text"  # pasted text — no transcription needed
    AUDIO = "audio"
    VIDEO = "video"


class MeetingTranscript(OwnedResource):
    """A stored meeting transcript owned by the consultant who ingested it. The text is sensitive:
    it is stored encrypted at rest and only ever returned to its owner. `transcriber_ref` records
    which adapter produced it ('pasted' for text) so a re-transcription is traceable."""

    model_config = ConfigDict(extra="forbid")

    engagement_id: UUID | None = Field(
        default=None, description="The engagement this meeting belongs to, if linked."
    )
    source_kind: MediaKind
    source_filename: str = Field(min_length=1)
    text: str = Field(description="Transcript plaintext (owner-only; stored encrypted at rest).")
    transcriber_ref: str = Field(
        min_length=1, description="The adapter/version that produced the text ('pasted' for text)."
    )
    retention_until: date | None = Field(
        default=None, description="Delete-after date — GDPR retention groundwork (GRS-0032)."
    )
