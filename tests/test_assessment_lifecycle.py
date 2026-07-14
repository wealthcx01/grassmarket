"""Assessment lifecycle + API tests (GRS-0009).

Partial autosave round-trips without scoring; finalisation locks inputs and creates an immutable
scoring run; the live-score endpoint returns a band with honest `modelled` flags on a partial
document; cross-consultant access is refused on every endpoint; guidance returns todo anchors
labelled, not blank.
"""

from __future__ import annotations

from bcap_contracts.assessments import (
    AssessmentDocument,
    MetricEntry,
    PowerEntry,
    SubcomponentRating,
)
from bcap_contracts.common import EvidenceGrade, MaturityLevel, MetricConfidence, StrengthRating
from bcap_contracts.registry import load_registry

from tests.committee_helpers import approve_committee_queue
from tests.conftest import SeededConsultant, auth_header
from tests.dual_rating_helpers import reach_consensus

_E3 = EvidenceGrade.E3_ARTIFACT


def _scoreable_partial_doc() -> AssessmentDocument:
    """A genuinely PARTIAL document that is still scoreable: all 7 powers (graded), one metric
    (graded), one subcomponent rated in a core module — the other 50 subs / 9 metrics unrated."""
    registry = load_registry()
    powers = tuple(
        PowerEntry(
            power_key=p.key,
            benefit=StrengthRating.EMERGING,
            barrier=StrengthRating.EMERGING,
            benefit_grade=_E3,
            barrier_grade=_E3,
        )
        for p in registry.powers
    )
    metrics = (
        MetricEntry(metric_key="AUA", raw=1_000_000_000, confidence=MetricConfidence.AUDITED),
    )
    subs = (
        SubcomponentRating(
            module_key="APP_SERVER",
            subcomponent_key="APP_SERVER_SECURITY_COMPLIANCE",
            level=MaturityLevel.ADVANCED,
            evidence_grade=_E3,
        ),
    )
    return AssessmentDocument(
        subject="Meridian (partial)", subcomponents=subs, metrics=metrics, powers=powers
    )


def _body(doc: AssessmentDocument) -> dict:
    return doc.model_dump(mode="json")


# --- Autosave round-trips a partial document without scoring -----------------------------


def test_partial_autosave_round_trips_without_scoring(client, alice: SeededConsultant) -> None:
    created = client.post("/assessments", json={"subject": "New"}, headers=auth_header(alice))
    assert created.status_code == 201
    aid = created.json()["id"]
    assert created.json()["state"] == "draft"

    # A half-filled document (2 subcomponents, no metrics/powers) saves — no scoring required.
    doc = AssessmentDocument(
        subject="Half filled",
        subcomponents=(
            SubcomponentRating(
                module_key="FRONTEND",
                subcomponent_key="FRONTEND_PERFORMANCE",
                level=MaturityLevel.DEVELOPING,
                evidence_grade=_E3,
            ),
        ),
    )
    saved = client.put(f"/assessments/{aid}", json=_body(doc), headers=auth_header(alice))
    assert saved.status_code == 200
    assert saved.json()["state"] == "in_progress"

    fetched = client.get(f"/assessments/{aid}", headers=auth_header(alice))
    assert fetched.json()["document"]["subject"] == "Half filled"
    assert len(fetched.json()["document"]["subcomponents"]) == 1
    assert fetched.json()["scoring_run_id"] is None  # never scored on autosave


# --- Live score on a partial document, honest modelled flags ----------------------------


def test_live_score_returns_band_with_honest_modelled_flags(
    client, alice: SeededConsultant
) -> None:
    aid = client.post("/assessments", json={}, headers=auth_header(alice)).json()["id"]
    client.put(
        f"/assessments/{aid}", json=_body(_scoreable_partial_doc()), headers=auth_header(alice)
    )

    resp = client.get(f"/assessments/{aid}/live-score", headers=auth_header(alice))
    assert resp.status_code == 200
    body = resp.json()
    assert body["scoreable"] is True
    assert body["v"] is not None and body["v"]["p10"] <= body["v"]["p50"] <= body["v"]["p90"]
    # Graded metric + graded powers → B and P are MODELLED (real ranges), honestly flagged.
    assert body["b"]["modelled"] is True
    assert body["p"]["modelled"] is True
    assert body["coverage"] is not None and body["coverage"] < 1.0  # genuinely partial
    assert body["uncertainty_version"] == "v1-draft-pending-elicitation"


