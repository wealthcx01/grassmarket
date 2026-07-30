"""Helpers for the founder review gate (GRS-0188, ADR-0041).

A production assessment cannot finalise until the founder has approved the document *as it stands*.
Tests that used to call `reach_consensus` + `approve_committee_queue` now call
`submit_and_approve` instead. The order matters and is the whole point of the gate: approve after
the last edit, or the hash will not match.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import SeededConsultant, auth_header


def submit_and_approve(
    client: TestClient,
    assessment_id: str,
    owner: SeededConsultant,
    founder: SeededConsultant,
) -> None:
    """The full handshake: the advisor submits, the founder approves the current version."""
    submitted = client.post(
        f"/assessments/{assessment_id}/submit-for-review", headers=auth_header(owner)
    )
    assert submitted.status_code == 200, submitted.text
    approved = client.post(
        f"/assessments/{assessment_id}/founder-approval", headers=auth_header(founder)
    )
    assert approved.status_code == 201, approved.text


def current_approval(
    client: TestClient, assessment_id: str, caller: SeededConsultant
) -> dict | None:
    resp = client.get(f"/assessments/{assessment_id}/founder-approval", headers=auth_header(caller))
    assert resp.status_code == 200, resp.text
    return resp.json()
