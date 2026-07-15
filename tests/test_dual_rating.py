"""Dual-rating + consensus governance tests (GRS-0020, Methodology §9, ADR-0010).

Pins the four things the ticket promises: a solo-rated assessment cannot finalise; a rater is BLIND
to a co-rater's draft until both submit; a resolved dissent is written into the immutable scoring
run and is retrievable for the methods appendix; and scoping widens to assigned raters without
letting a rater edit the document, finalise, assign, or resolve — those stay the lead's.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from bcap_contracts.common import EvidenceGrade, MaturityLevel

from grassmarket.atlas import AssessmentInputs
from tests.committee_helpers import approve_committee_queue
from tests.conftest import SeededConsultant, auth_header
from tests.dual_rating_helpers import (
    assign_rater,
    reach_consensus,
    seed_corater,
    submit_ratings,
)
from tests.test_assessment_lifecycle import _body, _scoreable_partial_doc

_MODULE = "APP_SERVER"
_SUB = "APP_SERVER_SECURITY_COMPLIANCE"
_SUB2 = "APP_SERVER_API_DESIGN"
_E3 = EvidenceGrade.E3_ARTIFACT


def _rating_of(subcomponent_key: str, level: MaturityLevel) -> dict:
    return {
        "module_key": _MODULE,
        "subcomponent_key": subcomponent_key,
        "level": level.value,
        "evidence_grade": _E3.value,
    }


def _new_assessment(client, owner: SeededConsultant) -> str:
    aid = client.post("/assessments", json={}, headers=auth_header(owner)).json()["id"]
    client.put(
        f"/assessments/{aid}", json=_body(_scoreable_partial_doc()), headers=auth_header(owner)
    )
    return aid


def _rating(level: MaturityLevel, *, dissent_note: str | None = None) -> dict:
    body = {
        "module_key": _MODULE,
        "subcomponent_key": _SUB,
        "level": level.value,
        "evidence_grade": _E3.value,
    }
    if dissent_note is not None:
        body["dissent_note"] = dissent_note
    return body


# --- GRS-0062: co-rater discovery + colleague lookup (the dual-rating UI's plumbing) -----


def test_consultant_lookup_by_email(client, alice: SeededConsultant) -> None:
    """A colleague resolves by EXACT email to the minimum needed to assign them as a rater — never
    the password hash. An unknown email is a 404."""
    ok = client.get(f"/consultants/by-email?email={alice.stored.email}", headers=auth_header(alice))
    assert ok.status_code == 200
    assert ok.json()["id"] == str(alice.stored.id)
    assert ok.json()["full_name"] == alice.stored.full_name
    assert "hashed_password" not in ok.json()
    assert (
        client.get(
            "/consultants/by-email?email=nobody@bruntsfieldcapital.com", headers=auth_header(alice)
        ).status_code
        == 404
    )


def test_rating_requests_lists_modules_assigned_to_me(client, alice: SeededConsultant) -> None:
    """GRS-0062: a co-rater finds the ratings requested of them via GET /assessments/rating-requests
    — every module they've been assigned to rate on an in-progress assessment."""
    aid = _new_assessment(client, alice)
    co = seed_corater(client)
    assign_rater(client, aid, alice, _MODULE, co.principal.consultant_id)

    reqs = client.get("/assessments/rating-requests", headers=auth_header(co))
    assert reqs.status_code == 200
    row = next(
        (r for r in reqs.json() if r["assessment_id"] == aid and r["module_key"] == _MODULE), None
    )
    assert row is not None and row["submitted"] is False and row["module_name"]

    # The lead who never asked to rate has no request for this (they only assigned the co-rater).
    assert all(
        r["assessment_id"] != aid
        for r in client.get("/assessments/rating-requests", headers=auth_header(alice)).json()
    )


# --- A solo-rated assessment cannot finalise --------------------------------------------


def test_solo_rated_assessment_cannot_finalise(client, alice: SeededConsultant) -> None:
    """The partial doc has one assessed subcomponent and no second opinion — finalisation is refused
    with a plain governance reason, not a scoreability one (Methodology §9)."""
    aid = _new_assessment(client, alice)
    resp = client.post(f"/assessments/{aid}/finalise", headers=auth_header(alice))
    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert "dual-rating consensus incomplete" in detail
    assert "solo-rated" in detail


