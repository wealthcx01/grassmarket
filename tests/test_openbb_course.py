"""OpenBB product course tests (GRS-0126).

The acceptance: a rich, use-case-aligned OpenBB course exists in the CMS, built on the GRS-0123
template so its commission section resolves LIVE from the Earnings v7 schedule; it is deep
(multiple modules of research-grounded content); it seeds idempotently; and completing it counts
toward the `product:openbb` certification (GRS-0127) via the `product-openbb` slug.
"""

from __future__ import annotations

from datetime import UTC, datetime

from bcap_contracts.commissions import load_commission_config
from bcap_contracts.learning import CourseTree, SlideKind

from grassmarket.data.repository import Repository
from grassmarket.earnings.product_carrot import product_commission_carrot
from grassmarket.workbench.content.depth import (
    MAX_SLIDES_PER_LESSON,
    MIN_DOING_SLIDES_PER_LESSON,
    MIN_QUESTIONS_PER_SECTION_TEST,
    MIN_SLIDES_PER_LESSON,
    assert_meets_standard,
)
from grassmarket.workbench.content.openbb_course import (
    OPENBB_PRODUCT_ID,
    OPENBB_SLUG,
    openbb_course,
)
from grassmarket.workbench.content.openbb_slides import (
    SECTIONS_AUTHORED,
    SECTIONS_PLANNED,
    rebuilt_sections,
)
from grassmarket.workbench.content.seed import seed_academy_content
from grassmarket.workbench.course_certs import product_subject_key
from tests.conftest import SeededConsultant

_NOW = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def _carrot():
    return product_commission_carrot(OPENBB_PRODUCT_ID, load_commission_config())


def test_course_is_deep_and_multi_module() -> None:
    """Depth is now counted in SLIDES, not lessons.

    This test used to assert 18-plus lessons, which the four superseded reference modules supplied.
    They were deleted on 2026-07-30 once all eight rebuilt sections existed, so the shape changed:
    eight rebuilt sections of one deep lesson each, plus the template spine. Fewer lessons, and
    roughly ten times the content — which is the whole point of the rebuild, so the assertion moves
    to the measure that reflects it."""
    tree = openbb_course(_carrot())
    assert len(tree.modules) == 1 + len(rebuilt_sections())
    lessons = [lesson for m in tree.modules for lesson in m.lessons]
    for lesson in lessons:
        assert lesson.body.strip() and lesson.drill_topics
    # Every rebuilt lesson carries a measurement; the spine's commission lessons do not.
    assert sum(1 for lesson in lessons if lesson.measurement) >= len(rebuilt_sections())
    # The real depth measure: nearly 200 slides across the eight sections.
    assert sum(len(lesson.slides) for lesson in lessons) >= 160


def test_commission_section_resolves_live_not_hardcoded() -> None:
    carrot = _carrot()
    tree = openbb_course(carrot)
    commission_lessons = [
        lesson for m in tree.modules for lesson in m.lessons if lesson.title == "How much you earn"
    ]
    assert len(commission_lessons) == 1
    body = commission_lessons[0].body
    # The live rate + schedule version appear (from the Earnings v7 compute, not typed in).
    assert carrot.schedule_version in body


def test_content_covers_the_key_sellable_facts() -> None:
    """The same accuracy anchors as before, read from SLIDES as well as lesson bodies.

    They used to live in the reference modules' bodies. Deleting those modules would have made this
    test pass vacuously if it had been deleted with them, and fail wrongly if left as it was — so it
    is re-pointed at where the content actually lives now. The anchors themselves are unchanged,
    because they are the things the research pass said must not go missing."""
    tree = openbb_course(_carrot())
    text = " ".join(
        part
        for m in tree.modules
        for lesson in m.lessons
        for part in [lesson.body, *(s.title + " " + s.body for s in lesson.slides)]
    ).lower()
    for fact in ("workspace", "open data platform", "agplv3", "mcp", "widget", "grounded"):
        assert fact in text, f"the course does not mention {fact!r}"
    # The honest positioning is present: OpenBB does not claim Bloomberg parity.
    assert "bloomberg" in text
    # Two anchors from the ORIGINAL research pass are deliberately gone with the reference modules:
    # "Gamestonk" (the founder-story origin of the sunset free terminal) and "Snowflake" (one named
    # example of connecting a firm's own database). Both were colour rather than sellable fact — the
    # pivot is covered by the two-products slide and the Bloomberg positioning, and connecting
    # internal databases is covered generically. MCP was NOT colour, so it was written into the
    # rebuilt section 1 rather than dropped. Recording the distinction here so a future reader can
    # see it was a decision.


