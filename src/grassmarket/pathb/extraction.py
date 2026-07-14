"""Extraction adapter (GRS-0030, PRD §3.3).

An `Extractor` port maps a transcript to a proposed `AssessmentDocument` plus per-field provenance
(which span, what confidence) and explicit gap flags. Extraction is AI, so it is a swappable port
behind the #8 gate — the real Claude extractor plugs in at the composition root; CI and tests use
deterministic offline fakes. Nothing here writes to an assessment: extraction only PROPOSES.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from bcap_contracts.assessments import AssessmentDocument
from bcap_contracts.extraction import ExtractionConfidence

# The production default recorded per the ticket: a Claude extractor, wired at the composition root
# behind this protocol (not imported here, so CI makes no live call).
CLAUDE_EXTRACTOR_REF = "claude-extractor-v1"


@dataclass(frozen=True)
class ExtractedFieldSpec:
    """One extracted field's provenance, before it becomes a persisted FieldProvenance record."""

    field_ref: str
    confidence: ExtractionConfidence
    span_start: int
    span_end: int


@dataclass(frozen=True)
class ExtractionResult:
    """What an extractor returns: the proposed document, the per-field provenance, and the gaps."""

    proposed_document: AssessmentDocument
    fields: tuple[ExtractedFieldSpec, ...] = ()
    gaps: tuple[str, ...] = ()


class Extractor(Protocol):
    """Maps a transcript to a proposed assessment document + provenance. `version` identifies the
    provider on the stored extraction so a re-extraction is traceable."""

    @property
    def version(self) -> str: ...

    def extract(self, transcript: str, *, subject: str) -> ExtractionResult: ...


class EmptyExtractor:
    """The offline default: proposes an empty document (subject only), everything a gap. Real
    extraction is AI — this placeholder never fabricates ratings; the Claude extractor replaces it
    behind the same port. Deterministic and offline, so CI makes no call."""

    version = "empty-extractor-v1"

    def extract(self, transcript: str, *, subject: str) -> ExtractionResult:
        return ExtractionResult(
            proposed_document=AssessmentDocument(subject=subject),
            fields=(),
            gaps=("all",),
        )


@dataclass
class FixtureExtractor:
    """A test/dev extractor that returns a pre-built document + provenance — stands in for the AI so
    the confirm→score path can be exercised deterministically (for the identical-scores test)."""

    document: AssessmentDocument
    provenance: tuple[ExtractedFieldSpec, ...] = field(default_factory=tuple)
    gaps: tuple[str, ...] = field(default_factory=tuple)
    version: str = "fixture-extractor-v1"

    def extract(self, transcript: str, *, subject: str) -> ExtractionResult:
        return ExtractionResult(
            proposed_document=self.document, fields=self.provenance, gaps=self.gaps
        )
