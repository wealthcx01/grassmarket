"""Pipeline service — pure computation over scoped prospects (GRS-0011, PRD §4).

Time-in-stage flags and the deal-volume forecast. Everything here is deterministic given an injected
``now`` (no wall-clock reads inside), so the tests pin behaviour exactly. Persistence stays in the
repository; this module only shapes what the repository already returned.

Currency-free by construction: the forecast is in *deal-count* units, weighted by the config
close-probabilities. The £ value forecast + recovery fees are a GRS-0012 concern (Money, ADR-0002).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from bcap_contracts.entities import PipelineStage, Prospect
from bcap_contracts.pipeline import (
    TERMINAL_STAGES,
    PipelineBoard,
    PipelineBoardEntry,
    PipelineConfig,
    PipelineForecast,
    StageForecast,
)


def _as_utc(value: datetime) -> datetime:
    """Coerce to timezone-aware UTC. Timestamps are always persisted in UTC, but SQLite drops the
    tzinfo on round-trip (Postgres keeps it), so a naive value read back is treated as UTC."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def days_in_stage(prospect: Prospect, now: datetime) -> int:
    """Whole days since the prospect entered its current stage. Never negative (clamped at 0)."""
    delta = _as_utc(now) - _as_utc(prospect.stage_entered_at)
    return max(0, delta.days)


def _board_entry(prospect: Prospect, config: PipelineConfig, now: datetime) -> PipelineBoardEntry:
    params = config.params(prospect.stage)
    dis = days_in_stage(prospect, now)
    return PipelineBoardEntry(
        prospect=prospect,
        days_in_stage=dis,
        stale_after_days=params.stale_after_days,
        stale=dis >= params.stale_after_days,
    )


def build_board(
    prospects: Sequence[Prospect], config: PipelineConfig, now: datetime
) -> PipelineBoard:
    """The kanban board: every prospect annotated with time-in-stage and its staleness flag."""
    entries = tuple(_board_entry(p, config, now) for p in prospects)
    return PipelineBoard(generated_at=now, entries=entries)


def build_forecast(
    prospects: Sequence[Prospect], config: PipelineConfig, now: datetime
) -> PipelineForecast:
    """A probability-weighted deal-*volume* forecast (currency-free). One row per stage (all ten,
    in canonical order) plus the book-level expected won-deal count."""
    counts: dict[PipelineStage, int] = {stage: 0 for stage in PipelineStage}
    for p in prospects:
        counts[p.stage] += 1

    stages: list[StageForecast] = []
    weighted_total = 0.0
    for stage in PipelineStage:
        count = counts[stage]
        prob = config.params(stage).close_probability
        weighted = count * prob
        weighted_total += weighted
        stages.append(
            StageForecast(stage=stage, count=count, close_probability=prob, weighted_deals=weighted)
        )

    total = len(prospects)
    open_count = sum(1 for p in prospects if p.stage not in TERMINAL_STAGES)
    return PipelineForecast(
        generated_at=now,
        total_prospects=total,
        open_prospects=open_count,
        stages=tuple(stages),
        weighted_expected_deals=weighted_total,
    )
