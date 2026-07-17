"""Sales Egoist core module tests (GRS-0122).

The three acceptance criteria: all 8 lessons exist as structured CMS content, each with a drill and
a measurement; each lesson ties to assessment work across the three operating models (retail
brokerage / wealth / exchange); and the module is flagged mandatory-first so it sorts to the front
of the learner catalog. Plus: the seed is idempotent (safe to re-apply).
"""

from __future__ import annotations

from datetime import UTC, datetime

from grassmarket.data.repository import Repository
from grassmarket.workbench.content.sales_egoist import (
    SALES_EGOIST_SLUG,
    sales_egoist_course,
)
from grassmarket.workbench.content.seed import seed_academy_content
from tests.conftest import SeededConsultant

_NOW = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
_OPERATING_MODELS = ("retail brokerage", "wealth", "exchange")


def test_eight_structured_lessons_each_with_drill_and_measurement() -> None:
    tree = sales_egoist_course()
    lessons = [lesson for module in tree.modules for lesson in module.lessons]
    assert len(lessons) == 8
    for lesson in lessons:
        assert lesson.body.strip()  # structured content, not an empty pointer
        assert lesson.drill_topics  # a drill
        assert lesson.measurement  # a measurement


def test_each_lesson_ties_to_all_three_operating_models() -> None:
    tree = sales_egoist_course()
    for module in tree.modules:
        for lesson in module.lessons:
            body = lesson.body.lower()
            for model in _OPERATING_MODELS:
                assert model in body, f"{lesson.title!r} does not tie to {model!r}"


def test_module_is_flagged_mandatory_first() -> None:
    assert sales_egoist_course().mandatory_first is True


def test_lesson_ids_are_stable_across_builds() -> None:
    # Derived (uuid5) ids → re-seeding keeps every lesson's identity (idempotent).
    first = [lesson.id for module in sales_egoist_course().modules for lesson in module.lessons]
    second = [lesson.id for module in sales_egoist_course().modules for lesson in module.lessons]
    assert first == second


def test_seed_publishes_and_sorts_mandatory_first(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    # Another (non-mandatory) course exists first — the seed must still sort ahead of it.
    repo.create_course(admin.principal, slug="other", title="Other", summary="S")
    repo.save_course_draft(
        admin.principal,
        "other",
        sales_egoist_course().model_copy(update={"mandatory_first": False}),
    )
    repo.publish_course(admin.principal, "other", now=_NOW)

    seed_academy_content(repo, admin.principal, now=_NOW)

    published = repo.list_published_courses(alice.principal)
    assert published[0].tree.mandatory_first is True  # sorts to the front
    assert published[0].slug == SALES_EGOIST_SLUG


def test_seed_is_idempotent(repo: Repository, admin: SeededConsultant) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    seed_academy_content(repo, admin.principal, now=_NOW)  # re-apply
    versions = repo.list_course_versions(admin.principal, SALES_EGOIST_SLUG)
    # Two publishes → two retained versions, identical content, same lesson ids.
    assert [v.version for v in versions] == [1, 2]
    ids_v1 = [lesson.id for m in versions[0].tree.modules for lesson in m.lessons]
    ids_v2 = [lesson.id for m in versions[1].tree.modules for lesson in m.lessons]
    assert ids_v1 == ids_v2
