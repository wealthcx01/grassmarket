"""Practice Arena contracts (GRS-0025, PRD §6) — AI-simulated discovery sessions.

An advisor runs a discovery conversation against a role-played client executive (built from an
anonymised vignette — never real client data). The conversation is then scored on **extraction
completeness**: which of the powers they probed on BOTH sides (benefit and barrier), which modules
they evidenced, and how many evidence-raising questions they asked. Scoring is deterministic
(keyword-cue matching over the advisor's turns) so it is testable against a fixture transcript; the
live role-play itself is exercised manually. AI feedback is a labelled proposal (#8), never
authoritative.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from bcap_contracts.base import OwnedResource
from bcap_contracts.common import Score

# The label every piece of AI feedback carries — nothing AI-authored is unmarked (#8).
AI_DRAFTED_LABEL = "AI-DRAFTED"


class ArenaSpeaker(StrEnum):
    ADVISOR = "advisor"
    CLIENT = "client"


class ArenaTurn(BaseModel):
    """One turn of the discovery conversation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    speaker: ArenaSpeaker
    text: str = Field(min_length=1)


class ArenaPowerTarget(BaseModel):
    """A power the advisor should probe, with the cue phrases that count as probing each side. A
    power is fully probed only when BOTH benefit and barrier are raised (Helmer, §8)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    power_key: str = Field(min_length=1)
    benefit_cues: tuple[str, ...] = Field(min_length=1)
    barrier_cues: tuple[str, ...] = Field(min_length=1)


class ArenaModuleTarget(BaseModel):
    """An infrastructure module the advisor should evidence, with its cue phrases."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    module_key: str = Field(min_length=1)
    cues: tuple[str, ...] = Field(min_length=1)


class ArenaScenario(OwnedResource):
    """A shared practice scenario (sourced from a calibration vignette — the single content
    pipeline, GRS-0022). Holds the case brief, the client persona, and the scoring targets."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    brief: str = Field(min_length=1)
    client_persona: str = Field(min_length=1)
    target_powers: tuple[ArenaPowerTarget, ...] = Field(min_length=1)
    target_modules: tuple[ArenaModuleTarget, ...] = ()
    evidence_cues: tuple[str, ...] = ()


class PowerProbeResult(BaseModel):
    """Whether the advisor probed a power's benefit and barrier sides."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    power_key: str
    benefit_probed: bool
    barrier_probed: bool

    @property
    def fully_probed(self) -> bool:
        return self.benefit_probed and self.barrier_probed


class ArenaScore(BaseModel):
    """The deterministic extraction-completeness score of a discovery transcript."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    powers: tuple[PowerProbeResult, ...]
    modules_evidenced: tuple[str, ...]
    evidence_questions: int = Field(ge=0)
    completeness: Score = Field(description="Fraction of the target extracted (0–1).")

    @property
    def powers_fully_probed(self) -> tuple[str, ...]:
        return tuple(p.power_key for p in self.powers if p.fully_probed)


class ArenaStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    SCORED = "scored"


class ArenaSession(OwnedResource):
    """One advisor's practice session. `owner_consultant_id` is the advisor. The transcript is
    submitted, then scored deterministically and given AI-drafted feedback (a labelled proposal,
    #8). Scores persist to the advisor's history (certification / bench-queue input)."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: UUID
    status: ArenaStatus = ArenaStatus.IN_PROGRESS
    transcript: tuple[ArenaTurn, ...] = ()
    score: ArenaScore | None = None
    feedback: str | None = None
    feedback_is_ai_drafted: bool = False
    drafter_version: str | None = None
    scored_at: datetime | None = None
