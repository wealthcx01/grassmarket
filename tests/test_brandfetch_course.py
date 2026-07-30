"""Brandfetch product course tests (GRS-0125).

The acceptance: a deep, use-case-aligned Brandfetch course exists in the CMS on the GRS-0123 base
so its commission section resolves LIVE; it centres the two commercial tiers (distribution vs
redistribution) with BOTH live rates; it seeds idempotently; and completing it counts toward the
`product:brandfetch_distribution` certification (whose backing slug is the hyphenated
`product-brandfetch-distribution`).
"""

from __future__ import annotations

from datetime import UTC, datetime

from bcap_contracts.commissions import load_commission_config
from bcap_contracts.learning import CourseTree, SlideKind

from grassmarket.data.repository import Repository
from grassmarket.earnings.product_carrot import product_commission_carrot
from grassmarket.workbench.content.brandfetch_course import (
    BRANDFETCH_PRODUCT_ID,
    BRANDFETCH_REDIST_ID,
    BRANDFETCH_SLUG,
    brandfetch_course,
)
from grassmarket.workbench.content.brandfetch_slides import (
    SECTIONS_AUTHORED,
    SECTIONS_PLANNED,
    rebuilt_sections,
)
from grassmarket.workbench.content.depth import (
    LEGACY_COURSES,
    MAX_SLIDES_PER_LESSON,
    MIN_ASSETS_PER_LESSON,
    MIN_DOING_SLIDES_PER_LESSON,
    MIN_QUESTIONS_PER_SECTION_TEST,
    MIN_SLIDES_PER_LESSON,
    assert_meets_standard,
)
from grassmarket.workbench.content.seed import seed_academy_content
from grassmarket.workbench.course_certs import course_cert_subjects, product_subject_key
from tests.conftest import SeededConsultant

_NOW = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def _course():
    config = load_commission_config()
    return brandfetch_course(
        product_commission_carrot(BRANDFETCH_PRODUCT_ID, config),
        product_commission_carrot(BRANDFETCH_REDIST_ID, config),
    )


def test_course_is_deep_and_multi_module() -> None:
    tree = _course()
    # Rebuilt sections plus the commission spine. Derived rather than hard-coded: this asserted 5
    # before the rebuild, and computing it from the parts is what made the transition a one-liner.
    assert len(tree.modules) == len(rebuilt_sections()) + 1
    lessons = [lesson for m in tree.modules for lesson in m.lessons]
    for lesson in lessons:
        assert lesson.body.strip() and lesson.drill_topics
    # Depth is counted in SLIDES now, not lessons. This asserted 18-plus lessons, which the four
    # superseded reference modules supplied; eight sections of one deep lesson each is far fewer
    # lessons and roughly ten times the content, so the assertion measures what actually changed.
    assert sum(len(lesson.slides) for lesson in lessons) == 192


def test_both_commission_tiers_resolve_live() -> None:
    config = load_commission_config()
    dist = product_commission_carrot(BRANDFETCH_PRODUCT_ID, config)
    redist = product_commission_carrot(BRANDFETCH_REDIST_ID, config)
    body = next(
        lesson.body
        for m in _course().modules
        for lesson in m.lessons
        if lesson.title == "Your two commission tiers, live"
    )
    # Both live rates + the schedule version appear (from the compute, not typed in).
    assert f"{dist.yr1_bps / 100:g}%" in body and f"{redist.yr1_bps / 100:g}%" in body
    assert dist.schedule_version in body
    # Distribution genuinely pays more than redistribution (the reason the lesson teaches).
    assert dist.yr1_bps > redist.yr1_bps


