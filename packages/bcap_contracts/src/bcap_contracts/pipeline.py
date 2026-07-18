"""Pipeline lifecycle — the stage-transition graph, the (config-driven) stage parameters, and the
currency-free forecast/board response shapes (PRD §4, GRS-0011).

Three things live here, all keyed off :class:`PipelineStage`:

1. **The transition graph** — which stage moves are legal. An illegal jump (e.g. Prospect straight
   to Contracted) is refused loudly (:class:`IllegalStageTransition`); the machine never silently
   allows a skip. This is intrinsic domain logic, not a tunable rate, so it lives in code.
2. **Stage parameters** — the per-stage close-probability (forecast weighting) and stale-after-days
   (time-in-stage flag). These ARE tunable **configuration**, loaded fail-loud from
   ``registry_data/pipeline_config.yaml`` (rates/percentages are config, never code — CLAUDE.md).
3. **Forecast / board response shapes** — deliberately **currency-free**. GRS-0011 forecasts *deal
   volume* (stage-probability-weighted counts); the £ value forecast + recovery fees arrive with
   Money in GRS-0012 (ADR-0002). No Money type is imported here on purpose.
"""

from __future__ import annotations

import functools
from datetime import datetime
from importlib import resources
from typing import Any
from uuid import UUID

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from bcap_contracts.entities import PipelineStage, Prospect


class PipelineError(Exception):
    """Base class for pipeline failures. Never swallowed."""


class IllegalStageTransition(PipelineError):
    """A stage transition that the lifecycle graph does not permit. Refusal, never a silent skip."""

    def __init__(self, src: PipelineStage, dst: PipelineStage) -> None:
        self.src = src
        self.dst = dst
        allowed = ", ".join(s.value for s in sorted(LEGAL_TRANSITIONS[src])) or "(none — terminal)"
        super().__init__(
            f"Illegal pipeline transition {src.value} → {dst.value}. "
            f"From {src.value} the only legal moves are: {allowed}."
        )


class PipelineConfigError(PipelineError):
    """The pipeline configuration is incomplete or malformed. Load-time refusal (fail loud)."""


# --- 1. Transition graph ----------------------------------------------------------------------
# Forward path plus the two ever-available off-ramps (Nurture / Closed). A move to the SAME stage
# is NOT in any set — a no-op "transition" is treated as illegal so callers can't mask a bug.
LEGAL_TRANSITIONS: dict[PipelineStage, frozenset[PipelineStage]] = {
    PipelineStage.PROSPECT: frozenset(
        {PipelineStage.WORKSHOP_SCHEDULED, PipelineStage.NURTURE, PipelineStage.CLOSED}
    ),
    PipelineStage.WORKSHOP_SCHEDULED: frozenset(
        {PipelineStage.WORKSHOP_DELIVERED, PipelineStage.NURTURE, PipelineStage.CLOSED}
    ),
    PipelineStage.WORKSHOP_DELIVERED: frozenset(
        {PipelineStage.QUALIFIED, PipelineStage.NURTURE, PipelineStage.CLOSED}
    ),
    PipelineStage.QUALIFIED: frozenset(
        {PipelineStage.SCOPED, PipelineStage.NURTURE, PipelineStage.CLOSED}
    ),
    PipelineStage.SCOPED: frozenset(
        {PipelineStage.CONTRACTED, PipelineStage.NURTURE, PipelineStage.CLOSED}
    ),
    PipelineStage.CONTRACTED: frozenset({PipelineStage.ACTIVE, PipelineStage.CLOSED}),
    PipelineStage.ACTIVE: frozenset({PipelineStage.DELIVERED, PipelineStage.CLOSED}),
    PipelineStage.DELIVERED: frozenset({PipelineStage.CLOSED, PipelineStage.NURTURE}),
    # Nurture re-engages back into the top of the funnel or is closed off.
    PipelineStage.NURTURE: frozenset(
        {PipelineStage.PROSPECT, PipelineStage.WORKSHOP_SCHEDULED, PipelineStage.CLOSED}
    ),
    # Closed can be re-opened only into Nurture (deliberate re-engagement), never mid-funnel.
    PipelineStage.CLOSED: frozenset({PipelineStage.NURTURE}),
}


