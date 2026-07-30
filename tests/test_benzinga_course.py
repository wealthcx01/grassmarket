"""Benzinga product course tests (GRS-0124).

The acceptance: a deep, use-case-aligned Benzinga course exists in the CMS on the GRS-0123 base so
its commission section resolves LIVE (the advisor's 15% share); it covers the key sellable facts +
honest caveats; it seeds idempotently; and completing it counts toward the `product:benzinga`
certification.
"""

from __future__ import annotations

from datetime import UTC, datetime

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
    """Rebuilt sections + the canonical product spine + the four retained reference modules.

    Derived rather than hard-coded: this used to assert 5, and GRS-0217 adding rebuilt sections
    broke it. A count computed from the parts stays true as the rebuild lands section by section,
    and still fails if a module goes missing."""
    return len(rebuilt_sections()) + 1 + 4


def test_course_is_deep_and_multi_module() -> None:
    tree = benzinga_course(_carrot())
    assert len(tree.modules) == _expected_module_count()
    lessons = [lesson for m in tree.modules for lesson in m.lessons]
    assert len(lessons) >= 18
    for lesson in lessons:
        assert lesson.body.strip() and lesson.drill_topics


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
    text = " ".join(lesson.body for m in benzinga_course(_carrot()).modules for lesson in m.lessons)
    lower = text.lower()
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


def test_the_course_is_not_finished_and_says_so() -> None:
    """Delete this test the day `SECTIONS_PLANNED` empties, and not before.

    It exists because GRS-0191 shipped a renderer with no content and still read as progress. Two
    sections out of eight is the same trap at a smaller scale: real work, genuinely done, that a
    reader could easily mistake for a finished course.
    """
    assert SECTIONS_PLANNED, (
        "SECTIONS_PLANNED is empty, so the Benzinga rebuild is complete. Remove 'product-benzinga' "
        "from depth.LEGACY_COURSES, assert the whole tree against the standard, and delete this "
        "test — that is what its own failure is asking for."
    )
    assert len(SECTIONS_AUTHORED) == len(rebuilt_sections())
    assert not set(SECTIONS_AUTHORED) & set(SECTIONS_PLANNED)


def test_the_legacy_exemption_is_still_recorded() -> None:
    """While the rebuild is partial the assembled tree still holds reference modules with no test,
    so the course stays exempt from the whole-tree check. An exemption nobody can see is how the
    last rebuild quietly did not happen, so it lives in LEGACY_COURSES with the clearing ticket."""
    assert LEGACY_COURSES.get("product-benzinga") == "GRS-0217"


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
