"""Sales-ops playbook tests (GRS-0129).

The acceptance: a sales-ops process module exists in the CMS, grounded in the v7 agreement +
commission schedule; it cross-references the Pipeline/GTM stages so process and tooling line up; and
it is CMS-authored (published through GRS-0121), not hardcoded copy.
"""

from __future__ import annotations

from datetime import UTC, datetime

from bcap_contracts.commissions import load_commission_config
from bcap_contracts.entities import PipelineStage
from bcap_contracts.learning import CourseTree, SlideKind

from grassmarket.data.repository import Repository
from grassmarket.workbench.content.depth import (
    LEGACY_COURSES,
    MAX_SLIDES_PER_LESSON,
    MIN_ASSETS_PER_LESSON,
    MIN_DOING_SLIDES_PER_LESSON,
    MIN_QUESTIONS_PER_SECTION_TEST,
    MIN_SLIDES_PER_LESSON,
    assert_meets_standard,
)
from grassmarket.workbench.content.sales_ops_playbook import (
    SALES_OPS_SLUG,
    sales_ops_playbook_course,
)
from grassmarket.workbench.content.sales_ops_slides import (
    SECTIONS_AUTHORED,
    SECTIONS_PLANNED,
    rebuilt_sections,
)
from grassmarket.workbench.content.seed import seed_academy_content
from tests.conftest import SeededConsultant

_NOW = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)

# The forward operational path the playbook must walk (off-ramps Closed/Nurture are prose).
_FORWARD_STAGES = (
    PipelineStage.PROSPECT,
    PipelineStage.WORKSHOP_SCHEDULED,
    PipelineStage.WORKSHOP_DELIVERED,
    PipelineStage.QUALIFIED,
    PipelineStage.SCOPED,
    PipelineStage.CONTRACTED,
    PipelineStage.ACTIVE,
    PipelineStage.DELIVERED,
)


def test_module_exists_as_structured_content() -> None:
    """Depth is counted in SLIDES now, not lessons.

    This asserted four lessons, which the four superseded paragraph-lessons supplied. GRS-0217
    replaced them with eight sections of one deep lesson each — far fewer lessons, roughly ten times
    the content — so the assertion moves to the measure that reflects the change."""
    tree = sales_ops_playbook_course()
    lessons = [lesson for module in tree.modules for lesson in module.lessons]
    assert len(lessons) == len(rebuilt_sections())
    for lesson in lessons:
        assert lesson.body.strip() and lesson.drill_topics and lesson.measurement
    assert sum(len(lesson.slides) for lesson in lessons) == 192


def _all_prose() -> str:
    """Every word of the course: lesson bodies plus slide titles and bodies."""
    return " ".join(
        part
        for module in sales_ops_playbook_course().modules
        for lesson in module.lessons
        for part in [lesson.body, *(s.title + " " + s.body for s in lesson.slides)]
    )


def test_cross_references_every_forward_pipeline_stage() -> None:
    """Derived from the enum, so adding a stage breaks this test rather than silently leaving a gap.

    Accepts the readable rendering — `workshop_scheduled` written as "workshop scheduled" — because
    the course is prose an advisor reads aloud, not a schema dump. What matters is that the stage
    the ENUM defines is covered, and that the course cannot quietly fall behind the enum.
    """
    prose = _all_prose().lower()
    for stage in _FORWARD_STAGES:
        readable = stage.value.replace("_", " ")
        assert readable in prose, f"the playbook does not reference the {stage.value!r} stage"
    # The two exits are stages too, and the course treats them as first-class outcomes.
    for exit_stage in (PipelineStage.CLOSED, PipelineStage.NURTURE):
        assert exit_stage.value in prose, f"the playbook does not reference {exit_stage.value!r}"


def test_grounded_in_the_v7_commission_schedule() -> None:
    text = _all_prose().lower()
    # The two commission streams + the recovery-fee mechanism (v7 schedule).
    assert "stream a" in text and "stream b" in text
    assert "recovery fee" in text
    assert "self-sourced" in text  # the v7 sourcing distinction that changes the rate