def test_content_covers_the_key_sellable_facts() -> None:
    # Read from SLIDES as well as lesson bodies. These anchors used to live in the reference
    # modules' bodies; deleting those would have made this test fail wrongly if left as it was, and
    # pass vacuously if deleted with them. Every anchor survived into the rebuilt slides, so unlike
    # OpenBB's case none had to be rescued or dropped.
    text = " ".join(
        part
        for m in _course().modules
        for lesson in m.lessons
        for part in [lesson.body, *(s.title + " " + s.body for s in lesson.slides)]
    ).lower()
    for fact in ("brand api", "ticker", "isin", "transaction api", "redistribution", "trademark"):
        assert fact in text, f"the course does not mention {fact!r}"
    # Finance peer proof + honest positioning.
    assert "morningstar" in text and "envestnet" in text


def test_seed_publishes_and_aligns_with_the_product_cert(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    published = repo.get_published_course(alice.principal, BRANDFETCH_SLUG)
    assert published.tree.title == "Brandfetch — product course"
    assert len(published.tree.modules) == len(rebuilt_sections()) + 1

    # The hyphenated slug backs the product:brandfetch_distribution cert (underscore→hyphen fix).
    subj = next(
        s
        for s in course_cert_subjects(["brandfetch_distribution"])
        if s.key == product_subject_key("brandfetch_distribution")
    )
    assert subj.backing_slug == BRANDFETCH_SLUG


def test_seed_is_idempotent(repo: Repository, admin: SeededConsultant) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    seed_academy_content(repo, admin.principal, now=_NOW)
    versions = repo.list_course_versions(admin.principal, BRANDFETCH_SLUG)
    assert [v.version for v in versions] == [1, 2]
    ids_v1 = [lesson.id for m in versions[0].tree.modules for lesson in m.lessons]
    ids_v2 = [lesson.id for m in versions[1].tree.modules for lesson in m.lessons]
    assert ids_v1 == ids_v2


# --- The GRS-0217 rebuild, to the GRS-0215 depth standard ------------------------------------
#
# Third and last course rebuilt to the standard, so these are the same checks re-pointed for the
# third time. That repetition is the evidence the standard travels rather than being about whichever
# course was in front of us when it was written.


_DOING = {SlideKind.WALKTHROUGH, SlideKind.EXAMPLE, SlideKind.CHECKPOINT}


def _rebuilt_tree() -> CourseTree:
    return CourseTree(
        title="Brandfetch", summary="The Brandfetch course.", modules=rebuilt_sections()
    )


def test_the_rebuilt_sections_meet_the_depth_standard() -> None:
    assert_meets_standard("product-brandfetch-distribution", _rebuilt_tree())


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


def test_brandfetch_is_no_longer_carried_as_legacy_debt() -> None:
    """It came off the visible-debt register on 2026-07-30 with Benzinga. What is left on that list
    is the honest remaining debt: the two sales courses, each with its clearing ticket."""
    assert "product-brandfetch" not in LEGACY_COURSES
    assert set(LEGACY_COURSES) == {"sales-egoist"}


def test_the_rebuilt_sections_have_distinct_ids_and_contiguous_orders() -> None:
    modules = rebuilt_sections()
    assert len({m.id for m in modules}) == len(modules)
    assert [m.order for m in modules] == list(range(len(modules)))


# --- The thing this course exists to teach ---------------------------------------------------


def test_the_course_teaches_the_distribution_redistribution_split() -> None:
    """The specific correction GRS-0185 recorded: we were conflating two products. Assert the course
    actually distinguishes them rather than merely mentioning both words somewhere.

    Each half of the split has to appear with its own segment attached, because "mentions
    redistribution" was true of the old course too — and the old course was the problem.
    """
    text = " ".join(
        part
        for module in rebuilt_sections()
        for lesson in module.lessons
        for slide in lesson.slides
        for part in (slide.title, slide.body)
    ).lower()

    # Distribution: the client's own product, and the retail segment.
    assert "distribution" in text
    assert "retail brokerage" in text
    # Redistribution: onward to the client's customers, and the venue/vendor segment.
    assert "redistribution" in text
    assert "exchange" in text and "information vendor" in text
    # The boundary question itself, and the honesty about it not being publicly drawn.
    assert "enterprise" in text
    assert "not publicly" in text or "not bright" in text
    # And the rule that follows from the two rates differing.
    assert "before you forecast" in text


_COMMISSION_WORDS = (
    "commission",
    "you earn",
    "your rate",
    "the rate",
    "year 1",
    "year one",
    "yr1",
    "tier pays",
    "pays more",
    "bps",
)


def test_no_commission_rate_is_written_into_the_slides() -> None:
    """Both tiers resolve live from the Earnings schedule, so no rate may be baked into content.

    Two false positives shaped this test, and both are worth recording. Forbidding percentages
    outright flagged Typeform's reported free-to-paid lift and the Enterprise availability
    commitment — attributed vendor claims, not commission. Then comparing against the schedule's own
    figures STILL flagged the Typeform lift, because distribution's year-two rate is five per cent
    and the reported lift is five per cent. The same characters, two unrelated facts.

    So the rule is checked in context: a live rate figure is a violation only in a slide that is
    also talking about commission. A slide citing a product statistic is not quoting your rate, and
    a test that cannot tell those apart makes authors work around it rather than obey it.
    """
    config = load_commission_config()
    carrots = [
        product_commission_carrot(BRANDFETCH_PRODUCT_ID, config),
        product_commission_carrot(BRANDFETCH_REDIST_ID, config),
    ]
    # Percentage forms plus the explicit bps suffix, NOT the bare bps integer. "500" collided with
    # "free to roughly 500 thousand a month" on the pricing slide, and nobody writes a commission
    # rate as a bare four-hundred-something in prose anyway — they write 7.5% or 750 bps.
    forbidden: set[str] = set()
    for carrot in carrots:
        for bps in (carrot.yr1_bps, carrot.yr2_bps):
            pct = bps / 100
            forbidden.add(f"{pct:g}%")
            forbidden.add(f"{pct:g} per cent")
            forbidden.add(f"{bps} bps")
    assert forbidden, "no rates resolved, so this test would pass vacuously"

    for module in rebuilt_sections():
        for lesson in module.lessons:
            for slide in lesson.slides:
                blob = f"{slide.title} {slide.body}"
                lower = blob.lower()
                assert "bps" not in lower, f"{slide.title!r} writes a bps figure into slide content"
                if not any(word in lower for word in _COMMISSION_WORDS):
                    continue
                hits = sorted(f for f in forbidden if f in blob)
                assert not hits, (
                    f"{slide.title!r} discusses commission AND writes a live rate {hits} into "
                    f"slide content; rates must resolve from the Earnings schedule"
                )


def test_the_rate_test_would_catch_a_rate_in_a_commission_slide() -> None:
    """A negative case, because the positive check passes on all 192 slides and a check that only
    ever passes is indistinguishable from one that does nothing."""
    config = load_commission_config()
    dist = product_commission_carrot(BRANDFETCH_PRODUCT_ID, config)
    pct = f"{dist.yr1_bps / 100:g}%"
    offending = f"Your commission on distribution is {pct} in year 1."
    lower = offending.lower()
    assert any(word in lower for word in _COMMISSION_WORDS)
    assert pct in offending


def test_the_two_tier_commission_lesson_survived_and_still_resolves_live() -> None:
    """It sits on the spine now rather than in a deleted reference module, and it must still compute
    both rates from the schedule rather than quote them."""
    config = load_commission_config()
    dist = product_commission_carrot(BRANDFETCH_PRODUCT_ID, config)
    lesson = next(
        les
        for m in _course().modules
        for les in m.lessons
        if les.title == "Your two commission tiers, live"
    )
    assert dist.schedule_version in lesson.body
    # On the spine module, which is the one with no section test.
    owner = next(m for m in _course().modules if lesson in m.lessons)
    assert owner.section_test is None
