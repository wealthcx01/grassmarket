"""Pipeline extraction adapter (GRS-0249 scope 4).

The sibling of `pathb.extraction`. That port maps a transcript to a proposed assessment; this one
maps a voice note to a proposed **pipeline update** — stage, next action, its date, a comms-log
line. Same shape, same reason: extraction is AI, so it sits behind a swappable port, the real
Claude extractor plugs in at the composition root, and CI uses deterministic offline doubles that
make no live call.

**Nothing here writes.** An extractor returns a proposal. Applying it is the repository's
`confirm_voice_note_proposal`, which runs only when an advisor says so (non-negotiable #8).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from bcap_contracts.extraction import ExtractionConfidence
from bcap_contracts.voice_notes import PipelineField

# The production default, wired at the composition root behind this protocol (not imported here,
# so CI makes no live call) — mirroring CLAUDE_EXTRACTOR_REF in `pathb.extraction`.
CLAUDE_PIPELINE_EXTRACTOR_REF = "claude-pipeline-extractor-v1"


@dataclass(frozen=True)
class ProposedValue:
    """One field the extractor is willing to suggest, with where in the transcript it heard it.

    The span is not decoration: an advisor reading a proposed stage change wants to see the
    sentence it came from, and a correction that cannot be traced back to what was actually said
    is not reviewable.
    """

    field: PipelineField
    value: str
    confidence: ExtractionConfidence
    span_start: int
    span_end: int


@dataclass(frozen=True)
class PipelineExtractionResult:
    """What an extractor returns: the fields it will suggest, and the ones it could not fill.

    `gaps` is required to be honest rather than empty. "I listened for a next action and did not
    hear one" and "I did not listen for a next action" are different statements, and only the first
    is useful to the advisor deciding whether to type it themselves.
    """

    values: tuple[ProposedValue, ...] = ()
    gaps: tuple[str, ...] = ()


class PipelineExtractor(Protocol):
    """Maps a voice-note transcript to proposed pipeline fields. `version` identifies the provider
    on the stored proposal, so a re-extraction is traceable and an old proposal can always say
    which model produced it."""

    @property
    def version(self) -> str: ...

    def extract(self, transcript: str, *, company_name: str) -> PipelineExtractionResult: ...


class EmptyPipelineExtractor:
    """The offline default: proposes nothing and says so.

    Real extraction is AI. This placeholder never guesses a stage from keywords, because a
    keyword-matched stage change is exactly the plausible-looking fabrication non-negotiable #3
    exists to prevent — and it would arrive wearing a confidence score it had not earned. It
    returns every field as a gap, which renders as "nothing was extracted" rather than as an empty
    form the advisor might mistake for a considered answer.
    """

    version = "empty-pipeline-extractor-v1"

    def extract(self, transcript: str, *, company_name: str) -> PipelineExtractionResult:
        return PipelineExtractionResult(values=(), gaps=tuple(f.value for f in PipelineField))


@dataclass
class FixturePipelineExtractor:
    """A test/dev extractor returning pre-built values, so the propose → correct → confirm path can
    be exercised deterministically without a model. Stands in for the AI exactly as
    `FixtureExtractor` does for Path A."""

    values: tuple[ProposedValue, ...] = field(default_factory=tuple)
    gaps: tuple[str, ...] = field(default_factory=tuple)
    version: str = "fixture-pipeline-extractor-v1"

    def extract(self, transcript: str, *, company_name: str) -> PipelineExtractionResult:
        return PipelineExtractionResult(values=self.values, gaps=self.gaps)