def test_live_score_on_empty_doc_is_not_scoreable_with_reasons(
    client, alice: SeededConsultant
) -> None:
    aid = client.post("/assessments", json={}, headers=auth_header(alice)).json()["id"]
    resp = client.get(f"/assessments/{aid}/live-score", headers=auth_header(alice))
    body = resp.json()
    assert body["scoreable"] is False
    assert body["blocking"]  # says what is still needed
    assert body["v"] is None  # no falsely-confident band on an empty doc


# --- Finalisation locks + creates an immutable scoring run ------------------------------


def test_finalisation_locks_and_creates_scoring_run(client, alice: SeededConsultant) -> None:
    aid = client.post("/assessments", json={}, headers=auth_header(alice)).json()["id"]
    client.put(
        f"/assessments/{aid}", json=_body(_scoreable_partial_doc()), headers=auth_header(alice)
    )
    # Dual-rating consensus (§9) AND committee sign-off of the high-stakes triad (§8) must clear
    # before finalisation is allowed.
    reach_consensus(
        client,
        aid,
        alice,
        "APP_SERVER",
        [("APP_SERVER_SECURITY_COMPLIANCE", MaturityLevel.ADVANCED)],
    )
    approve_committee_queue(client, aid, alice)

    final = client.post(f"/assessments/{aid}/finalise", headers=auth_header(alice))
    assert final.status_code == 200
    body = final.json()
    assert body["state"] == "finalised"
    assert body["scoring_run_id"] is not None
    assert body["engine_version"] and body["methodology_version"] and body["uncertainty_version"]

    # Locked: an edit after finalisation is refused (409).
    edit = client.put(
        f"/assessments/{aid}", json=_body(_scoreable_partial_doc()), headers=auth_header(alice)
    )
    assert edit.status_code == 409
    # Re-finalise is also refused.
    assert (
        client.post(f"/assessments/{aid}/finalise", headers=auth_header(alice)).status_code == 409
    )


def test_finalise_refuses_an_unscoreable_assessment(client, alice: SeededConsultant) -> None:
    aid = client.post("/assessments", json={}, headers=auth_header(alice)).json()["id"]  # empty
    resp = client.post(f"/assessments/{aid}/finalise", headers=auth_header(alice))
    assert resp.status_code == 409
    assert "not yet scoreable" in resp.json()["detail"]


# --- Absolute scoping on every endpoint -------------------------------------------------