def is_legal_transition(src: PipelineStage, dst: PipelineStage) -> bool:
    return dst in LEGAL_TRANSITIONS[src]


def assert_legal_transition(src: PipelineStage, dst: PipelineStage) -> None:
    """Raise :class:`IllegalStageTransition` unless ``src → dst`` is a permitted move."""
    if not is_legal_transition(src, dst):
        raise IllegalStageTransition(src, dst)


# --- 2. Stage parameters (CONFIGURATION) ------------------------------------------------------
class PipelineStageParams(BaseModel):
    """Per-stage config: forecast weight + the time-in-stage staleness threshold."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    close_probability: float = Field(
        ge=0.0, le=1.0, description="Probability a prospect at this stage becomes a won deal."
    )
    stale_after_days: int = Field(
        ge=0, description="Days in stage after which the prospect is flagged stale."
    )


# --- Win-probability configuration (GRS-0111, config-not-code) --------------------------------
# The per-prospect win-probability scorer (src/grassmarket/pipeline/win_probability.py) is a
# deterministic, explainable estimate: it starts from the stage's close_probability and nudges it
# by data-completeness signals, then bands the result into a headline word. Every weight and band
# is CONFIGURATION here — not a currency, a probability (ADR-0002: score-points and £ never mix).
class WinProbabilitySignals(BaseModel):
    """Additive adjustments (in probability points, e.g. 0.05 = +5pp) applied to the stage base for
    a prospect that carries / lacks a given piece of qualifying information. ``stale_penalty`` is
    the (typically negative) adjustment when the prospect is flagged stale in its stage."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    has_primary_contact: float = Field(ge=-1.0, le=1.0)
    has_contact_email: float = Field(ge=-1.0, le=1.0)
    has_sector: float = Field(ge=-1.0, le=1.0)
    has_notes: float = Field(ge=-1.0, le=1.0)
    stale_penalty: float = Field(ge=-1.0, le=1.0)


