"""The founder review gate (GRS-0188, ADR-0041).

The gate is a hash comparison, so these tests are mostly about one question: does an edit after
approval genuinely re-open review? If it does not, the gate is decorative.
"""

from __future__ import annotations

from bcap_contracts.assessments import MaturityLevel, RecordProvenance, SubcomponentRating
from fastapi.testclient import TestClient

from tests.conftest import SeededConsultant, auth_header
from tests.founder_review_helpers import current_approval, submit_and_approve

# The scoreable fixture lives with the lifecycle tests. Reused rather than re-hand-rolled, so a
# change to what "scoreable" means cannot leave these tests quietly asserting against a shape the
# product no longer accepts.
from tests.test_assessment_lifecycle import _body, _scoreable_partial_doc


def _edited_doc():
    """The same document with one subcomponent moved. Any edit at all changes the hash; this one is
    just easy to read in a diff."""
    doc = _scoreable_partial_doc()
    original = doc.subcomponents[0]
    moved = SubcomponentRating(
        module_key=original.module_key,
        subcomponent_key=original.subcomponent_key,
        level=MaturityLevel.BASIC,
        evidence_grade=original.evidence_grade,
    )
    return doc.model_copy(update={"subcomponents": (moved,)})


def _new_production_assessment(client: TestClient, owner: SeededConsultant) -> str:
    aid = client.post("/assessments", json={}, headers=auth_header(owner)).json()["id"]
    resp = client.put(
        f"/assessments/{aid}", json=_body(_scoreable_partial_doc()), headers=auth_header(owner)
    )
    assert resp.status_code == 200, resp.text
    return aid


def test_a_production_record_cannot_finalise_without_approval(
    client, alice: SeededConsultant
) -> None:
    aid = _new_production_assessment(client, alice)
    resp = client.post(f"/assessments/{aid}/finalise", headers=auth_header(alice))
    assert resp.status_code == 409
    assert "awaiting founder approval" in resp.json()["detail"]


def test_approval_then_edit_re_opens_review(
    client, alice: SeededConsultant, founder: SeededConsultant
) -> None:
    """The whole mechanism in one test. Approve, edit, and the approval stops counting."""
    aid = _new_production_assessment(client, alice)
    submit_and_approve(client, aid, alice, founder)
    assert current_approval(client, aid, alice) is not None

    # Any edit at all changes the hash. Here, one subcomponent drops a level.
    client.put(f"/assessments/{aid}", json=_body(_edited_doc()), headers=auth_header(alice))

    assert current_approval(client, aid, alice) is None
    refused = client.post(f"/assessments/{aid}/finalise", headers=auth_header(alice))
    assert refused.status_code == 409
    assert "awaiting founder approval" in refused.json()["detail"]

    # Re-approving at the new version unblocks it again.
    submit_and_approve(client, aid, alice, founder)
    assert (
        client.post(f"/assessments/{aid}/finalise", headers=auth_header(alice)).status_code == 200
    )


def test_only_the_founder_may_approve(
    client, alice: SeededConsultant, admin: SeededConsultant
) -> None:
    """Not the owner, and not an admin. An admin bypass would reintroduce self-approval by the back
    door, which is the thing non-negotiable #8 exists to stop."""
    aid = _new_production_assessment(client, alice)
    own = client.post(f"/assessments/{aid}/founder-approval", headers=auth_header(alice))
    assert own.status_code == 403
    by_admin = client.post(f"/assessments/{aid}/founder-approval", headers=auth_header(admin))
    assert by_admin.status_code == 403
    assert current_approval(client, aid, alice) is None


def test_a_sandbox_record_still_finalises_alone(client, alice: SeededConsultant) -> None:
    """ADR-0029 is untouched: a watermarked record with no client on the other end needs nobody."""
    aid = client.post(
        "/assessments",
        json={"provenance": RecordProvenance.SANDBOX.value},
        headers=auth_header(alice),
    ).json()["id"]
    client.put(
        f"/assessments/{aid}", json=_body(_scoreable_partial_doc()), headers=auth_header(alice)
    )
    assert (
        client.post(f"/assessments/{aid}/finalise", headers=auth_header(alice)).status_code == 200
    )


def test_the_queue_is_founder_only_and_production_only(
    client,
    alice: SeededConsultant,
    bob: SeededConsultant,
    founder: SeededConsultant,
) -> None:
    production = _new_production_assessment(client, alice)
    client.post(f"/assessments/{production}/submit-for-review", headers=auth_header(alice))

    sandbox = client.post(
        "/assessments",
        json={"provenance": RecordProvenance.SANDBOX.value},
        headers=auth_header(bob),
    ).json()["id"]
    client.put(
        f"/assessments/{sandbox}", json=_body(_scoreable_partial_doc()), headers=auth_header(bob)
    )
    client.post(f"/assessments/{sandbox}/submit-for-review", headers=auth_header(bob))

    refused = client.get("/founder-review/queue", headers=auth_header(alice))
    assert refused.status_code == 403

    queue = client.get("/founder-review/queue", headers=auth_header(founder))
    assert queue.status_code == 200
    ids = [entry["assessment_id"] for entry in queue.json()]
    assert production in ids
    assert sandbox not in ids  # self-approving, no client at the other end


def test_an_approved_record_leaves_the_queue_and_a_re_edit_puts_it_back(
    client, alice: SeededConsultant, founder: SeededConsultant
) -> None:
    aid = _new_production_assessment(client, alice)
    submit_and_approve(client, aid, alice, founder)

    queue = client.get("/founder-review/queue", headers=auth_header(founder)).json()
    assert aid not in [e["assessment_id"] for e in queue]

    client.put(f"/assessments/{aid}", json=_body(_edited_doc()), headers=auth_header(alice))

    queue = client.get("/founder-review/queue", headers=auth_header(founder)).json()
    entry = next(e for e in queue if e["assessment_id"] == aid)
    # The founder is re-reading, not reading. Saying so is the difference between "review this"
    # and "review what changed".
    assert entry["previously_approved"] is True


def test_an_approval_is_audited(
    client, alice: SeededConsultant, founder: SeededConsultant, admin: SeededConsultant
) -> None:
    from bcap_contracts.audit import AuditEventType

    aid = _new_production_assessment(client, alice)
    submit_and_approve(client, aid, alice, founder)

    events = client.get("/compliance/audit", headers=auth_header(admin))
    assert events.status_code == 200
    approvals = [
        e for e in events.json() if e["event_type"] == AuditEventType.FOUNDER_APPROVAL.value
    ]
    assert len(approvals) == 1
    assert approvals[0]["resource_id"] == aid


def test_another_advisors_assessment_is_invisible_not_forbidden(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    """Scope refusals stay 404 — the API never reveals a record the caller cannot see. That is a
    different answer from the 403 a role refusal gets, and the difference is deliberate."""
    aid = _new_production_assessment(client, alice)
    assert (
        client.post(f"/assessments/{aid}/submit-for-review", headers=auth_header(bob)).status_code
        == 404
    )
    assert (
        client.get(f"/assessments/{aid}/founder-approval", headers=auth_header(bob)).status_code
        == 404
    )
