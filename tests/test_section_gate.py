"""The section gate (GRS-0226, wiring GRS-0215's contract).

`SectionTest` and `SectionTestAttempt` shipped as contracts with no table, no route and no marker,
so GRS-0215's test-plan item 3 — "a section does not unlock until its predecessor's test is
passed" — had never run against anything. These are the tests it should have had.

Two properties matter more than the rest and are asserted directly: the score is computed from the
published tree rather than taken from the caller, and an attempt is visible only to the advisor who
made it.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from grassmarket.data.repository import ConflictError, NotFoundError, Repository
from grassmarket.workbench.content.openbb_course import OPENBB_SLUG
from grassmarket.workbench.content.seed import seed_academy_content
from tests.conftest import SeededConsultant, auth_header

_NOW = datetime(2026, 7, 30, 9, 0, tzinfo=UTC)


def _sections(repo: Repository, principal, slug: str = OPENBB_SLUG):
    tree = repo.get_published_course(principal, slug).tree
    return sorted(tree.modules, key=lambda m: m.order)


def _right_answers(module) -> list[int]:
    assert module.section_test is not None
    return [q.answer_index for q in module.section_test.questions]


def _wrong_answers(module) -> list[int]:
    """Every answer deliberately wrong: the first option that is not the right one."""
    assert module.section_test is not None
    return [1 if q.answer_index == 0 else 0 for q in module.section_test.questions]


def test_a_correct_attempt_passes_and_a_wrong_one_does_not(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    first = _sections(repo, alice.principal)[0]

    failed = repo.record_section_test_attempt(
        alice.principal, OPENBB_SLUG, first.id, _wrong_answers(first), now=_NOW
    )
    assert failed.passed is False
    assert failed.score == 0.0

    passed = repo.record_section_test_attempt(
        alice.principal, OPENBB_SLUG, first.id, _right_answers(first), now=_NOW
    )
    assert passed.passed is True
    assert passed.score == 1.0


def test_a_retake_is_a_new_row_not_an_update(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    """The record shows how many goes it took — that is the point of append-only here."""
    seed_academy_content(repo, admin.principal, now=_NOW)
    first = _sections(repo, alice.principal)[0]

    repo.record_section_test_attempt(
        alice.principal, OPENBB_SLUG, first.id, _wrong_answers(first), now=_NOW
    )
    repo.record_section_test_attempt(
        alice.principal, OPENBB_SLUG, first.id, _right_answers(first), now=_NOW
    )
    attempts = repo.list_section_test_attempts(alice.principal, OPENBB_SLUG)
    assert len(attempts) == 2
    assert [a.passed for a in attempts] == [False, True]


def test_attempts_are_owner_scoped(
    repo: Repository,
    admin: SeededConsultant,
    alice: SeededConsultant,
    bob: SeededConsultant,
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    first = _sections(repo, alice.principal)[0]

    repo.record_section_test_attempt(
        bob.principal, OPENBB_SLUG, first.id, _right_answers(first), now=_NOW
    )
    assert repo.list_section_test_attempts(alice.principal, OPENBB_SLUG) == []
    assert len(repo.list_section_test_attempts(bob.principal, OPENBB_SLUG)) == 1


def test_the_wrong_number_of_answers_is_refused_not_padded(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    """Padding or truncating would silently mark a question the advisor never saw (#3)."""
    seed_academy_content(repo, admin.principal, now=_NOW)
    first = _sections(repo, alice.principal)[0]

    with pytest.raises(ConflictError):
        repo.record_section_test_attempt(
            alice.principal, OPENBB_SLUG, first.id, _right_answers(first)[:-1], now=_NOW
        )
    assert repo.list_section_test_attempts(alice.principal, OPENBB_SLUG) == []


def test_an_unknown_section_is_refused(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    from uuid import uuid4

    seed_academy_content(repo, admin.principal, now=_NOW)
    with pytest.raises(NotFoundError):
        repo.record_section_test_attempt(alice.principal, OPENBB_SLUG, uuid4(), [0], now=_NOW)


def test_section_one_is_open_and_section_two_is_not(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    progress = repo.section_progress(alice.principal, OPENBB_SLUG)

    assert progress[0].unlocked is True
    assert progress[0].passed is False
    assert progress[0].attempts == 0
    assert progress[0].best_score is None
    assert progress[1].unlocked is False
    # Nothing beyond the first section is reachable before anything is passed.
    assert [p.unlocked for p in progress[2:]] == [False] * len(progress[2:])


def test_passing_a_section_opens_the_next_one_and_only_the_next_one(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    sections = _sections(repo, alice.principal)

    repo.record_section_test_attempt(
        alice.principal, OPENBB_SLUG, sections[0].id, _right_answers(sections[0]), now=_NOW
    )
    progress = repo.section_progress(alice.principal, OPENBB_SLUG)
    assert progress[0].passed is True
    assert progress[1].unlocked is True
    assert progress[2].unlocked is False


def test_a_failed_attempt_does_not_open_the_next_section(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    sections = _sections(repo, alice.principal)

    repo.record_section_test_attempt(
        alice.principal, OPENBB_SLUG, sections[0].id, _wrong_answers(sections[0]), now=_NOW
    )
    progress = repo.section_progress(alice.principal, OPENBB_SLUG)
    assert progress[0].passed is False
    assert progress[0].attempts == 1
    assert progress[0].best_score == 0.0
    assert progress[1].unlocked is False


def test_best_score_is_the_best_not_the_last(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    first = _sections(repo, alice.principal)[0]

    repo.record_section_test_attempt(
        alice.principal, OPENBB_SLUG, first.id, _right_answers(first), now=_NOW
    )
    repo.record_section_test_attempt(
        alice.principal, OPENBB_SLUG, first.id, _wrong_answers(first), now=_NOW
    )
    progress = repo.section_progress(alice.principal, OPENBB_SLUG)
    assert progress[0].best_score == 1.0
    assert progress[0].passed is True


def test_http_sit_a_test_and_read_the_progress(
    repo: Repository,
    admin: SeededConsultant,
    alice: SeededConsultant,
    client: TestClient,
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    sections = _sections(repo, alice.principal)

    before = client.get(
        f"/workbench/courses/{OPENBB_SLUG}/section-progress", headers=auth_header(alice)
    )
    assert before.status_code == 200
    assert before.json()[0]["unlocked"] is True
    assert before.json()[1]["unlocked"] is False

    sat = client.post(
        f"/workbench/courses/{OPENBB_SLUG}/sections/{sections[0].id}/test",
        json={"answers": _right_answers(sections[0])},
        headers=auth_header(alice),
    )
    assert sat.status_code == 201, sat.text
    assert sat.json()["passed"] is True

    after = client.get(
        f"/workbench/courses/{OPENBB_SLUG}/section-progress", headers=auth_header(alice)
    ).json()
    assert after[0]["passed"] is True
    assert after[1]["unlocked"] is True


def test_http_a_short_answer_list_is_a_409_and_an_unknown_course_is_a_404(
    repo: Repository,
    admin: SeededConsultant,
    alice: SeededConsultant,
    client: TestClient,
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    sections = _sections(repo, alice.principal)

    short = client.post(
        f"/workbench/courses/{OPENBB_SLUG}/sections/{sections[0].id}/test",
        json={"answers": _right_answers(sections[0])[:-1]},
        headers=auth_header(alice),
    )
    assert short.status_code == 409

    missing = client.get(
        "/workbench/courses/no-such-course/section-progress", headers=auth_header(alice)
    )
    assert missing.status_code == 404


def test_the_seeded_course_numbers_its_sections_once_each(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    """The OpenBB tree is assembled from three sources — the rebuilt sections, the canonical
    product module and the retained reference sections — and each of them used to number itself
    from zero. Two sections at `order` 0 made the gate read a tie and open section 2 to an advisor
    who had passed nothing, so distinctness is asserted on the real tree, not a fixture."""
    seed_academy_content(repo, admin.principal, now=_NOW)
    orders = [m.order for m in _sections(repo, alice.principal)]

    assert orders == sorted(set(orders)), f"sections share an order number: {orders}"
    assert orders == list(range(len(orders))), f"section numbering has a hole in it: {orders}"


def test_publishing_refuses_a_course_whose_sections_share_an_order(
    repo: Repository, admin: SeededConsultant
) -> None:
    """The guard sits at the publish choke point rather than in the seed, because a gate that
    fails open must be impossible for any tree — seeded, authored or imported."""
    seed_academy_content(repo, admin.principal, now=_NOW)
    tree = repo.get_published_course(admin.principal, OPENBB_SLUG).tree
    clashing = tree.model_copy(
        update={
            "modules": tuple(
                m.model_copy(update={"order": 0}) if i < 2 else m
                for i, m in enumerate(sorted(tree.modules, key=lambda m: m.order))
            )
        }
    )
    repo.save_course_draft(admin.principal, OPENBB_SLUG, clashing)

    with pytest.raises(ConflictError) as exc:
        repo.publish_course(admin.principal, OPENBB_SLUG, now=_NOW)
    assert "distinct order numbers" in str(exc.value)


def test_a_locked_section_cannot_be_sat_at_all(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    """The reader hides a locked section, but hiding is not refusing. The attempt record is the
    auditable one, so a pass recorded against a section that was never opened would describe a
    progression that did not happen."""
    seed_academy_content(repo, admin.principal, now=_NOW)
    sections = _sections(repo, alice.principal)

    with pytest.raises(ConflictError) as exc:
        repo.record_section_test_attempt(
            alice.principal, OPENBB_SLUG, sections[1].id, _right_answers(sections[1]), now=_NOW
        )
    assert "locked" in str(exc.value)

    # Opening it the honest way makes the same call succeed.
    repo.record_section_test_attempt(
        alice.principal, OPENBB_SLUG, sections[0].id, _right_answers(sections[0]), now=_NOW
    )
    second = repo.record_section_test_attempt(
        alice.principal, OPENBB_SLUG, sections[1].id, _right_answers(sections[1]), now=_NOW
    )
    assert second.passed is True