def test_seed_publishes_openbb_and_aligns_with_the_product_cert(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    published = repo.get_published_course(alice.principal, OPENBB_SLUG)
    assert published.tree.title == "OpenBB — product course"
    assert len(published.tree.modules) == 1 + len(rebuilt_sections())

    # The slug backs the product:openbb certification subject (GRS-0127).
    from grassmarket.workbench.course_certs import course_cert_subjects

    subj = next(
        s for s in course_cert_subjects(["openbb"]) if s.key == product_subject_key("openbb")
    )
    assert subj.backing_slug == OPENBB_SLUG


def test_seed_is_idempotent(repo: Repository, admin: SeededConsultant) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    seed_academy_content(repo, admin.principal, now=_NOW)
    versions = repo.list_course_versions(admin.principal, OPENBB_SLUG)
    assert [v.version for v in versions] == [1, 2]
    ids_v1 = [lesson.id for m in versions[0].tree.modules for lesson in m.lessons]
    ids_v2 = [lesson.id for m in versions[1].tree.modules for lesson in m.lessons]
    assert ids_v1 == ids_v2  # stable uuid5 ids across re-seeds


# --- The GRS-0216 rebuild ------------------------------------------------------------------
# The founder asked for one thing above all: an advisor who finishes this course has OpenBB
# installed, workspaces built, and knows how and when to sell it. Two halves are held here — the
# sections written so far meet the depth standard, and the course keeps FAILING to be finished
# until every section is written. The second half matters more: GRS-0191 shipped a renderer and no
# content and still read as progress, and a test that goes green with six sections missing would
# let that happen again.

_DOING = frozenset({SlideKind.WALKTHROUGH, SlideKind.EXAMPLE, SlideKind.CHECKPOINT})


def _rebuilt_tree() -> CourseTree:
    return CourseTree(title="OpenBB", summary="The OpenBB course.", modules=rebuilt_sections())


def test_the_rebuilt_sections_meet_the_depth_standard() -> None:
    assert_meets_standard("product-openbb", _rebuilt_tree())


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
                f"{module.title!r} / {lesson.title!r} is mostly reading"
            )


def test_every_rebuilt_section_ends_in_a_real_test() -> None:
    for module in rebuilt_sections():
        assert module.section_test is not None, f"{module.title!r} has no gate"
        assert len(module.section_test.questions) >= MIN_QUESTIONS_PER_SECTION_TEST


def test_every_test_question_explains_its_answer() -> None:
    """A gate that only says "wrong" teaches nothing, and this gate exists to teach."""
    for module in rebuilt_sections():
        assert module.section_test is not None
        for q in module.section_test.questions:
            assert len(q.explanation.strip()) >= 40, f"{module.title!r}: {q.prompt!r}"


def test_every_claim_carries_a_source() -> None:
    """The failure being corrected was content summarised from memory."""
    for module in rebuilt_sections():
        for lesson in module.lessons:
            refs = list(lesson.references) + [r for s in lesson.slides for r in s.references]
            assert refs, f"{module.title!r} / {lesson.title!r} cites nothing"
            for ref in refs:
                assert ref.url.startswith("https://")


def test_the_install_section_shows_the_commands_an_advisor_actually_runs() -> None:
    """A section on installing that never shows the install command is the old failure in a new
    shape."""
    install = next(m for m in rebuilt_sections() if "Install" in m.title)
    text = "\n".join(s.body for lesson in install.lessons for s in lesson.slides)
    for command in ("pip install openbb", "from openbb import obb", "openbb-build"):
        assert command in text, f"the install section never shows {command!r}"


def test_the_course_is_finished() -> None:
    """This replaces test_the_course_is_not_finished_and_says_so, which failed while any section
    was unwritten and told whoever wrote the last one to delete it. All eight are written."""
    assert not SECTIONS_PLANNED
    assert len(SECTIONS_AUTHORED) == len(rebuilt_sections()) == 8


def test_the_plan_covers_every_clause_of_the_founders_outcome() -> None:
    """ "download, sign up to OpenBB, create their own workspaces (multiple) and know exactly how
    and when to sell it" — every clause has to be a section somewhere."""
    everything = set(SECTIONS_AUTHORED) | set(SECTIONS_PLANNED)
    for required in (
        "install",
        "sign-up-and-orientation",
        "first-workspace",
        "second-workspace",
        "how-and-when-to-sell",
    ):
        assert required in everything, f"nothing in the plan delivers {required!r}"


def test_an_authored_section_is_not_still_listed_as_planned() -> None:
    assert not (set(SECTIONS_AUTHORED) & set(SECTIONS_PLANNED))
