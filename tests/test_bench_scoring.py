"""Golden-master + property tests for the bench queue assembler and performance aggregation
(GRS-0026). The priority ORDER of the queue is the product decision, so it is pinned exactly for the
three canonical advisor states named in the ticket (fresh, mid-certification, fully-certified with
due drills). Pure functions — no DB, no clock — so the fixtures are built directly.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from bcap_contracts.arena import ArenaScenario, ArenaScore, ArenaSession, ArenaStatus
from bcap_contracts.bench import BenchItemKind
from bcap_contracts.certification import CertificationRecord
from bcap_contracts.common import AssessorLevel
from bcap_contracts.entities import PipelineStage, Prospect
from bcap_contracts.learning import CertificationCredit, DrillCard, LearningModule

from grassmarket.workbench.bench import (
    assemble_queue,
    pick_arena_scenario,
    pick_next_coursework,
    pick_research_prospect,
    summarise_performance,
)

_NOW = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)
_OWNER = uuid4()


def _owned() -> dict:
    return {"id": uuid4(), "owner_consultant_id": _OWNER, "created_at": _NOW, "updated_at": _NOW}


def _record(
    level: AssessorLevel, *, coursework: bool = False, exam: float | None = None
) -> CertificationRecord:
    return CertificationRecord(
        **_owned(), level=level, coursework_complete=coursework, exam_score=exam
    )


def _coursework_module(title: str = "The Bruntsfield Playbook") -> LearningModule:
    from bcap_contracts.learning import LearningKind

    return LearningModule(
        **_owned(),
        kind=LearningKind.PLAYBOOK,
        title=title,
        methodology_ref="§1",
        certification_credit=CertificationCredit.COURSEWORK,
    )


def _drill(topic: str, *, due: datetime, streak: int = 0) -> DrillCard:
    return DrillCard(**_owned(), topic=topic, due_at=due, streak=streak)


def _scenario(title: str = "Meridian discovery") -> ArenaScenario:
    from bcap_contracts.arena import ArenaPowerTarget

    return ArenaScenario(
        **_owned(),
        title=title,
        brief="b",
        client_persona="p",
        target_powers=(
            ArenaPowerTarget(power_key="SCALE_ECONOMIES", benefit_cues=("x",), barrier_cues=("y",)),
        ),
    )


def _prospect(stage: PipelineStage, name: str = "Acme Broking") -> Prospect:
    return Prospect(**_owned(), company_name=name, stage=stage, stage_entered_at=_NOW)


# --- Golden master: the three canonical advisor states -----------------------------------


def test_queue_for_a_fresh_advisor() -> None:
    # Trained, no coursework, no drills due, an arena scenario available, an early-stage prospect.
    queue = assemble_queue(
        cert_record=_record(AssessorLevel.TRAINED),
        next_coursework=_coursework_module(),
        due_drills=[],
        arena_scenario=_scenario(),
        research_prospect=_prospect(PipelineStage.PROSPECT),
    )
    assert [i.kind for i in queue] == [
        BenchItemKind.CERTIFICATION,
        BenchItemKind.ARENA,
        BenchItemKind.RESEARCH,
    ]
    assert [i.priority for i in queue] == [1, 2, 3]
    assert queue[0].title.startswith("Complete coursework:")
    assert queue[0].action_hint == "complete"


def test_queue_for_a_mid_certification_advisor() -> None:
    # Coursework done but exam not passed → the certification item is exam guidance, not coursework.
    queue = assemble_queue(
        cert_record=_record(AssessorLevel.TRAINED, coursework=True, exam=None),
        next_coursework=None,
        due_drills=[_drill("power:SCALE_ECONOMIES", due=_NOW)],
        arena_scenario=_scenario(),
        research_prospect=None,
    )
    assert [i.kind for i in queue] == [
        BenchItemKind.CERTIFICATION,
        BenchItemKind.DRILL,
        BenchItemKind.ARENA,
        BenchItemKind.RESEARCH,
    ]
    assert "exam" in queue[0].detail.lower()
    assert queue[0].action_hint == "progress"


def test_queue_for_a_fully_certified_advisor_with_due_drills() -> None:
    # Certified Lead → no certification item; due drills lead, then arena, then research.
    due = [
        _drill("power:NETWORK_ECONOMIES", due=_NOW - timedelta(days=1)),
        _drill("module:OEMS", due=_NOW),
    ]
    queue = assemble_queue(
        cert_record=_record(AssessorLevel.CERTIFIED_LEAD, coursework=True, exam=0.9),
        next_coursework=None,
        due_drills=due,
        arena_scenario=_scenario(),
        research_prospect=_prospect(PipelineStage.NURTURE),
    )
    assert [i.kind for i in queue] == [
        BenchItemKind.DRILL,
        BenchItemKind.ARENA,
        BenchItemKind.RESEARCH,
    ]
    # The drill item counts all due cards and points at the soonest-due one.
    assert queue[0].title.startswith("2 power drills")
    assert queue[0].ref_id == due[0].id  # the earlier due_at


# --- Properties --------------------------------------------------------------------------


def test_research_is_always_the_tail_item() -> None:
    queue = assemble_queue(
        cert_record=_record(AssessorLevel.CERTIFIED_LEAD, coursework=True, exam=0.9),
        next_coursework=None,
        due_drills=[],
        arena_scenario=None,
        research_prospect=None,
    )
    assert queue[-1].kind is BenchItemKind.RESEARCH
    # Even with nothing else actionable, the advisor always has a next action.
    assert len(queue) == 1


def test_priorities_are_contiguous_and_ascending() -> None:
    queue = assemble_queue(
        cert_record=_record(AssessorLevel.TRAINED),
        next_coursework=_coursework_module(),
        due_drills=[_drill("t", due=_NOW)],
        arena_scenario=_scenario(),
        research_prospect=_prospect(PipelineStage.PROSPECT),
    )
    assert [i.priority for i in queue] == list(range(1, len(queue) + 1))


def test_coursework_item_only_when_coursework_is_the_actual_blocker() -> None:
    # An admin override can leave an advisor above TRAINED with coursework still incomplete. At the
    # SHADOW→OBSERVED_LEAD rung the blocker is experiential, so the queue must point there — NOT at
    # coursework — even though coursework_complete is False and a coursework module exists.
    queue = assemble_queue(
        cert_record=_record(AssessorLevel.SHADOW, coursework=False),
        next_coursework=_coursework_module(),
        due_drills=[],
        arena_scenario=None,
        research_prospect=None,
    )
    cert = queue[0]
    assert cert.kind is BenchItemKind.CERTIFICATION
    assert cert.action_hint == "progress"
    assert "observed lead" in cert.detail.lower()
    assert "coursework" not in cert.title.lower()


def test_empty_arena_library_yields_no_arena_item() -> None:
    queue = assemble_queue(
        cert_record=_record(AssessorLevel.CERTIFIED_LEAD, coursework=True, exam=0.9),
        next_coursework=None,
        due_drills=[],
        arena_scenario=None,
        research_prospect=None,
    )
    assert BenchItemKind.ARENA not in [i.kind for i in queue]


# --- pickers -----------------------------------------------------------------------------


def test_pick_next_coursework_skips_completed_and_non_coursework() -> None:
    from bcap_contracts.learning import LearningKind

    done = _coursework_module("Done module")
    primer = LearningModule(
        **_owned(),
        kind=LearningKind.TECHNICAL_PRIMER,
        title="A primer",
        methodology_ref="§2",
        certification_credit=CertificationCredit.NONE,
    )
    todo = _coursework_module("Still to do")
    picked = pick_next_coursework([done, primer, todo], frozenset({done.id}))
    assert picked is todo


def test_pick_arena_scenario_prefers_unattempted() -> None:
    a, b = _scenario("A"), _scenario("B")
    session = ArenaSession(
        **_owned(), scenario_id=a.id, status=ArenaStatus.IN_PROGRESS, transcript=()
    )
    assert pick_arena_scenario([a, b], [session]) is b


def test_pick_research_prospect_only_early_stage() -> None:
    contracted = _prospect(PipelineStage.CONTRACTED, "Signed Co")
    nurture = _prospect(PipelineStage.NURTURE, "Cooling Co")
    assert pick_research_prospect([contracted, nurture]) is nurture
    assert pick_research_prospect([contracted]) is None


# --- Performance aggregation -------------------------------------------------------------


def test_performance_summary_golden() -> None:
    # 4 prospects, 2 contracted-or-beyond → 0.5 conversion. 1 active + 1 delivered engagement.
    scored = ArenaSession(
        **_owned(),
        scenario_id=uuid4(),
        status=ArenaStatus.SCORED,
        transcript=(),
        score=ArenaScore(powers=(), modules_evidenced=(), evidence_questions=0, completeness=0.625),
        scored_at=_NOW,
    )
    earlier = ArenaSession(
        **_owned(),
        scenario_id=uuid4(),
        status=ArenaStatus.SCORED,
        transcript=(),
        score=ArenaScore(powers=(), modules_evidenced=(), evidence_questions=0, completeness=0.4),
        scored_at=_NOW - timedelta(days=5),
    )
    summary = summarise_performance(
        owner_consultant_id=_OWNER,
        cert_record=_record(AssessorLevel.SHADOW, coursework=True, exam=0.8),
        engagement_statuses=["active", "delivered", "scoped"],
        prospect_stages=[
            PipelineStage.PROSPECT,
            PipelineStage.QUALIFIED,
            PipelineStage.CONTRACTED,
            PipelineStage.CLOSED,
        ],
        due_drill_count=3,
        drill_streaks=[1, 4, 2],
        arena_sessions=[scored, earlier],
    )
    assert summary.engagements_active == 1
    assert summary.engagements_completed == 1  # delivered (scoped is not complete)
    assert summary.prospects_total == 4
    assert summary.pipeline_conversion_rate == 0.5
    assert summary.coursework_complete is True
    assert summary.exam_passed is True
    assert summary.drills_due == 3
    assert summary.drill_best_streak == 4
    assert summary.arena_sessions_scored == 2
    assert summary.arena_best_completeness == 0.625
    # Trend is chronological (earlier session first).
    assert [round(p.completeness, 3) for p in summary.arena_trend] == [0.4, 0.625]


def test_conversion_rate_is_zero_with_no_prospects() -> None:
    summary = summarise_performance(
        owner_consultant_id=_OWNER,
        cert_record=_record(AssessorLevel.TRAINED),
        engagement_statuses=[],
        prospect_stages=[],
        due_drill_count=0,
        drill_streaks=[],
        arena_sessions=[],
    )
    assert summary.pipeline_conversion_rate == 0.0
    assert summary.arena_best_completeness is None
    assert summary.arena_trend == ()


# --- GRS-0128: governance + Academy folded into the one hub -------------------------------
def test_hub_folds_rating_committee_and_academy_in_priority_order() -> None:
    aid = uuid4()
    queue = assemble_queue(
        cert_record=_record(AssessorLevel.TRAINED),
        next_coursework=_coursework_module(),
        due_drills=[_drill("t", due=_NOW)],
        arena_scenario=_scenario(),
        research_prospect=_prospect(PipelineStage.PROSPECT),
        pending_rating_count=2,
        pending_rating_subject="Meridian Securities",
        pending_rating_ref=aid,
        committee_review_count=1,
        committee_ref=uuid4(),
        academy_course_title="Sales Egoist",
    )
    # Governance first (others are blocked on it), then certification, then Academy, then the rest.
    assert [i.kind for i in queue] == [
        BenchItemKind.RATING_REQUEST,
        BenchItemKind.COMMITTEE,
        BenchItemKind.CERTIFICATION,
        BenchItemKind.ACADEMY,
        BenchItemKind.DRILL,
        BenchItemKind.ARENA,
        BenchItemKind.RESEARCH,
    ]
    assert [i.priority for i in queue] == list(range(1, 8))
    assert queue[0].ref_id == aid
    assert "Meridian Securities" in queue[0].detail
    assert queue[3].title == "Continue the Academy: Sales Egoist"


def test_hub_items_absent_when_nothing_pending() -> None:
    # The defaults add nothing — a plain advisor's queue is unchanged from before GRS-0128.
    queue = assemble_queue(
        cert_record=_record(AssessorLevel.CERTIFIED_LEAD, coursework=True, exam=0.9),
        next_coursework=None,
        due_drills=[],
        arena_scenario=None,
        research_prospect=None,
    )
    kinds = {i.kind for i in queue}
    assert BenchItemKind.RATING_REQUEST not in kinds
    assert BenchItemKind.COMMITTEE not in kinds
    assert BenchItemKind.ACADEMY not in kinds
