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


class PipelineConfig(BaseModel):
    """The full pipeline configuration — every stage must be present (ADR-0001 completeness)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = Field(min_length=1)
    stages: dict[PipelineStage, PipelineStageParams]

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
        description="Σ close_probability over all prospects — expected won deals in the book.",
    )


class PipelineBoardEntry(BaseModel):
    """A prospect annotated with its time-in-stage and staleness flag."""

    model_config = ConfigDict(extra="forbid")

    prospect: Prospect
    days_in_stage: int = Field(ge=0)
    stale_after_days: int = Field(ge=0)
    stale: bool


class PipelineBoard(BaseModel):
    """The kanban board: every scoped prospect with its time-in-stage flag."""

    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    entries: tuple[PipelineBoardEntry, ...]
