"""Documents an advisor uploads (GRS-0247).

A board pack, an org chart, a signed engagement letter — the evidence behind an assessment. Until
this existed the product had no general upload path at all: the only inbound route was Path B's
media ingest, which keeps a transcript and discards the file.

**Parented by prospect, workshop or engagement — at least one.** A workshop is recorded and its
papers collected while the client is still a prospect, before any engagement exists, so requiring
an engagement would exclude the case the feature is for (Backend Requests R2, 2026-09-02).

The bytes are never on this resource. It is metadata; the content is fetched separately and is
stored encrypted at rest, like a meeting transcript.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from bcap_contracts.assessments import RecordProvenance
from bcap_contracts.base import OwnedResource

#: The largest upload accepted, mirroring `Settings.max_upload_bytes`. Stated here so the contract
#: carries the limit the client should enforce before wasting a round trip on it.
MAX_DOCUMENT_BYTES = 25 * 1024 * 1024


class Document(OwnedResource):
    """One uploaded file, owned by the advisor who uploaded it and scoped to them absolutely."""

    model_config = ConfigDict(extra="forbid")

    prospect_id: UUID | None = Field(
        default=None, description="The prospect this document belongs to, if any."
    )
    workshop_id: UUID | None = Field(
        default=None, description="The workshop this document belongs to, if any."
    )
    engagement_id: UUID | None = Field(
        default=None, description="The engagement this document belongs to, if any."
    )

    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=128)
    byte_size: int = Field(ge=1, le=MAX_DOCUMENT_BYTES)
    sha256: str = Field(
        min_length=64,
        max_length=64,
        description="SHA-256 of the PLAINTEXT, so an integrity check needs no key and a re-upload "
        "of the same file is recognisable although its ciphertext differs each time.",
    )
    provenance: RecordProvenance = RecordProvenance.PRODUCTION
    scanner_ref: str = Field(
        min_length=1,
        max_length=64,
        description="Which scanner passed this file, so a later change of provider is traceable.",
    )
    uploaded_by_consultant_id: UUID
    retention_until: date | None = None

    @model_validator(mode="after")
    def _requires_a_parent(self) -> Document:
        """A document with no parent is unreachable — nothing lists it and nobody finds it again.

        Refused here as well as by the table's CHECK constraint: the contract is the shape the
        Holy Corner API will expose, and a rule enforced only in the database is invisible to it.
        """
        if self.prospect_id is None and self.workshop_id is None and self.engagement_id is None:
            raise ValueError(
                "A document must belong to a prospect, a workshop or an engagement. One with no "
                "parent could never be found again."
            )
        return self


class UploadDocumentRequest(BaseModel):
    """The upload body: base64 content plus where it belongs.

    Base64-in-JSON matches the existing media ingest rather than introducing multipart for one
    endpoint. It costs ~33% on the wire, which the size cap already accounts for.
    """

    model_config = ConfigDict(extra="forbid")

    content_base64: str = Field(min_length=1)
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=128)
    prospect_id: UUID | None = None
    workshop_id: UUID | None = None
    engagement_id: UUID | None = None
    retention_until: date | None = None