def test_consensus_needs_at_least_two_raters(client, alice: SeededConsultant) -> None:
    aid = _new_assessment(client, alice)
    assign_rater(client, aid, alice, _MODULE, alice.principal.consultant_id)
    submit_ratings(client, aid, alice, _MODULE, [(_SUB, MaturityLevel.ADVANCED)])
    resp = client.post(
        f"/assessments/{aid}/modules/{_MODULE}/consensus",
        json={"resolved": [_rating(MaturityLevel.ADVANCED)]},
        headers=auth_header(alice),
    )
    assert resp.status_code == 409
    assert "requires ≥2" in resp.json()["detail"]


def test_agreed_consensus_lets_the_assessment_finalise(client, alice: SeededConsultant) -> None:
    aid = _new_assessment(client, alice)
    reach_consensus(client, aid, alice, _MODULE, [(_SUB, MaturityLevel.ADVANCED)])
    approve_committee_queue(client, aid, alice)  # the high-stakes triad also needs sign-off (§8)
    final = client.post(f"/assessments/{aid}/finalise", headers=auth_header(alice))
    assert final.status_code == 200
    assert final.json()["state"] == "finalised"


# --- Blind until both submit ------------------------------------------------------------


def test_co_rater_is_blind_until_both_submit(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    aid = _new_assessment(client, alice)
    assign_rater(client, aid, alice, _MODULE, alice.principal.consultant_id)
    assign_rater(client, aid, alice, _MODULE, bob.principal.consultant_id)

    # Alice submits; Bob has not. Bob lists the module's ratings → he sees ONLY his own draft.
    submit_ratings(client, aid, alice, _MODULE, [(_SUB, MaturityLevel.ADVANCED)])
    bob_view = client.get(
        f"/assessments/{aid}/modules/{_MODULE}/ratings", headers=auth_header(bob)
    ).json()
    assert len(bob_view) == 1
    assert bob_view[0]["owner_consultant_id"] == str(bob.principal.consultant_id)
    assert (
        bob_view[0]["ratings"] == []
    )  # Alice's ADVANCED is not leaked into Bob's independent call
    # Alice, symmetrically, sees only her own until Bob submits.
    alice_view = client.get(
        f"/assessments/{aid}/modules/{_MODULE}/ratings", headers=auth_header(alice)
    ).json()
    assert [d["owner_consultant_id"] for d in alice_view] == [str(alice.principal.consultant_id)]

    # Bob submits → the blind opens; both now see both drafts.
    submit_ratings(client, aid, bob, _MODULE, [(_SUB, MaturityLevel.DEVELOPING)])
    opened = client.get(
        f"/assessments/{aid}/modules/{_MODULE}/ratings", headers=auth_header(bob)
    ).json()
    assert len(opened) == 2
    owners = {d["owner_consultant_id"] for d in opened}
    assert owners == {str(alice.principal.consultant_id), str(bob.principal.consultant_id)}


def test_a_submitted_draft_is_locked(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    aid = _new_assessment(client, alice)
    assign_rater(client, aid, alice, _MODULE, bob.principal.consultant_id)
    submit_ratings(client, aid, bob, _MODULE, [(_SUB, MaturityLevel.ADVANCED)])
    edit = client.put(
        f"/assessments/{aid}/modules/{_MODULE}/my-rating",
        json={"ratings": [_rating(MaturityLevel.FRONTIER)]},
        headers=auth_header(bob),
    )
    assert edit.status_code == 409
    assert "submitted" in edit.json()["detail"]


def test_an_empty_rating_cannot_be_submitted(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    aid = _new_assessment(client, alice)
    assign_rater(client, aid, alice, _MODULE, bob.principal.consultant_id)
    resp = client.post(
        f"/assessments/{aid}/modules/{_MODULE}/my-rating/submit", headers=auth_header(bob)
    )
    assert resp.status_code == 409
    assert "empty" in resp.json()["detail"]


# --- Dissent: required on disagreement, and persisted into the scoring run ----------------


def test_disagreement_requires_a_dissent_note(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    aid = _new_assessment(client, alice)
    assign_rater(client, aid, alice, _MODULE, alice.principal.consultant_id)
    assign_rater(client, aid, alice, _MODULE, bob.principal.consultant_id)
    submit_ratings(client, aid, alice, _MODULE, [(_SUB, MaturityLevel.ADVANCED)])
    submit_ratings(client, aid, bob, _MODULE, [(_SUB, MaturityLevel.DEVELOPING)])

    # The raters differed — resolving without a dissent note is refused.
    no_note = client.post(
        f"/assessments/{aid}/modules/{_MODULE}/consensus",
        json={"resolved": [_rating(MaturityLevel.ADVANCED)]},
        headers=auth_header(alice),
    )
    assert no_note.status_code == 409
    assert "dissent note is required" in no_note.json()["detail"]

    # With a note, consensus resolves as a documented dissent (consensus=False).
    note = "Alice weighted the pen-test evidence; Bob's DEVELOPING yielded. Lead call: ADVANCED."
    ok = client.post(
        f"/assessments/{aid}/modules/{_MODULE}/consensus",
        json={"resolved": [_rating(MaturityLevel.ADVANCED, dissent_note=note)]},
        headers=auth_header(alice),
    )
    assert ok.status_code == 200
    resolved_sub = next(
        s for s in ok.json()["document"]["subcomponents"] if s["subcomponent_key"] == _SUB
    )
    assert resolved_sub["consensus"] is False
    assert resolved_sub["dissent_note"] == note
    assert len(resolved_sub["rater_ids"]) == 2


def test_dissent_is_sealed_into_the_scoring_run_and_retrievable(
    client, repo, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    """A resolved dissent must survive into the immutable run's inputs (its content-hash seal) so it
    is retrievable for the methods appendix — Methodology §9 audit evidence."""
    aid = _new_assessment(client, alice)
    assign_rater(client, aid, alice, _MODULE, alice.principal.consultant_id)
    assign_rater(client, aid, alice, _MODULE, bob.principal.consultant_id)
    submit_ratings(client, aid, alice, _MODULE, [(_SUB, MaturityLevel.ADVANCED)])
    submit_ratings(client, aid, bob, _MODULE, [(_SUB, MaturityLevel.DEVELOPING)])
    note = "Documented dissent: Bob deferred to Alice on compliance maturity."
    client.post(
        f"/assessments/{aid}/modules/{_MODULE}/consensus",
        json={"resolved": [_rating(MaturityLevel.ADVANCED, dissent_note=note)]},
        headers=auth_header(alice),
    )
    approve_committee_queue(client, aid, alice)
    final = client.post(f"/assessments/{aid}/finalise", headers=auth_header(alice))
    assert final.status_code == 200
    run_id = final.json()["scoring_run_id"]

    record = repo.get_scoring_run_record(alice.principal, UUID(run_id))
    assert note in record.inputs_json  # dissent is in the sealed inputs
    inputs = AssessmentInputs.model_validate_json(record.inputs_json)
    sub = next(s for s in inputs.subcomponents if s.subcomponent_key == _SUB)
    assert sub.dissent_note == note
    assert sub.consensus is False
    assert len(set(sub.rater_ids)) == 2


# --- Scoping (ADR-0010): raters reach the rating surface, nothing more -------------------


def test_a_non_assigned_consultant_cannot_reach_the_rating_workflow(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    aid = _new_assessment(client, alice)  # Bob is not assigned to anything on it
    h = auth_header(bob)
    assert (
        client.get(f"/assessments/{aid}/modules/{_MODULE}/my-rating", headers=h).status_code == 404
    )
    assert client.get(f"/assessments/{aid}/modules/{_MODULE}/ratings", headers=h).status_code == 404
    assert (
        client.put(
            f"/assessments/{aid}/modules/{_MODULE}/my-rating",
            json={"ratings": [_rating(MaturityLevel.ADVANCED)]},
            headers=h,
        ).status_code
        == 404
    )
    # And Bob cannot assign raters or resolve consensus — those are the lead's authority.
    assert (
        client.post(
            f"/assessments/{aid}/modules/{_MODULE}/raters",
            json={"rater_consultant_id": str(bob.principal.consultant_id)},
            headers=h,
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/assessments/{aid}/modules/{_MODULE}/consensus",
            json={"resolved": [_rating(MaturityLevel.ADVANCED)]},
            headers=h,
        ).status_code
        == 404
    )


def test_an_assigned_rater_still_cannot_edit_the_document_or_finalise(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    """Scoping widens for the rating surface only. An assigned rater can rate, but the document, its
    finalisation, and rater assignment stay the lead's (ADR-0010)."""
    aid = _new_assessment(client, alice)
    assign_rater(client, aid, alice, _MODULE, bob.principal.consultant_id)
    # Bob can touch his own draft...
    assert (
        client.get(
            f"/assessments/{aid}/modules/{_MODULE}/my-rating", headers=auth_header(bob)
        ).status_code
        == 200
    )
    # ...but not the document, live-score, finalise, or assigning another rater.
    assert (
        client.put(
            f"/assessments/{aid}", json=_body(_scoreable_partial_doc()), headers=auth_header(bob)
        ).status_code
        == 404
    )
    assert client.get(f"/assessments/{aid}", headers=auth_header(bob)).status_code == 404
    assert client.post(f"/assessments/{aid}/finalise", headers=auth_header(bob)).status_code == 404
    assert (
        client.post(
            f"/assessments/{aid}/modules/{_MODULE}/raters",
            json={"rater_consultant_id": str(alice.principal.consultant_id)},
            headers=auth_header(bob),
        ).status_code
        == 404
    )


def test_unknown_module_is_rejected(client, alice: SeededConsultant) -> None:
    aid = _new_assessment(client, alice)
    co = seed_corater(client)
    resp = client.post(
        f"/assessments/{aid}/modules/NOT_A_MODULE/raters",
        json={"rater_consultant_id": str(co.principal.consultant_id)},
        headers=auth_header(alice),
    )
    assert resp.status_code == 404
    assert "Unknown module" in resp.json()["detail"]


def test_stray_subcomponent_in_a_rating_is_422(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    aid = _new_assessment(client, alice)
    assign_rater(client, aid, alice, _MODULE, bob.principal.consultant_id)
    resp = client.put(
        f"/assessments/{aid}/modules/{_MODULE}/my-rating",
        json={
            "ratings": [
                {
                    "module_key": _MODULE,
                    "subcomponent_key": "FRONTEND_PERFORMANCE",  # not in APP_SERVER
                    "level": MaturityLevel.ADVANCED.value,
                    "evidence_grade": _E3.value,
                }
            ]
        },
        headers=auth_header(bob),
    )
    assert resp.status_code == 422
    assert "not part of module" in resp.json()["detail"]


# --- The finalise gate cannot be forged via a raw document PUT (ADR-0010) ----------------


def test_forged_governance_fields_in_a_put_cannot_finalise(client, alice: SeededConsultant) -> None:
    """The primary §9 guarantee: a lead cannot fake dual rating. Governance fields carried on an
    autosaved document are stripped, so a PUT with hand-crafted rater_ids/consensus still finalises
    as solo-rated. Without the strip, the finalise gate (which reads these fields) would be
    bypassable and §9 advisory."""
    aid = client.post("/assessments", json={}, headers=auth_header(alice)).json()["id"]
    doc = _scoreable_partial_doc()
    forged_sub = doc.subcomponents[0].model_copy(
        update={"rater_ids": (uuid4(), uuid4()), "consensus": True}
    )
    forged = doc.model_copy(update={"subcomponents": (forged_sub,)})
    client.put(f"/assessments/{aid}", json=_body(forged), headers=auth_header(alice))

    # The stored document has the governance fields reset — no real drafts, no consensus.
    stored = client.get(f"/assessments/{aid}", headers=auth_header(alice)).json()
    sub = stored["document"]["subcomponents"][0]
    assert sub["rater_ids"] == []
    assert sub["consensus"] is False

    resp = client.post(f"/assessments/{aid}/finalise", headers=auth_header(alice))
    assert resp.status_code == 409
    assert "solo-rated" in resp.json()["detail"]


# --- More consensus edge cases -----------------------------------------------------------


def test_a_subcomponent_only_one_rater_assessed_cannot_reach_consensus(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    """Distinct from the ≥2-raters-per-module check: a subcomponent only ONE rater assessed cannot
    be resolved, even when both raters submitted the module (exercises a multi-sub module)."""
    aid = _new_assessment(client, alice)
    assign_rater(client, aid, alice, _MODULE, alice.principal.consultant_id)
    assign_rater(client, aid, alice, _MODULE, bob.principal.consultant_id)
    # Alice rates two subs; Bob rates only the first — so _SUB2 has a single opinion.
    submit_ratings(
        client,
        aid,
        alice,
        _MODULE,
        [(_SUB, MaturityLevel.ADVANCED), (_SUB2, MaturityLevel.DEVELOPING)],
    )
    submit_ratings(client, aid, bob, _MODULE, [(_SUB, MaturityLevel.ADVANCED)])

    resp = client.post(
        f"/assessments/{aid}/modules/{_MODULE}/consensus",
        json={
            "resolved": [
                _rating_of(_SUB, MaturityLevel.ADVANCED),
                _rating_of(_SUB2, MaturityLevel.DEVELOPING),
            ]
        },
        headers=auth_header(alice),
    )
    assert resp.status_code == 409
    assert "two independent assessments" in resp.json()["detail"]


def test_consensus_refused_before_all_assigned_raters_submit(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    aid = _new_assessment(client, alice)
    assign_rater(client, aid, alice, _MODULE, alice.principal.consultant_id)
    assign_rater(client, aid, alice, _MODULE, bob.principal.consultant_id)
    submit_ratings(client, aid, alice, _MODULE, [(_SUB, MaturityLevel.ADVANCED)])  # Bob has not
    resp = client.post(
        f"/assessments/{aid}/modules/{_MODULE}/consensus",
        json={"resolved": [_rating(MaturityLevel.ADVANCED)]},
        headers=auth_header(alice),
    )
    assert resp.status_code == 409
    assert "must submit before consensus" in resp.json()["detail"]


def test_duplicate_and_unknown_rater_assignment_refused(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    aid = _new_assessment(client, alice)
    assign_rater(client, aid, alice, _MODULE, bob.principal.consultant_id)
    dup = client.post(
        f"/assessments/{aid}/modules/{_MODULE}/raters",
        json={"rater_consultant_id": str(bob.principal.consultant_id)},
        headers=auth_header(alice),
    )
    assert dup.status_code == 409
    assert "already assigned" in dup.json()["detail"]

    unknown = client.post(
        f"/assessments/{aid}/modules/{_MODULE}/raters",
        json={"rater_consultant_id": str(uuid4())},
        headers=auth_header(alice),
    )
    assert unknown.status_code == 404


def test_finalisation_locks_the_whole_rating_workflow(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    """Once finalised, the assessment's inputs are locked (#6): no new assignment, no draft edit by
    an assigned rater, no re-resolution."""
    aid = _new_assessment(client, alice)
    co = reach_consensus(client, aid, alice, _MODULE, [(_SUB, MaturityLevel.ADVANCED)])
    approve_committee_queue(client, aid, alice)
    assert (
        client.post(f"/assessments/{aid}/finalise", headers=auth_header(alice)).status_code == 200
    )

    assign = client.post(
        f"/assessments/{aid}/modules/{_MODULE}/raters",
        json={"rater_consultant_id": str(bob.principal.consultant_id)},
        headers=auth_header(alice),
    )
    assert assign.status_code == 409
    edit = client.put(
        f"/assessments/{aid}/modules/{_MODULE}/my-rating",
        json={"ratings": [_rating(MaturityLevel.FRONTIER)]},
        headers=auth_header(co),
    )
    assert edit.status_code == 409
    assert "finalised" in edit.json()["detail"]
    reresolve = client.post(
        f"/assessments/{aid}/modules/{_MODULE}/consensus",
        json={"resolved": [_rating(MaturityLevel.ADVANCED)]},
        headers=auth_header(alice),
    )
    assert reresolve.status_code == 409


def test_admin_cannot_peek_at_drafts_before_all_submit(
    client, alice: SeededConsultant, bob: SeededConsultant, admin: SeededConsultant
) -> None:
    """The blind holds even for an admin — peeking would defeat the method, not merely leak data
    (ADR-0010). Admin reaches the endpoint but sees no draft until every rater has submitted."""
    aid = _new_assessment(client, alice)
    assign_rater(client, aid, alice, _MODULE, alice.principal.consultant_id)
    assign_rater(client, aid, alice, _MODULE, bob.principal.consultant_id)
    submit_ratings(client, aid, alice, _MODULE, [(_SUB, MaturityLevel.ADVANCED)])  # Bob has not
    admin_view = client.get(
        f"/assessments/{aid}/modules/{_MODULE}/ratings", headers=auth_header(admin)
    ).json()
    assert admin_view == []  # admin owns none of these drafts, and not all have submitted