class WinProbabilityBand(BaseModel):
    """A headline label applied when the adjusted probability is at least ``min_probability``."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    min_probability: float = Field(ge=0.0, le=1.0)
    label: str = Field(min_length=1)


class WinProbabilityConfig(BaseModel):
    """Win-probability tuning: the completeness signal weights and the label bands. Fail-loud — the
    bands must cover the whole [0, 1] range (a lowest band anchored at 0.0), so every score gets a
    label, never a default."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = Field(min_length=1)
    signals: WinProbabilitySignals
    bands: tuple[WinProbabilityBand, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _bands_cover_range(self) -> WinProbabilityConfig:
        if min(b.min_probability for b in self.bands) != 0.0:
            raise PipelineConfigError(
                "win_probability.bands must include a band anchored at 0.0 so every score is "
                "labelled (no default — ADR-0001)."
            )
        return self

    def band_for(self, probability: float) -> str:
        """The headline label for a probability — the highest band whose floor it clears."""
        best = max(
            (b for b in self.bands if probability >= b.min_probability),
            key=lambda b: b.min_probability,
        )
        return best.label


class PipelineConfig(BaseModel):
    """The full pipeline configuration — every stage must be present (ADR-0001 completeness)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = Field(min_length=1)
    stages: dict[PipelineStage, PipelineStageParams]
    win_probability: WinProbabilityConfig

    @model_validator(mode="after")
    def _require_every_stage(self) -> PipelineConfig:
        missing = set(PipelineStage) - set(self.stages)
        if missing:
            shown = ", ".join(s.value for s in sorted(missing))
            raise PipelineConfigError(
                f"pipeline_config.yaml is incomplete — missing stage parameters for: {shown}. "
                f"Every pipeline stage must be configured (no defaults — ADR-0001)."
            )
        return self

    def params(self, stage: PipelineStage) -> PipelineStageParams:
        """Fail-loud lookup — an unconfigured stage refuses rather than defaulting."""
        try:
            return self.stages[stage]
        except KeyError as exc:  # pragma: no cover - guarded by the completeness validator
            raise PipelineConfigError(f"No pipeline config for stage {stage.value}.") from exc


def _load_yaml(filename: str) -> Any:
    data_pkg = resources.files("bcap_contracts").joinpath("registry_data")
    with resources.as_file(data_pkg.joinpath(filename)) as path:
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)


@functools.lru_cache(maxsize=1)
def load_pipeline_config() -> PipelineConfig:
    """Load + validate the pipeline config once. Fails loud on an incomplete/malformed file."""
    raw = _load_yaml("pipeline_config.yaml")
    if not isinstance(raw, dict):
        raise PipelineConfigError("pipeline_config.yaml must be a mapping.")
    return PipelineConfig.model_validate(raw)


# --- 3. Forecast / board responses (currency-free) --------------------------------------------
# The stages considered out of active pursuit — excluded from the "open pipeline" count.
TERMINAL_STAGES: frozenset[PipelineStage] = frozenset({PipelineStage.CLOSED, PipelineStage.NURTURE})


class StageForecast(BaseModel):
    """One stage's slice of the forecast — count and probability-weighted expected deals."""

    model_config = ConfigDict(extra="forbid")

    stage: PipelineStage
    count: int = Field(ge=0)
    close_probability: float = Field(ge=0.0, le=1.0)
    weighted_deals: float = Field(ge=0.0, description="count × close_probability.")


class PipelineForecast(BaseModel):
    """A currency-free pipeline forecast: deal *volume*, probability-weighted by stage.

    The £ value forecast is a GRS-0012 concern (Money enters there); this stays in deal-count units
    so score/volume and currency never mix (ADR-0002).
    """

    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    total_prospects: int = Field(ge=0)
    open_prospects: int = Field(ge=0, description="Prospects not in a terminal stage.")
    stages: tuple[StageForecast, ...]
    weighted_expected_deals: float = Field(
        ge=0.0,
        description="Σ per-prospect win probability over NON-SETTLED prospects (GRS-0137) — the "
        "expected count of NEW wins from the open book, equal to the sum of the win-probability "
        "pills. Already-won (in-delivery) and lost deals are excluded.",
    )


class WinProbability(BaseModel):
    """A prospect's explainable win-probability (GRS-0111). ``score`` is a percentage 0–100 (a
    probability, never currency — ADR-0002); ``label`` is the config-banded headline word;
    ``reasons`` explain what moved the estimate; ``missing_info`` names the data gaps a consultant
    could fill to sharpen it. Deterministic given the prospect + config."""

    model_config = ConfigDict(extra="forbid")

    score: int = Field(ge=0, le=100, description="Win probability as a whole-number percentage.")
    label: str = Field(min_length=1)
    reasons: tuple[str, ...]
    missing_info: tuple[str, ...]


class PipelineBoardEntry(BaseModel):
    """A prospect annotated with its time-in-stage, staleness flag, and win-probability."""

    model_config = ConfigDict(extra="forbid")

    prospect: Prospect
    days_in_stage: int = Field(ge=0)
    stale_after_days: int = Field(ge=0)
    stale: bool
    win_probability: WinProbability


class PipelineBoard(BaseModel):
    """The kanban board: every scoped prospect with its time-in-stage flag."""

    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    entries: tuple[PipelineBoardEntry, ...]


class StageHistoryEntry(BaseModel):
    """One recorded stage transition for a prospect (GRS-0111) — the audit timeline behind the
    board. Written at the ``update_prospect_stage`` choke-point; ``from_stage`` is None only for the
    creation row (the prospect's first stage). Read-only, owner-scoped."""

    model_config = ConfigDict(extra="forbid")

    prospect_id: UUID
    from_stage: PipelineStage | None
    to_stage: PipelineStage
    occurred_at: datetime
