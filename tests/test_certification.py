"""Certification-ladder tests (GRS-0023, Methodology §9).

Pins the exit criteria: an uncertified advisor cannot finalise a Frontier-bearing assessment (the
enforcement); state transitions require their evidence (you cannot reach Observed Lead with one
shadow); an admin override leaves an audit record. Plus the ladder climb, scoping, sign-off rules.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from bcap_contracts.assessments import (
    AssessmentDocument,
    MetricEntry,
    PowerEntry,
    SubcomponentRating,
)
from bcap_contracts.common import (
    AssessorLevel,
    EvidenceGrade,
    MaturityLevel,
    MetricConfidence,
    StrengthRating,
)
from bcap_contracts.registry import load_registry

from grassmarket.assessments.service import compute_score
from grassmarket.atlas.draft_coefficients import draft_v1_coefficient_set
from grassmarket.atlas.montecarlo import draft_v1_uncertainty_model
from grassmarket.workbench.certification import requires_certified_lead
from tests.certification_helpers import (
    frontier_assessment_ready_to_finalise,
    seed_consultant_at_level,
)
from tests.conftest import SeededConsultant, auth_header

_REGISTRY = load_registry()
_E3 = EvidenceGrade.E3_ARTIFACT
_METRICS = (MetricEntry(metric_key="AUA", raw=1_000_000_000, confidence=MetricConfidence.AUDITED),)


def _powers(strength: StrengthRating) -> tuple:
    return tuple(
        PowerEntry(
            power_key=p.key,
            benefit=strength,
            barrier=strength,
            benefit_grade=_E3,
            barrier_grade=_E3,
        )
        for p in _REGISTRY.powers
    )


def _result_of(document: AssessmentDocument):
    return compute_score(
        document,
        draft_v1_coefficient_set(_REGISTRY),
        _REGISTRY,
        draft_v1_uncertainty_model(),
        random.Random(1),
    ).result


# --- Unit: which ratings require a Certified Lead (both branches of the exit criterion) ---


def test_requires_certified_lead_flags_wide_powers_and_frontier_modules() -> None:
    one_sub = (
        SubcomponentRating(
            module_key="APP_SERVER",
            subcomponent_key="APP_SERVER_SECURITY_COMPLIANCE",
            level=MaturityLevel.ADVANCED,
            evidence_grade=_E3,
        ),
    )
    # A Wide power triggers the floor.
    wide = AssessmentDocument(
        subject="wide", subcomponents=one_sub, metrics=_METRICS, powers=_powers(StrengthRating.WIDE)
    )
    wide_reasons = requires_certified_lead(_result_of(wide))
    assert wide_reasons and all("Wide" in r for r in wide_reasons)

    # A Frontier module triggers the floor.
    module = _REGISTRY.require_module("APP_SERVER")
    frontier_subs = tuple(
        SubcomponentRating(
            module_key="APP_SERVER",
            subcomponent_key=s.key,
            level=MaturityLevel.FRONTIER,
            evidence_grade=_E3,
        )
        for s in module.subcomponents
    )
    frontier = AssessmentDocument(
        subject="frontier",
        subcomponents=frontier_subs,
        metrics=_METRICS,
        powers=_powers(StrengthRating.EMERGING),
    )
    frontier_reasons = requires_certified_lead(_result_of(frontier))
    assert any("Frontier" in r for r in frontier_reasons)

    # Neither present → no certification floor (the standard non-high-stakes assessment).
    ordinary = AssessmentDocument(
        subject="ordinary",
        subcomponents=one_sub,
        metrics=_METRICS,
        powers=_powers(StrengthRating.EMERGING),
    )
    assert requires_certified_lead(_result_of(ordinary)) == []


def test_certified_lead_floor_is_a_subset_of_the_committee_trigger() -> None:
    # GRS-0131 reconciliation: the two high-stakes gates are nested, never in conflict. Anything
    # that needs a Certified Lead (module Frontier / power Wide) also triggers committee review;
    # committee additionally catches lesser-stakes ratings (Established powers, non-None triads)
    # that the lead-floor lets pass. Pin: CL-floor non-empty ⟹ committee non-empty, on both.
    from grassmarket.atlas.committee import required_committee_items

    one_sub = (
        SubcomponentRating(
            module_key="APP_SERVER",
            subcomponent_key="APP_SERVER_SECURITY_COMPLIANCE",
            level=MaturityLevel.ADVANCED,
            evidence_grade=_E3,
        ),
    )
    wide_result = _result_of(
        AssessmentDocument(
            subject="wide",
            subcomponents=one_sub,
            metrics=_METRICS,
            powers=_powers(StrengthRating.WIDE),
        )
    )
    # A Wide power hits the CL floor AND committee (Wide ≥ Established).
    assert requires_certified_lead(wide_result)
    assert required_committee_items(wide_result)

    module = _REGISTRY.require_module("APP_SERVER")
    frontier_result = _result_of(
        AssessmentDocument(
            subject="frontier",
            subcomponents=tuple(
                SubcomponentRating(
                    module_key="APP_SERVER",
                    subcomponent_key=s.key,
                    level=MaturityLevel.FRONTIER,
                    evidence_grade=_E3,
                )
                for s in module.subcomponents
            ),
            metrics=_METRICS,
            powers=_powers(StrengthRating.EMERGING),
        )
    )
    # A Frontier module hits the CL floor AND committee (both have a Frontier-module branch).
    assert any("Frontier" in r for r in requires_certified_lead(frontier_result))
    assert required_committee_items(frontier_result)


def _cert(client, admin, advisor_id: str) -> dict:
    return client.get(f"/certification/{advisor_id}", headers=auth_header(admin)).json()


def _bring_to_shadow_evidence(client, admin: SeededConsultant, advisor_id: str) -> None:
    client.post(f"/certification/{advisor_id}/coursework", headers=auth_header(admin))
    client.post(
        f"/certification/{advisor_id}/exam", json={"score": 0.85}, headers=auth_header(admin)
    )
    client.post(f"/certification/{advisor_id}/shadow", headers=auth_header(admin))
    client.post(f"/certification/{advisor_id}/shadow", headers=auth_header(admin))


# --- The ladder climbs only on evidence -------------------------------------------------


def test_full_ladder_climb_trained_to_certified_lead(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    aid = str(alice.principal.consultant_id)
    signer = seed_consultant_at_level(client, AssessorLevel.CERTIFIED_LEAD)

    _bring_to_shadow_evidence(client, admin, aid)
    assert (
        client.post(f"/certification/{aid}/promote", headers=auth_header(admin)).status_code == 200
    )
    assert _cert(client, admin, aid)["level"] == "shadow"

    client.post(f"/certification/{aid}/observed-lead", headers=auth_header(admin))
    assert (
        client.post(f"/certification/{aid}/promote", headers=auth_header(admin)).status_code == 200
    )
    assert _cert(client, admin, aid)["level"] == "observed_lead"

    client.post(
        f"/certification/{aid}/signoff",
        json={"signer_consultant_id": str(signer.principal.consultant_id)},
        headers=auth_header(admin),
    )
    assert (
        client.post(f"/certification/{aid}/promote", headers=auth_header(admin)).status_code == 200
    )
    assert _cert(client, admin, aid)["level"] == "certified_lead"


def test_cannot_reach_shadow_with_one_shadow_assessment(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    aid = str(alice.principal.consultant_id)
    client.post(f"/certification/{aid}/coursework", headers=auth_header(admin))
    client.post(f"/certification/{aid}/exam", json={"score": 0.85}, headers=auth_header(admin))
    client.post(f"/certification/{aid}/shadow", headers=auth_header(admin))  # only ONE
    resp = client.post(f"/certification/{aid}/promote", headers=auth_header(admin))
    assert resp.status_code == 409
    assert "1/2 shadow assessments" in resp.json()["detail"]


def test_cannot_promote_without_coursework_or_exam(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    aid = str(alice.principal.consultant_id)
    client.post(f"/certification/{aid}/shadow", headers=auth_header(admin))
    client.post(f"/certification/{aid}/shadow", headers=auth_header(admin))
    resp = client.post(f"/certification/{aid}/promote", headers=auth_header(admin))
    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert "Coursework is not complete" in detail
    assert "exam has not been passed" in detail


def test_a_failed_exam_does_not_count(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    aid = str(alice.principal.consultant_id)
    client.post(f"/certification/{aid}/coursework", headers=auth_header(admin))
    client.post(
        f"/certification/{aid}/exam", json={"score": 0.5}, headers=auth_header(admin)
    )  # <0.7
    client.post(f"/certification/{aid}/shadow", headers=auth_header(admin))
    client.post(f"/certification/{aid}/shadow", headers=auth_header(admin))
    resp = client.post(f"/certification/{aid}/promote", headers=auth_header(admin))
    assert resp.status_code == 409
    assert "exam has not been passed" in resp.json()["detail"]


def test_signoff_must_come_from_a_certified_lead(
    client, admin: SeededConsultant, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    aid = str(alice.principal.consultant_id)
    # Bob is a plain (Trained) consultant — not a Certified Lead.
    resp = client.post(
        f"/certification/{aid}/signoff",
        json={"signer_consultant_id": str(bob.principal.consultant_id)},
        headers=auth_header(admin),
    )
    assert resp.status_code == 409
    assert "Certified Lead" in resp.json()["detail"]


# --- Finalisation enforcement (the exit criterion) --------------------------------------


def test_uncertified_lead_cannot_finalise_a_frontier_assessment(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    aid = frontier_assessment_ready_to_finalise(client, alice)  # alice is Trained
    resp = client.post(f"/assessments/{aid}/finalise", headers=auth_header(alice))
    assert resp.status_code == 409
    assert "Certified Lead must lead" in resp.json()["detail"]
    assert "Frontier" in resp.json()["detail"]


def test_a_certified_lead_can_finalise_a_frontier_assessment(
    client, admin: SeededConsultant
) -> None:
    lead = seed_consultant_at_level(client, AssessorLevel.CERTIFIED_LEAD)
    aid = frontier_assessment_ready_to_finalise(client, lead)
    resp = client.post(f"/assessments/{aid}/finalise", headers=auth_header(lead))
    assert resp.status_code == 200
    assert resp.json()["state"] == "finalised"


# --- Admin override leaves an audit record ----------------------------------------------


def test_admin_can_override_the_certification_gate_with_a_recorded_reason(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    aid = frontier_assessment_ready_to_finalise(client, alice)
    # No reason → refused even for an admin (no silent bypass).
    assert (
        client.post(f"/assessments/{aid}/finalise", headers=auth_header(admin)).status_code == 409
    )

    # A blank/whitespace reason is NOT a valid override — it falls through to the refusal.
    assert (
        client.post(
            f"/assessments/{aid}/finalise",
            params={"override_reason": "   "},
            headers=auth_header(admin),
        ).status_code
        == 409
    )

    reason = "Client deadline; John approved a one-off waiver pending Alice's Certified Lead board."
    ok = client.post(
        f"/assessments/{aid}/finalise",
        params={"override_reason": reason},
        headers=auth_header(admin),
    )
    assert ok.status_code == 200

    # The override is on the audit trail.
    events = client.get(
        f"/certification/{alice.principal.consultant_id}/events", headers=auth_header(admin)
    ).json()
    overrides = [e for e in events if e["kind"] == "override"]
    assert len(overrides) == 1
    assert overrides[0]["reason"] == reason


def test_override_event_requires_a_reason_structurally() -> None:
    from bcap_contracts.certification import CertificationEvent, CertificationEventKind

    now = datetime.now(UTC)
    with pytest.raises(ValueError, match="reason"):
        CertificationEvent(
            id=uuid4(),
            owner_consultant_id=uuid4(),
            created_at=now,
            updated_at=now,
            kind=CertificationEventKind.OVERRIDE,
            recorded_by_consultant_id=uuid4(),
            occurred_at=now,  # no reason
        )


# --- Scoping ----------------------------------------------------------------------------


def test_only_an_admin_can_record_evidence_or_promote(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    aid = str(bob.principal.consultant_id)
    assert (
        client.post(f"/certification/{aid}/coursework", headers=auth_header(alice)).status_code
        == 403
    )
    assert (
        client.post(f"/certification/{aid}/promote", headers=auth_header(alice)).status_code == 403
    )


def test_an_advisor_sees_their_own_record_but_not_anothers(
    client, admin: SeededConsultant, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    assert (
        client.get(
            f"/certification/{alice.principal.consultant_id}", headers=auth_header(alice)
        ).status_code
        == 200
    )
    # Alice cannot see Bob's certification record.
    assert (
        client.get(
            f"/certification/{bob.principal.consultant_id}", headers=auth_header(alice)
        ).status_code
        == 403
    )
    # An admin can see anyone's.
    assert (
        client.get(
            f"/certification/{bob.principal.consultant_id}", headers=auth_header(admin)
        ).status_code
        == 200
    )


def test_endpoints_require_authentication(client, alice: SeededConsultant) -> None:
    assert client.post(f"/certification/{alice.principal.consultant_id}/promote").status_code == 401


# --- Review-driven: the upper promotion rungs, top-of-ladder, ordering, defaults ---------


def test_cannot_reach_observed_lead_without_an_observed_lead(
    client, admin: SeededConsultant
) -> None:
    shadow = seed_consultant_at_level(client, AssessorLevel.SHADOW)
    resp = client.post(
        f"/certification/{shadow.principal.consultant_id}/promote", headers=auth_header(admin)
    )
    assert resp.status_code == 409
    assert "No observed lead recorded" in resp.json()["detail"]


def test_cannot_reach_certified_lead_without_a_signoff(client, admin: SeededConsultant) -> None:
    ol = seed_consultant_at_level(client, AssessorLevel.OBSERVED_LEAD)
    resp = client.post(
        f"/certification/{ol.principal.consultant_id}/promote", headers=auth_header(admin)
    )
    assert resp.status_code == 409
    assert "No sign-off recorded" in resp.json()["detail"]


def test_cannot_promote_past_certified_lead(client, admin: SeededConsultant) -> None:
    lead = seed_consultant_at_level(client, AssessorLevel.CERTIFIED_LEAD)
    resp = client.post(
        f"/certification/{lead.principal.consultant_id}/promote", headers=auth_header(admin)
    )
    assert resp.status_code == 409
    assert "top of the ladder" in resp.json()["detail"]


def test_events_are_appended_in_order(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    aid = str(alice.principal.consultant_id)
    _bring_to_shadow_evidence(client, admin, aid)
    client.post(f"/certification/{aid}/promote", headers=auth_header(admin))
    events = client.get(f"/certification/{aid}/events", headers=auth_header(admin)).json()
    kinds = [e["kind"] for e in events]
    assert kinds == [
        "coursework_completed",
        "exam_recorded",
        "shadow_logged",
        "shadow_logged",
        "promoted",
    ]
    stamps = [e["occurred_at"] for e in events]
    assert stamps == sorted(stamps)  # append-only, chronological
    promoted = events[-1]
    assert promoted["from_level"] == "trained" and promoted["to_level"] == "shadow"


def test_a_fresh_record_defaults_to_trained_and_zero(client, alice: SeededConsultant) -> None:
    rec = client.get(
        f"/certification/{alice.principal.consultant_id}", headers=auth_header(alice)
    ).json()
    assert rec["level"] == "trained"
    assert rec["shadow_count"] == 0
    assert rec["coursework_complete"] is False
    assert rec["exam_score"] is None
