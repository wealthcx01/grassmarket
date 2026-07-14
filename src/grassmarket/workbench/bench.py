"""The bench-time queue assembler + performance aggregation (GRS-0026, PRD §6).

Pure and deterministic. `assemble_queue` turns an advisor's already-fetched workbench state into a
prioritised "what to do next" list; the priority ORDER is the product decision and is pinned by a
golden master. `summarise_performance` folds the same kinds of records into a self-development
picture. Neither reads the database or the clock — the repository fetches, these compute — so both
are trivially testable and can never silently drift from the records they summarise.

Priority order (PRD §6): the next certification step, then due drills, then a practice-arena
scenario, then an Opportunity Radar research task (always present as the standing idle-time filler).
"""

from __future__ import annotations

from collections.abc import Sequence

from bcap_contracts.arena import ArenaScenario, ArenaSession, ArenaStatus
from bcap_contracts.bench import (
    ArenaTrendPoint,
    BenchItemKind,
    BenchQueueItem,
    PerformanceSummary,
)
from bcap_contracts.certification import CertificationRecord
from bcap_contracts.common import AssessorLevel
from bcap_contracts.entities import PipelineStage, Prospect
from bcap_contracts.learning import CertificationCredit, DrillCard, LearningModule

from grassmarket.workbench.certification import next_level, promotion_blockers

# Pipeline stages that count as "converted" for the advisor's own conversion rate — a prospect that
# reached a signed engagement or beyond. Earlier stages (and NURTURE) are not yet conversions.
_CONVERTED_STAGES = frozenset(
    {
        PipelineStage.CONTRACTED,
        PipelineStage.ACTIVE,
        PipelineStage.DELIVERED,
        PipelineStage.CLOSED,
    }
)
# Early-stage prospects worth a bench-time research nudge (sourcing credit already the advisor's).
_RESEARCHABLE_STAGES = (PipelineStage.PROSPECT, PipelineStage.NURTURE)


def _level_label(level_value: str) -> str:
    return level_value.replace("_", " ").title()


def _certification_spec(
    record: CertificationRecord, next_coursework: LearningModule | None
) -> tuple[str, str, str, object] | None:
    """(title, detail, action_hint, ref_id) for the next certification step, or None if the advisor
    is already Certified Lead (nothing above to work toward)."""
    target = next_level(record.level)
    if target is None:
        return None
    label = _level_label(target.value)
    blockers = promotion_blockers(record, target)
    if not blockers:
        # Evidence is in, but the promotion itself is admin-recorded (ADR-0013).
        return (
            f"Ready to advance to {label}",
            "All evidence is in — ask an admin to record the promotion.",
            "await-admin",
            None,
        )
    # Coursework only blocks the TRAINED→SHADOW rung (Methodology §9); above that the blockers are
    # experiential (shadows, observed lead, sign-off). Only point at coursework when it is genuinely
    # the current blocker — an admin OVERRIDE could leave coursework incomplete at a higher rung.
    if (
        target is AssessorLevel.SHADOW
        and not record.coursework_complete
        and next_coursework is not None
    ):
        return (
            f"Complete coursework: {next_coursework.title}",
            f"Coursework is required to advance to {label}.",
            "complete",
            next_coursework.id,
        )
    # Otherwise surface the single most-blocking requirement as guidance.
    return (f"Advance to {label}", blockers[0], "progress", None)


def _research_spec(prospect: Prospect | None) -> tuple[str, str, str, object]:
    if prospect is not None:
        return (
            f"Opportunity Radar: research {prospect.company_name}",
            "Deepen sourcing on one of your early-stage prospects to move it forward.",
            "research",
            prospect.id,
        )
    return (
        "Opportunity Radar",
        "No idle-time task outstanding — scan for new sourcing opportunities.",
        "research",
        None,
    )


