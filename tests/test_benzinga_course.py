"""Benzinga product course tests (GRS-0124).

The acceptance: a deep, use-case-aligned Benzinga course exists in the CMS on the GRS-0123 base so
its commission section resolves LIVE (the advisor's 15% share); it covers the key sellable facts +
honest caveats; it seeds idempotently; and completing it counts toward the `product:benzinga`
certification.
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import pytest
from bcap_contracts.commissions import load_commission_config
from bcap_contracts.learning import CourseTree, SlideKind

from grassmarket.data.repository import Repository
from grassmarket.earnings.product_carrot import product_commission_carrot
from grassmarket.workbench.content.benzinga_course import (
    BENZINGA_PRODUCT_ID,
    BENZINGA_SLUG,
    benzinga_course,
)
from grassmarket.workbench.content.benzinga_slides import (
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


def _carrot():
    return product_commission_carrot(BENZINGA_PRODUCT_ID, load_commission_config())


def _expected_module_count() -> int:
    """Rebuilt sections plus the canonical product spine. That is all there is now.

    Derived rather than hard-coded: this asserted 5 before the rebuild, then rebuilt + 1 + 4 while
    the four superseded reference modules were still carried, and now rebuilt + 1 since they were
    deleted on 2026-07-30. Computing it from the parts is what made each of those transitions a
    one-line change instead of a hunt."""
    return len(rebuilt_sections()) + 1


def test_course_is_deep_and_multi_module() -> None:
    """Depth is counted in SLIDES, not lessons.

    This asserted 18-plus lessons, which the four superseded reference modules supplied. Deleting
    them changed the shape: eight rebuilt sections of one deep lesson each, plus the spine. Far
    fewer lessons, roughly ten times the content — which is the point of the rebuild, so the
    assertion moves to the measure that reflects it."""
    tree = benzinga_course(_carrot())
    assert len(tree.modules) == _expected_module_count()
    lessons = [lesson for m in tree.modules for lesson in m.lessons]
    for lesson in lessons:
        assert lesson.body.strip() and lesson.drill_topics
    assert sum(len(lesson.slides) for lesson in lessons) == 192


def test_commission_resolves_live_the_advisor_share() -> None:
    carrot = _carrot()
    # The advisor share is 15% (Bruntsfield takes the reseller's 30% and shares half).
    assert carrot.yr1_bps == 1500
    body = next(
        lesson.body
        for m in benzinga_course(carrot).modules
        for lesson in m.lessons
        if lesson.title == "How much you earn"
    )
    assert carrot.schedule_version in body  # from the compute, not typed in


def test_content_covers_the_key_facts_and_caveats() -> None:
    """The same anchors as before, read from SLIDES as well as lesson bodies.

    They used to live in the reference modules' bodies. Deleting those modules would have made this
    test fail wrongly if left as it was, and pass vacuously if deleted with them — so it is
    re-pointed at where the content lives now. The anchors are unchanged, because they are the
    things the original research pass said must not go missing, and "Raznick" was written into the
    rebuilt company-history slide rather than allowed to disappear."""
    tree = benzinga_course(_carrot())
    lower = " ".join(
        part
        for m in tree.modules
        for lesson in m.lessons
        for part in [lesson.body, *(s.title + " " + s.body for s in lesson.slides)]
    ).lower()
    for fact in ("wiim", "analyst rating", "unusual options", "redistribution", "raznick"):
        assert fact in lower, f"the course does not mention {fact!r}"
    # Honest positioning + attribution discipline are present.
    assert "not a terminal" in lower or "not a full institutional terminal" in lower
    assert "not validated alpha" in lower


def test_seed_publishes_and_aligns_with_the_product_cert(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    published = repo.get_published_course(alice.principal, BENZINGA_SLUG)
    assert published.tree.title == "Benzinga — product course"
    assert len(published.tree.modules) == _expected_module_count()

    subj = next(
        s for s in course_cert_subjects(["benzinga"]) if s.key == product_subject_key("benzinga")
    )
    assert subj.backing_slug == BENZINGA_SLUG


def test_seed_is_idempotent(repo: Repository, admin: SeededConsultant) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    seed_academy_content(repo, admin.principal, now=_NOW)
    versions = repo.list_course_versions(admin.principal, BENZINGA_SLUG)
    assert [v.version for v in versions] == [1, 2]
    ids_v1 = [lesson.id for m in versions[0].tree.modules for lesson in m.lessons]
    ids_v2 = [lesson.id for m in versions[1].tree.modules for lesson in m.lessons]
    assert ids_v1 == ids_v2


# --- The GRS-0217 rebuild, to the GRS-0215 depth standard ------------------------------------
#
# This is the second course rebuilt to the standard, so part of the value here is proving the
# standard travels: these are the OpenBB checks re-pointed. Anything that needed special-casing for
# Benzinga would be a sign the standard was only ever about OpenBB.


_DOING = {SlideKind.WALKTHROUGH, SlideKind.EXAMPLE, SlideKind.CHECKPOINT}


def _rebuilt_tree() -> CourseTree:
    return CourseTree(title="Benzinga", summary="The Benzinga course.", modules=rebuilt_sections())


def test_the_rebuilt_sections_meet_the_depth_standard() -> None:
    assert_meets_standard("product-benzinga", _rebuilt_tree())


def test_every_rebuilt_lesson_is_a_lesson_not_a_paragraph() -> None:
    """The founder's number, asserted directly rather than only through the shared checker."""
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
                f"{module.title!r} has only {len(doing)} hands-on slides. Reading is not learning."
            )