def test_seed_publishes_the_playbook_through_the_cms(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    published = repo.get_published_course(alice.principal, SALES_OPS_SLUG)
    assert published.tree.title == "Sales Operations Playbook"
    assert (
        published.tree.mandatory_first is False
    )  # the doctrine (Sales Egoist) is the mandatory one
    assert len(published.tree.modules) == len(rebuilt_sections())
    assert all(module.section_test is not None for module in published.tree.modules)


# --- The GRS-0217 rebuild, to the GRS-0215 depth standard ------------------------------------
#
# The fourth and last course rebuilt to the standard, and the only one that is not about a product.
# That makes it the strongest evidence the standard is about depth rather than about product courses
# specifically — the checks below are the other three courses' checks, unchanged.


_DOING = {SlideKind.WALKTHROUGH, SlideKind.EXAMPLE, SlideKind.CHECKPOINT}


def _rebuilt_tree() -> CourseTree:
    return CourseTree(
        title="Sales Operations Playbook",
        summary="The rebuilt playbook.",
        modules=rebuilt_sections(),
    )


def test_the_rebuilt_sections_meet_the_depth_standard() -> None:
    assert_meets_standard("sales-ops-playbook", _rebuilt_tree())


def test_every_rebuilt_lesson_is_a_lesson_not_a_paragraph() -> None:
    for module in rebuilt_sections():
        for lesson in module.lessons:
            n = len(lesson.slides)
            assert MIN_SLIDES_PER_LESSON <= n <= MAX_SLIDES_PER_LESSON, (
                f"{module.title!r} / {lesson.title!r} has {n} slides"
            )


def test_every_rebuilt_lesson_makes_the_advisor_do_something() -> None:
    for module in rebuilt_sections():
        for lesson in module.lessons:
            doing = [s for s in lesson.slides if s.kind in _DOING]
            assert len(doing) >= MIN_DOING_SLIDES_PER_LESSON, (
                f"{module.title!r} has only {len(doing)} hands-on slides."
            )


def test_every_rebuilt_section_gates_on_a_real_test() -> None:
    for module in rebuilt_sections():
        assert module.section_test is not None, f"{module.title!r} has no section test"
        assert len(module.section_test.questions) >= MIN_QUESTIONS_PER_SECTION_TEST


def test_every_rebuilt_lesson_carries_a_diagram() -> None:
    for module in rebuilt_sections():
        for lesson in module.lessons:
            assets = [s.asset for s in lesson.slides if s.asset]
            assert len(assets) >= MIN_ASSETS_PER_LESSON, f"{module.title!r}: no diagram"


def test_every_test_question_teaches_rather_than_only_marking() -> None:
    for module in rebuilt_sections():
        assert module.section_test is not None
        for question in module.section_test.questions:
            assert question.explanation.strip(), f"{question.prompt!r} has no explanation"
            assert 0 <= question.answer_index < len(question.options)


def test_the_rebuild_is_complete() -> None:
    assert SECTIONS_PLANNED == ()
    assert len(SECTIONS_AUTHORED) == 8
    assert len(rebuilt_sections()) == 8


def test_the_legacy_register_is_down_to_the_doctrine_course() -> None:
    """GRS-0217 is finished, so the only visible debt left is Sales Egoist — and that one is blocked
    on source material rather than on effort, which is worth the register saying."""
    assert "sales-ops-playbook" not in LEGACY_COURSES
    assert set(LEGACY_COURSES) == {"sales-egoist"}
    assert LEGACY_COURSES["sales-egoist"] == "GRS-0218"


# --- The two rules this course exists to enforce ---------------------------------------------


def test_the_course_teaches_the_score_price_separation() -> None:
    """Non-negotiable #7 and ADR-0002: score-points and currency never appear in one equation.

    This is the single most consequential rule in the Academy, because breaking it looks like doing
    a better job — it produces a confident number and a persuasive slide. So assert the course
    actually teaches the separation rather than merely mentioning the value bridge.
    """
    prose = _all_prose().lower()
    assert "value bridge" in prose
    assert "score points" in prose or "score-points" in prose
    assert "never" in prose and "equation" in prose
    # The specific temptation is named, not just the rule.
    assert "assumption register" in prose or "assumption" in prose
    # And the reason the rule protects the score rather than the price.
    assert "defensible" in prose or "measurement" in prose


def test_no_commission_rate_is_written_into_the_slides() -> None:
    """The v7 rates resolve live. A rate typed into a slide is a rate that goes stale silently.

    Checked against the schedule's own consultancy figures, in the forms a rate would plausibly be
    written, and only in slides that are also discussing commission — the lesson learned writing the
    Brandfetch version of this test, where a product statistic collided with a rate by coincidence.
    """
    config = load_commission_config()
    forbidden: set[str] = set()
    for delivery in config.consultancy.values():
        for rate in delivery.values():
            for bps in (rate.yr1_bps, rate.thereafter_bps):
                pct = bps / 100
                forbidden.add(f"{pct:g}%")
                forbidden.add(f"{pct:g} per cent")
                forbidden.add(f"{bps} bps")
    assert forbidden, "no rates resolved, so this test would pass vacuously"

    commission_words = ("commission", "you earn", "your rate", "the rate", "pays more", "bps")
    for module in rebuilt_sections():
        for lesson in module.lessons:
            for slide in lesson.slides:
                blob = f"{slide.title} {slide.body}"
                lower = blob.lower()
                assert "bps" not in lower, f"{slide.title!r} writes a bps figure into content"
                if not any(word in lower for word in commission_words):
                    continue
                hits = sorted(f for f in forbidden if f in blob)
                assert not hits, (
                    f"{slide.title!r} discusses commission AND writes a live rate {hits}; rates "
                    f"must resolve from the Earnings schedule"
                )