def test_cross_consultant_access_is_refused_everywhere(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    aid = client.post("/assessments", json={"subject": "Alice"}, headers=auth_header(alice)).json()[
        "id"
    ]
    client.put(
        f"/assessments/{aid}", json=_body(_scoreable_partial_doc()), headers=auth_header(alice)
    )

    # Bob cannot GET, PUT, live-score, or finalise Alice's assessment — 404, never revealing it.
    assert client.get(f"/assessments/{aid}", headers=auth_header(bob)).status_code == 404
    assert (
        client.put(
            f"/assessments/{aid}", json=_body(_scoreable_partial_doc()), headers=auth_header(bob)
        ).status_code
        == 404
    )
    assert client.get(f"/assessments/{aid}/live-score", headers=auth_header(bob)).status_code == 404
    assert client.post(f"/assessments/{aid}/finalise", headers=auth_header(bob)).status_code == 404
    # Bob's list does not include Alice's assessment.
    assert client.get("/assessments", headers=auth_header(bob)).json() == []


def test_endpoints_require_authentication(client) -> None:
    assert client.get("/assessments").status_code == 401
    assert client.post("/assessments", json={}).status_code == 401


# --- Guidance returns todo anchors labelled, not blank ----------------------------------


def test_guidance_returns_authored_anchors(client, alice: SeededConsultant) -> None:
    resp = client.get("/guidance/subcomponents/OEMS_EXEC_ALGOS", headers=auth_header(alice))
    assert resp.status_code == 200
    anchors = resp.json()
    assert len(anchors) == 4
    assert all(a["status"] == "authored" for a in anchors)
    assert all(a["statement"] for a in anchors)


def test_guidance_returns_todo_anchors_labelled_not_blank(client, alice: SeededConsultant) -> None:
    resp = client.get("/guidance/subcomponents/FRONTEND_PERFORMANCE", headers=auth_header(alice))
    assert resp.status_code == 200
    anchors = resp.json()
    assert len(anchors) == 4
    # Unauthored guidance is returned as explicit `todo` (the client shows "not yet authored"),
    # NOT silently omitted or a blank authored anchor.
    assert all(a["status"] == "todo" for a in anchors)
    assert all(a["statement"] == "" for a in anchors)


def test_guidance_unknown_subcomponent_is_404(client, alice: SeededConsultant) -> None:
    assert client.get("/guidance/subcomponents/NOPE", headers=auth_header(alice)).status_code == 404


# --- Scenario evaluation (ΔV → Upgrade Priority Index) -----------------------------------


def _doc_with_extra_sub(module: str, key: str, level: MaturityLevel) -> AssessmentDocument:
    base = _scoreable_partial_doc()
    extra = SubcomponentRating(
        module_key=module, subcomponent_key=key, level=level, evidence_grade=_E3
    )
    return base.model_copy(update={"subcomponents": (*base.subcomponents, extra)})


def test_scenarios_rank_by_delta_v(client, alice: SeededConsultant) -> None:
    aid = client.post("/assessments", json={}, headers=auth_header(alice)).json()["id"]
    client.put(
        f"/assessments/{aid}", json=_body(_scoreable_partial_doc()), headers=auth_header(alice)
    )
    # A bottleneck fix in a core module (OEMS) vs a top-up elsewhere (FRONTEND, non-core).
    big = _doc_with_extra_sub("OEMS", "OEMS_EXEC_ALGOS", MaturityLevel.ADVANCED)
    small = _doc_with_extra_sub("FRONTEND", "FRONTEND_PERFORMANCE", MaturityLevel.DEVELOPING)
    resp = client.post(
        f"/assessments/{aid}/scenarios",
        json={
            "scenarios": [
                {"name": "Top-up frontend", "document": _body(small)},
                {"name": "Fix OEMS bottleneck", "document": _body(big)},
            ]
        },
        headers=auth_header(alice),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["scoreable"] is True
    assert body["baseline_v"] is not None
    ranked = body["priority_index"]
    assert [r["rank"] for r in ranked] == [1, 2]
    assert (
        ranked[0]["delta_v"] >= ranked[1]["delta_v"]
    )  # bigger ΔV first, regardless of input order


def test_scenario_missing_powers_reports_blocking_not_500(client, alice: SeededConsultant) -> None:
    """GRS-0045: a schema-valid but structurally-incomplete scenario (here, no powers) must be
    reported as unscoreable, never crash the endpoint with a KeyError → 500."""
    aid = client.post("/assessments", json={}, headers=auth_header(alice)).json()["id"]
    client.put(
        f"/assessments/{aid}", json=_body(_scoreable_partial_doc()), headers=auth_header(alice)
    )
    incomplete = _scoreable_partial_doc().model_copy(update={"powers": ()})
    resp = client.post(
        f"/assessments/{aid}/scenarios",
        json={"scenarios": [{"name": "Broken", "document": _body(incomplete)}]},
        headers=auth_header(alice),
    )
    assert resp.status_code == 200
    assert resp.json()["scoreable"] is False
    assert any("Broken" in b for b in resp.json()["blocking"])


def test_scenarios_on_unscoreable_baseline_reports_blocking(
    client, alice: SeededConsultant
) -> None:
    aid = client.post("/assessments", json={}, headers=auth_header(alice)).json()["id"]  # empty
    resp = client.post(
        f"/assessments/{aid}/scenarios", json={"scenarios": []}, headers=auth_header(alice)
    )
    assert resp.status_code == 200
    assert resp.json()["scoreable"] is False
    assert resp.json()["blocking"]


def test_scenarios_scoped_to_owner(client, alice: SeededConsultant, bob: SeededConsultant) -> None:
    aid = client.post("/assessments", json={}, headers=auth_header(alice)).json()["id"]
    resp = client.post(
        f"/assessments/{aid}/scenarios", json={"scenarios": []}, headers=auth_header(bob)
    )
    assert resp.status_code == 404


# --- Registry endpoint (wizard form structure) ------------------------------------------


def test_registry_endpoint_returns_structure(client, alice: SeededConsultant) -> None:
    resp = client.get("/registry", headers=auth_header(alice))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["modules"]) == 9
    assert sum(len(m["subcomponents"]) for m in body["modules"]) == 51
    assert len(body["metrics"]) == 10
    assert len(body["powers"]) == 7


def test_registry_requires_authentication(client) -> None:
    assert client.get("/registry").status_code == 401