def test_every_rebuilt_section_gates_on_a_real_test() -> None:
    for module in rebuilt_sections():
        assert module.section_test is not None, f"{module.title!r} has no section test"
        assert len(module.section_test.questions) >= MIN_QUESTIONS_PER_SECTION_TEST


def test_every_rebuilt_lesson_carries_a_diagram() -> None:
    """GRS-0225's rule. The OpenBB rebuild met every other rule with 196 slides and no drawing."""
    for module in rebuilt_sections():
        for lesson in module.lessons:
            assets = [s.asset for s in lesson.slides if s.asset]
            assert len(assets) >= MIN_ASSETS_PER_LESSON, f"{module.title!r}: no diagram"


def test_every_test_question_teaches_rather_than_only_marking() -> None:
    """A wrong answer with no explanation teaches nothing, and this gate exists to teach."""
    for module in rebuilt_sections():
        assert module.section_test is not None
        for question in module.section_test.questions:
            assert question.explanation.strip(), f"{question.prompt!r} has no explanation"
            assert 0 <= question.answer_index < len(question.options)


def test_the_rebuild_is_complete() -> None:
    """This replaced `test_the_course_is_not_finished_and_says_so`, which failed while
    `SECTIONS_PLANNED` was non-empty and whose failure message asked to be deleted the day it
    emptied. That day was 2026-07-30, so it was.

    What remains is the assertion in the other direction: eight sections, and nothing still listed
    as planned. The mechanism existed because GRS-0191 shipped a renderer with no content and still
    read as progress; the honest end state is a check that the content is all there."""
    assert SECTIONS_PLANNED == ()
    assert len(SECTIONS_AUTHORED) == 8
    assert len(rebuilt_sections()) == 8
    assert [m.title for m in rebuilt_sections()] == [
        "What Benzinga is, and what it is not",
        "The catalogue, in four families",
        "How it arrives, and what that costs to build",
        "The content layer: what a user reads",
        "The event layer: what a user plans around",
        "The signal layer: what a desk trades on",
        "Who buys which family, and what triggers it",
        "How to sell it",
    ]


def test_benzinga_is_no_longer_carried_as_legacy_debt() -> None:
    """`LEGACY_COURSES` is a visible-debt register, not a switch — nothing in `check_depth` reads
    it, so it never exempted anything mechanically. Benzinga came off it when the rebuild finished.
    The courses still on it are the honest remaining debt, each with the ticket that clears it."""
    assert "product-benzinga" not in LEGACY_COURSES
    # `product-brandfetch` left too, on the same day and for the same reason (GRS-0217 finished it).
    # What is left is the honest remaining debt, each with the ticket that clears it.
    assert set(LEGACY_COURSES) == {"sales-egoist", "sales-ops-playbook"}


