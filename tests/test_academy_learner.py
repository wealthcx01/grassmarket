"""Academy learner reads (GRS-0135).

The CMS (GRS-0121) let admins author courses; this closes the learner loop — an advisor reads a
published course and marks lessons complete, and the reader shows their own progress. The read is
owner-scoped: a consultant sees only their own completions, though the course itself is org-wide.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from grassmarket.data.repository import Repository
from grassmarket.workbench.content.sales_ops_playbook import SALES_OPS_SLUG
from grassmarket.workbench.content.seed import seed_academy_content
from tests.conftest import SeededConsultant, auth_header

_NOW = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)


def _first_lesson_ids(repo: Repository, principal, slug: str) -> list:
    tree = repo.get_published_course(principal, slug).tree
    return [lesson.id for module in tree.modules for lesson in module.lessons]


def test_completions_start_empty_then_reflect_a_completed_lesson(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    lessons = _first_lesson_ids(repo, alice.principal, SALES_OPS_SLUG)

    assert repo.list_lesson_completions(alice.principal, SALES_OPS_SLUG) == []

    repo.complete_lesson(alice.principal, SALES_OPS_SLUG, lessons[0], now=_NOW)
    done = repo.list_lesson_completions(alice.principal, SALES_OPS_SLUG)
    assert [c.lesson_id for c in done] == [lessons[0]]
    assert done[0].owner_consultant_id == alice.principal.consultant_id


def test_completions_are_owner_scoped(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    lessons = _first_lesson_ids(repo, alice.principal, SALES_OPS_SLUG)

    repo.complete_lesson(bob.principal, SALES_OPS_SLUG, lessons[0], now=_NOW)
    # Bob's progress is his alone — Alice sees none of it.
    assert repo.list_lesson_completions(alice.principal, SALES_OPS_SLUG) == []
    assert len(repo.list_lesson_completions(bob.principal, SALES_OPS_SLUG)) == 1


def test_http_learner_can_read_catalog_course_and_progress(
    repo: Repository,
    admin: SeededConsultant,
    alice: SeededConsultant,
    client: TestClient,
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)

    # The org-wide learner catalog + single published course are readable by a non-admin advisor.
    catalog = client.get("/workbench/courses/published", headers=auth_header(alice))
    assert catalog.status_code == 200
    assert any(v["slug"] == SALES_OPS_SLUG for v in catalog.json())

    course = client.get(
        f"/workbench/courses/{SALES_OPS_SLUG}/published", headers=auth_header(alice)
    )
    assert course.status_code == 200
    lesson_id = course.json()["tree"]["modules"][0]["lessons"][0]["id"]

    # Progress starts empty, a completion lands, and re-reading reflects it.
    assert (
        client.get(
            f"/workbench/courses/{SALES_OPS_SLUG}/completions", headers=auth_header(alice)
        ).json()
        == []
    )
    done = client.post(
        f"/workbench/courses/{SALES_OPS_SLUG}/lessons/{lesson_id}/complete",
        headers=auth_header(alice),
    )
    assert done.status_code == 200
    progress = client.get(
        f"/workbench/courses/{SALES_OPS_SLUG}/completions", headers=auth_header(alice)
    )
    assert [c["lesson_id"] for c in progress.json()] == [lesson_id]


def test_http_completions_404_for_unknown_course(
    alice: SeededConsultant, client: TestClient
) -> None:
    resp = client.get("/workbench/courses/does-not-exist/completions", headers=auth_header(alice))
    assert resp.status_code == 404
