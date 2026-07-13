"""Workbench tests (GRS-0024, PRD §6) — Power Drills, learning content, the weekly quiz.

The SM-2 arithmetic is golden-mastered in tests/test_drills_sm2.py; here we pin the three exit
criteria: the drill schedule round-trips deterministically (due → answered → rescheduled by the
algorithm, fixed clock); an AI-generated quiz is unreachable by advisors until approved; and a
learning completion feeds certification evidence.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from grassmarket.data.repository import Repository
from tests.conftest import SeededConsultant, auth_header

# --- Drill scheduling round-trips deterministically (fixed clock) ------------------------


def test_drill_schedule_round_trips_by_sm2(repo: Repository, alice: SeededConsultant) -> None:
    t0 = datetime(2026, 7, 13, 9, 0, tzinfo=UTC)
    card = repo.create_drill_card(alice.principal, topic="power:SCALE_ECONOMIES", now=t0)
    assert card.due_at == t0  # a fresh card is due immediately
    assert card.interval_days == 0 and card.streak == 0

    # First pass (grade 5): interval → 1 day, reps → 1, streak → 1, due → t0 + 1 day.
    after1 = repo.answer_drill_card(alice.principal, card.id, grade=5, now=t0)
    assert after1.repetitions == 1 and after1.interval_days == 1 and after1.streak == 1
    assert after1.due_at == t0 + timedelta(days=1)

    # Second pass (grade 4) a day later: interval → 6 days, reps → 2, streak → 2.
    t1 = t0 + timedelta(days=1)
    after2 = repo.answer_drill_card(alice.principal, card.id, grade=4, now=t1)
    assert after2.repetitions == 2 and after2.interval_days == 6 and after2.streak == 2
    assert after2.due_at == t1 + timedelta(days=6)

    # A lapse (grade 1) resets: interval → 1 day, reps → 0, streak → 0.
    t2 = t1 + timedelta(days=6)
    lapsed = repo.answer_drill_card(alice.principal, card.id, grade=1, now=t2)
    assert lapsed.repetitions == 0 and lapsed.interval_days == 1 and lapsed.streak == 0
    assert lapsed.due_at == t2 + timedelta(days=1)


def test_due_list_reflects_the_schedule(repo: Repository, alice: SeededConsultant) -> None:
    t0 = datetime(2026, 7, 13, 9, 0, tzinfo=UTC)
    card = repo.create_drill_card(alice.principal, topic="module:OEMS", now=t0)
    assert [c.id for c in repo.list_due_drill_cards(alice.principal, now=t0)] == [card.id]
    # After a pass it is scheduled a day out, so it is no longer due at t0.
    repo.answer_drill_card(alice.principal, card.id, grade=5, now=t0)
    assert repo.list_due_drill_cards(alice.principal, now=t0) == []
    # …but it is due again once the interval has elapsed.
    later = t0 + timedelta(days=1)
    assert [c.id for c in repo.list_due_drill_cards(alice.principal, now=later)] == [card.id]


def test_drill_cards_are_owner_scoped(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    created = client.post(
        "/workbench/drills/cards",
        json={"topic": "triad:economic_value"},
        headers=auth_header(alice),
    )
    assert created.status_code == 201
    card_id = created.json()["id"]
    # Bob cannot answer Alice's card, and does not see it in his own list.
    assert (
        client.post(
            f"/workbench/drills/cards/{card_id}/answer", json={"grade": 5}, headers=auth_header(bob)
        ).status_code
        == 404
    )
    assert client.get("/workbench/drills/cards", headers=auth_header(bob)).json() == []


def test_a_duplicate_drill_card_is_refused(client, alice: SeededConsultant) -> None:
    body = {"topic": "power:BRANDING"}
    assert (
        client.post("/workbench/drills/cards", json=body, headers=auth_header(alice)).status_code
        == 201
    )
    dup = client.post("/workbench/drills/cards", json=body, headers=auth_header(alice))
    assert dup.status_code == 409


# --- The weekly quiz: AI-drafted, unreachable until approved (#8) ------------------------


def _propose_quiz(client, admin: SeededConsultant) -> str:
    resp = client.post(
        "/workbench/quizzes",
        json={"title": "Week 28 drill", "topics": ["power:SCALE_ECONOMIES", "module:OEMS"]},
        headers=auth_header(admin),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == "proposed"
    assert len(resp.json()["questions"]) == 2  # one per topic
    return resp.json()["id"]


def test_a_proposed_quiz_is_invisible_to_advisors_until_approved(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    quiz_id = _propose_quiz(client, admin)
    # While proposed: the advisor cannot list or fetch it (it is not shown to exist, #8).
    assert client.get("/workbench/quizzes", headers=auth_header(alice)).json() == []
    assert (
        client.get(f"/workbench/quizzes/{quiz_id}", headers=auth_header(alice)).status_code == 404
    )
    # The admin sees it, though.
    assert any(
        q["id"] == quiz_id
        for q in client.get("/workbench/quizzes", headers=auth_header(admin)).json()
    )

    # Approve → now the advisor can see it.
    approved = client.post(f"/workbench/quizzes/{quiz_id}/approve", headers=auth_header(admin))
    assert approved.status_code == 200 and approved.json()["status"] == "approved"
    assert any(
        q["id"] == quiz_id
        for q in client.get("/workbench/quizzes", headers=auth_header(alice)).json()
    )
    assert (
        client.get(f"/workbench/quizzes/{quiz_id}", headers=auth_header(alice)).status_code == 200
    )


def test_only_an_admin_proposes_approves_or_rejects_a_quiz(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    denied = client.post(
        "/workbench/quizzes", json={"title": "rogue", "topics": ["x"]}, headers=auth_header(alice)
    )
    assert denied.status_code == 403
    quiz_id = _propose_quiz(client, admin)
    assert (
        client.post(f"/workbench/quizzes/{quiz_id}/approve", headers=auth_header(alice)).status_code
        == 403
    )


def test_a_rejected_quiz_stays_hidden_and_cannot_be_re_decided(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    quiz_id = _propose_quiz(client, admin)
    assert (
        client.post(f"/workbench/quizzes/{quiz_id}/reject", headers=auth_header(admin)).status_code
        == 200
    )
    assert (
        client.get(f"/workbench/quizzes/{quiz_id}", headers=auth_header(alice)).status_code == 404
    )
    # Re-deciding a settled quiz is refused.
    assert (
        client.post(f"/workbench/quizzes/{quiz_id}/approve", headers=auth_header(admin)).status_code
        == 409
    )


# --- Learning completion feeds certification evidence (GRS-0023) -------------------------


def _create_module(client, admin, *, kind, credit) -> str:
    body = {
        "kind": kind,
        "title": f"{kind} module",
        "methodology_ref": "Methodology §9",
        "certification_credit": credit,
    }
    resp = client.post("/workbench/learning/modules", json=body, headers=auth_header(admin))
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_completing_coursework_feeds_certification_evidence(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    coursework = _create_module(client, admin, kind="playbook", credit="coursework")
    advisor = str(alice.principal.consultant_id)

    assert (
        client.post(
            f"/workbench/learning/modules/{coursework}/complete",
            json={},
            headers=auth_header(alice),
        ).status_code
        == 200
    )

    # The coursework credit is on her certification record (feeds the human-gated promotion, §9)…
    record = client.get(f"/certification/{advisor}", headers=auth_header(alice)).json()
    assert record["coursework_complete"] is True
    # …but NOT the exam score — that is proctored/admin-recorded, never self-service (ADR-0014).
    assert record["exam_score"] is None
    kinds = {
        e["kind"]
        for e in client.get(f"/certification/{advisor}/events", headers=auth_header(admin)).json()
    }
    assert "coursework_completed" in kinds
    assert "exam_recorded" not in kinds


def test_a_practice_exam_completion_does_not_feed_certification(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    """An exam-quiz is practice content: an advisor's self-reported score is recorded on the
    completion for their own tracking, but it NEVER touches the certification exam evidence."""
    exam = _create_module(client, admin, kind="exam_quiz", credit="none")
    advisor = str(alice.principal.consultant_id)
    completed = client.post(
        f"/workbench/learning/modules/{exam}/complete",
        json={"score": 0.95},
        headers=auth_header(alice),
    )
    assert completed.status_code == 200 and completed.json()["score"] == 0.95
    # The certification record's exam evidence is untouched — no self-attested exam.
    record = client.get(f"/certification/{advisor}", headers=auth_header(alice)).json()
    assert record["exam_score"] is None


def test_a_none_credit_completion_writes_no_certification_evidence(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    module = _create_module(client, admin, kind="technical_primer", credit="none")
    advisor = str(alice.principal.consultant_id)
    client.post(
        f"/workbench/learning/modules/{module}/complete", json={}, headers=auth_header(alice)
    )
    record = client.get(f"/certification/{advisor}", headers=auth_header(alice)).json()
    assert record["coursework_complete"] is False
    events = client.get(f"/certification/{advisor}/events", headers=auth_header(admin)).json()
    assert events == []  # a no-credit completion leaves no certification footprint


def test_learning_modules_are_admin_authored_and_org_readable(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    denied = client.post(
        "/workbench/learning/modules",
        json={"kind": "playbook", "title": "x", "methodology_ref": "§1"},
        headers=auth_header(alice),
    )
    assert denied.status_code == 403
    _create_module(client, admin, kind="technical_primer", credit="none")
    # Any consultant can read the shared library.
    assert len(client.get("/workbench/learning/modules", headers=auth_header(alice)).json()) == 1


def test_completing_a_module_twice_is_refused(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    module = _create_module(client, admin, kind="playbook", credit="none")
    assert (
        client.post(
            f"/workbench/learning/modules/{module}/complete", json={}, headers=auth_header(alice)
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/workbench/learning/modules/{module}/complete", json={}, headers=auth_header(alice)
        ).status_code
        == 409
    )


def test_answering_a_nonexistent_card_is_404(client, alice: SeededConsultant) -> None:
    from uuid import uuid4

    resp = client.post(
        f"/workbench/drills/cards/{uuid4()}/answer", json={"grade": 5}, headers=auth_header(alice)
    )
    assert resp.status_code == 404


def test_a_non_admin_cannot_reject_a_quiz(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    quiz_id = _propose_quiz(client, admin)
    assert (
        client.post(f"/workbench/quizzes/{quiz_id}/reject", headers=auth_header(alice)).status_code
        == 403
    )


def test_endpoints_require_authentication(client) -> None:
    assert client.get("/workbench/drills/cards").status_code == 401
    assert client.get("/workbench/quizzes").status_code == 401