def test_the_rebuilt_sections_have_distinct_ids_and_contiguous_orders() -> None:
    """Both halves of the GRS-0226 publish guard, checked where the ids are actually minted. The
    reference modules carry a `reference-` key prefix precisely because the bare key collided with a
    rebuilt section of the same name, and a collision makes one attempt count for two sections."""
    modules = rebuilt_sections()
    ids = [m.id for m in modules]
    assert len(set(ids)) == len(ids)
    assert [m.order for m in modules] == list(range(len(modules)))


def test_the_assembled_course_has_no_id_or_order_collisions(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    """The publish path refuses duplicate ids and duplicate orders, so seeding the real catalogue
    is itself the end-to-end assertion that the assembled Benzinga tree is well formed."""
    seed_academy_content(repo, admin.principal, now=_NOW)
    tree = repo.get_published_course(alice.principal, BENZINGA_SLUG).tree

    ids = [m.id for m in tree.modules]
    assert len(set(ids)) == len(ids)
    assert sorted(m.order for m in tree.modules) == list(range(len(tree.modules)))
    # The rebuilt sections come first: they are the course now.
    ordered = sorted(tree.modules, key=lambda m: m.order)
    assert [m.title for m in ordered][: len(rebuilt_sections())] == [
        m.title for m in rebuilt_sections()
    ]


def test_the_rebuilt_sections_are_reachable_through_the_gate(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    """Section 1 open, section 2 shut, and passing 1 opens 2 — on the real seeded Benzinga tree
    rather than a fixture, because GRS-0226's whole point was that untested wiring is not wiring."""
    seed_academy_content(repo, admin.principal, now=_NOW)
    ordered = sorted(
        repo.get_published_course(alice.principal, BENZINGA_SLUG).tree.modules,
        key=lambda m: m.order,
    )
    first = ordered[0]
    assert first.section_test is not None

    before = repo.section_progress(alice.principal, BENZINGA_SLUG)
    assert before[0].unlocked is True
    assert before[1].unlocked is False

    repo.record_section_test_attempt(
        alice.principal,
        BENZINGA_SLUG,
        first.id,
        [q.answer_index for q in first.section_test.questions],
        now=_NOW,
    )
    after = repo.section_progress(alice.principal, BENZINGA_SLUG)
    assert after[0].passed is True
    assert after[1].unlocked is True


# --- The course's numbers against the source they came from -----------------------------------


def test_the_family_counts_match_the_committed_catalogue() -> None:
    """The course states four counts and a total, so those are checkable against the spreadsheet
    they came from — and they should be, because I got two of them backwards on the first pass and
    the error reached a slide, a test question and a diagram before anyone counted.

    A claim that can be checked against a committed source belongs in a test, not in a proofread.
    """
    openpyxl = pytest.importorskip("openpyxl")
    book = openpyxl.load_workbook(
        Path(__file__).resolve().parents[1] / "data/gtm/sources/benzinga-product-catalog.xlsx",
        data_only=True,
    )
    counts: Counter[str] = Counter()
    for row in list(book["Full Catalog"].iter_rows(values_only=True))[1:]:
        category, name = row[0], row[1]
        # Banded category headers carry a marker glyph and no product name.
        if not category or str(category).strip().startswith("▌") or name is None:
            continue
        counts[str(category).strip()] += 1

    assert counts == {
        "Newswire & Content": 8,
        "Calendar": 11,
        "Alternative Data": 9,
        "Market Data": 4,
    }
    assert sum(counts.values()) == 32

    # Every one of those numbers is quoted somewhere in the rebuilt slides, so assert the slides
    # agree with the sheet rather than with my memory of it.
    prose = " ".join(
        part
        for module in rebuilt_sections()
        for lesson in module.lessons
        for slide in lesson.slides
        for part in (slide.title, slide.body)
    )
    assert "**Newswire & Content** (8)" in prose
    assert "**Calendar** (11)" in prose
    assert "**Alternative Data** (9)" in prose
    assert "**Market Data** (4)" in prose
    assert "32 products" in prose
