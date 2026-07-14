"""Path B extraction → review (GRS-0030, PRD §3.3).

AI maps a stored transcript to the assessment schema; the consultant confirms every field before any
of it reaches the engine. The extraction is a **gated proposal** (the ActiveGraph / #8 pattern): the
proposed `AssessmentDocument` lives on the extraction record, NOT on the assessment, until it is
confirmed — so unconfirmed AI output can never be scored. Confirmation applies the (possibly
corrected) document through the SAME Path A save path, so confirmed Path B data is indistinguishable
from manual entry downstream — the PRD's "byte-identical scoring run" guarantee is structural.

Each proposed field carries provenance: which transcript, which character span, the model's
confidence, and whether it was accepted — the audit trail (PRD §3.3, acceptance logged per field).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import ConfigDict, Field

from bcap_contracts.assessments import AssessmentDocument
from bcap_contracts.base import OwnedResource


class ExtractionConfidence(StrEnum):
    """The model's confidence in an extracted field (PRD §3.3)."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExtractionStatus(StrEnum):
    """A proposal collects while PROPOSED; confirmation applies it and moves it to CONFIRMED."""

    PROPOSED = "proposed"
    CONFIRMED = "confirmed"


class FieldProvenance(OwnedResource):
    """The audit record for one extracted field: which schema field, from which transcript span, at
    what confidence, and whether the consultant accepted it. Persisted per field (PRD §3.3)."""

    model_config = ConfigDict(extra="forbid")

    extraction_id: UUID
    transcript_id: UUID
    field_ref: str = Field(
        min_length=1, description="The assessment-schema field, e.g. 'subcomponent:OEMS_LATENCY'."
    )
    confidence: ExtractionConfidence
    span_start: int = Field(
        ge=0, description="Character offset of the supporting span in the text."
    )
    span_end: int = Field(ge=0)
    accepted: bool = Field(
        default=False, description="Set true when the consultant confirms this field (per-field)."
    )


class Extraction(OwnedResource):
    """A gated extraction proposal against one assessment, drawn from one transcript. The proposed
    document is NOT the assessment's document — it is applied only on confirmation, so nothing
    unconfirmed reaches the engine. `gaps` names fields the extractor could not fill."""

    model_config = ConfigDict(extra="forbid")

    assessment_id: UUID
    transcript_id: UUID
    status: ExtractionStatus = ExtractionStatus.PROPOSED
    proposed_document: AssessmentDocument
    gaps: tuple[str, ...] = Field(
        default=(), description="Schema fields the transcript did not fill (explicit gap flags)."
    )
    extractor_version: str = Field(min_length=1)
    confirmed_at: datetime | None = None