def assemble_queue(
    *,
    cert_record: CertificationRecord,
    next_coursework: LearningModule | None,
    due_drills: Sequence[DrillCard],
    arena_scenario: ArenaScenario | None,
    research_prospect: Prospect | None,
) -> tuple[BenchQueueItem, ...]:
    """The advisor's prioritised bench queue (highest priority first). Only applicable items appear,
    in the fixed priority order; the Opportunity Radar research task is always the tail item."""
    specs: list[tuple[BenchItemKind, str, str, str, object]] = []

    cert = _certification_spec(cert_record, next_coursework)
    if cert is not None:
        specs.append((BenchItemKind.CERTIFICATION, *cert))

    if due_drills:
        soonest = min(due_drills, key=lambda c: c.due_at)
        n = len(due_drills)
        specs.append(
            (
                BenchItemKind.DRILL,
                f"{n} power drill{'s' if n != 1 else ''} due for review",
                f"Spaced-repetition review keeps recall sharp — next up: {soonest.topic}.",
                "review",
                soonest.id,
            )
        )

    if arena_scenario is not None:
        specs.append(
            (
                BenchItemKind.ARENA,
                f"Practise discovery: {arena_scenario.title}",
                "Rehearse a client discovery and get scored on extraction completeness.",
                "practise",
                arena_scenario.id,
            )
        )

    specs.append((BenchItemKind.RESEARCH, *_research_spec(research_prospect)))

    return tuple(
        BenchQueueItem(
            kind=kind,
            priority=i,
            title=title,
            detail=detail,
            action_hint=action,
            ref_id=ref,  # type: ignore[arg-type]
        )
        for i, (kind, title, detail, action, ref) in enumerate(specs, start=1)
    )


def pick_next_coursework(
    modules: Sequence[LearningModule], completed_module_ids: frozenset
) -> LearningModule | None:
    """The first coursework module the advisor has not yet completed (load order), or None."""
    for module in modules:
        if (
            module.certification_credit is CertificationCredit.COURSEWORK
            and module.id not in completed_module_ids
        ):
            return module
    return None


def pick_arena_scenario(
    scenarios: Sequence[ArenaScenario], sessions: Sequence[ArenaSession]
) -> ArenaScenario | None:
    """A scenario the advisor has not yet attempted (in load order); else the first scenario as a
    re-practice suggestion; None only when the library is empty."""
    attempted = {s.scenario_id for s in sessions}
    for scenario in scenarios:
        if scenario.id not in attempted:
            return scenario
    return scenarios[0] if scenarios else None


def pick_research_prospect(prospects: Sequence[Prospect]) -> Prospect | None:
    """An early-stage prospect (PROSPECT/NURTURE) worth a bench-time research nudge, else None."""
    for prospect in prospects:
        if prospect.stage in _RESEARCHABLE_STAGES:
            return prospect
    return None


def summarise_performance(
    *,
    owner_consultant_id,
    cert_record: CertificationRecord,
    engagement_statuses: Sequence[str],
    prospect_stages: Sequence[PipelineStage],
    due_drill_count: int,
    drill_streaks: Sequence[int],
    arena_sessions: Sequence[ArenaSession],
) -> PerformanceSummary:
    """Fold the advisor's own records into a self-development picture (deterministic)."""
    active = sum(1 for s in engagement_statuses if s == "active")
    completed = sum(1 for s in engagement_statuses if s in ("delivered", "closed"))

    total_prospects = len(prospect_stages)
    converted = sum(1 for st in prospect_stages if st in _CONVERTED_STAGES)
    conversion = round(converted / total_prospects, 6) if total_prospects else 0.0

    # A scored session always carries both a score and a scored_at; narrow both in one pass so the
    # trend key is a concrete datetime (chronological, earliest first).
    points = [
        (s.scored_at, s.score.completeness)
        for s in arena_sessions
        if s.status is ArenaStatus.SCORED and s.score is not None and s.scored_at is not None
    ]
    points.sort(key=lambda p: p[0])
    trend = tuple(ArenaTrendPoint(scored_at=at, completeness=c) for at, c in points)
    best = max((c for _, c in points), default=None)

    return PerformanceSummary(
        owner_consultant_id=owner_consultant_id,
        level=cert_record.level,
        engagements_active=active,
        engagements_completed=completed,
        prospects_total=total_prospects,
        pipeline_conversion_rate=conversion,
        coursework_complete=cert_record.coursework_complete,
        exam_passed=cert_record.exam_passed,
        drills_due=due_drill_count,
        drill_best_streak=max(drill_streaks, default=0),
        arena_sessions_scored=len(points),
        arena_best_completeness=best,
        arena_trend=trend,
    )
