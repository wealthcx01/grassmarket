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

from grassmarket.pipeline.win_probability import score_win_probability


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
    stale = dis >= params.stale_after_days
    return PipelineBoardEntry(
        prospect=prospect,
        days_in_stage=dis,
        stale_after_days=params.stale_after_days,
        stale=stale,
        win_probability=score_win_probability(prospect, stale=stale, config=config),
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
    """A probability-weighted deal-*volume* forecast (currency-free). Per-stage funnel rows (count ×
    stage close-probability) plus the headline `weighted_expected_deals` — the expected count of NEW
    wins from the open book.

    The headline is the sum of each in-flight prospect's OWN win probability — the exact number the
    advisor sees on its card — so the KPI and the cards can never disagree (GRS-0137). A SETTLED
    deal is excluded: an already-won one (base 1.0, in delivery) is a win not an *expected* win, and
    a lost one (base 0.0) contributes nothing. So the KPI counts open pipeline, not closed work."""
    counts: dict[PipelineStage, int] = {stage: 0 for stage in PipelineStage}
    for p in prospects:
        counts[p.stage] += 1

    # Per-stage funnel view (unchanged): the book by stage, at each stage's base close rate.
    stages: list[StageForecast] = []
    for stage in PipelineStage:
        count = counts[stage]
        prob = config.params(stage).close_probability
        stages.append(
            StageForecast(
                stage=stage, count=count, close_probability=prob, weighted_deals=count * prob
            )
        )

    # Headline = Σ per-prospect win probability over NON-SETTLED prospects (base in (0,1)) — equal
    # to the sum of the win-probability pills, and free of already-won / lost work.
    expected_new_wins = 0.0
    for p in prospects:
        params = config.params(p.stage)
        if params.close_probability in (0.0, 1.0):
            continue  # settled — an already-won or lost deal is not an "expected new win"
        stale = days_in_stage(p, now) >= params.stale_after_days
        expected_new_wins += score_win_probability(p, stale=stale, config=config).score / 100.0

    total = len(prospects)
    open_count = sum(1 for p in prospects if p.stage not in TERMINAL_STAGES)
    return PipelineForecast(
        generated_at=now,
        total_prospects=total,
        open_prospects=open_count,
        stages=tuple(stages),
        weighted_expected_deals=expected_new_wins,
    )
