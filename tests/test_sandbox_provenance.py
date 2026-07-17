"""GRS-0119 / ADR-0029 — sandbox self-approve mode.

A non-production (sandbox) record self-approves: the owning tester finalises their OWN assessment
runs the real deliverable generation WITHOUT a second rater or committee — so a solo tester reaches
the payoff. Crucially, the production dual-rating + committee gate is UNCHANGED, and sandbox records
are segregated: never ratified into the benchmark, provenance immutable, non-promotable."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from grassmarket.data.repository import ConflictError, Repository
from tests.conftest import SeededConsultant, auth_header
from tests.test_assessment_lifecycle import _body, _scoreable_partial_doc

_NOW = datetime(2026, 7, 17, tzinfo=UTC)


def _create(client: TestClient, owner: SeededConsultant, *, provenance: str | None) -> str:
    payload: dict = {"subject": "Test Co"}
    if provenance is not None:
        payload["provenance"] = provenance
    resp = client.post("/assessments", json=payload, headers=auth_header(owner))
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _fill_scoreable(client: TestClient, aid: str, owner: SeededConsultant) -> None:
    client.put(
        f"/assessments/{aid}", json=_body(_scoreable_partial_doc()), headers=auth_header(owner)
    )


def test_sandbox_finalises_solo_without_dual_rating_or_committee(
    client: TestClient, alice: SeededConsultant
) -> None:
    aid = _create(client, alice, provenance="sandbox")
    assert (
        client.get(f"/assessments/{aid}", headers=auth_header(alice)).json()["provenance"]
        == "sandbox"
    )
    _fill_scoreable(client, aid, alice)
    # No reach_consensus, no committee approval — the solo tester self-approves (ADR-0029).
    resp = client.post(f"/assessments/{aid}/finalise", headers=auth_header(alice))
    assert resp.status_code == 200, resp.text
    assert resp.json()["state"] == "finalised"


def test_production_still_requires_the_full_gate(
    client: TestClient, alice: SeededConsultant
) -> None:
    # The SAME solo document under a production record is refused — the gate is unchanged.
    aid = _create(client, alice, provenance=None)  # default production
    assert (
        client.get(f"/assessments/{aid}", headers=auth_header(alice)).json()["provenance"]
        == "production"
    )
    _fill_scoreable(client, aid, alice)
    resp = client.post(f"/assessments/{aid}/finalise", headers=auth_header(alice))
    assert resp.status_code == 409
    detail = resp.json()["detail"].lower()
    assert "dual-rating" in detail or "consensus" in detail


def test_a_client_cannot_create_a_demo_record(client: TestClient, alice: SeededConsultant) -> None:
    # Demo records are seeded server-side only; a client asking for "demo" gets a production record,
    # never a governance bypass it didn't earn (ADR-0029).
    aid = _create(client, alice, provenance="demo")
    assert (
        client.get(f"/assessments/{aid}", headers=auth_header(alice)).json()["provenance"]
        == "production"
    )


def test_sandbox_provenance_is_immutable_across_updates(
    client: TestClient, alice: SeededConsultant
) -> None:
    aid = _create(client, alice, provenance="sandbox")
    _fill_scoreable(client, aid, alice)  # a document autosave must never change provenance
    assert (
        client.get(f"/assessments/{aid}", headers=auth_header(alice)).json()["provenance"]
        == "sandbox"
    )


def test_a_sandbox_run_cannot_enter_the_benchmark(
    client: TestClient, repo: Repository, alice: SeededConsultant
) -> None:
    aid = _create(client, alice, provenance="sandbox")
    _fill_scoreable(client, aid, alice)
    finalised = client.post(f"/assessments/{aid}/finalise", headers=auth_header(alice)).json()
    run_id = UUID(finalised["scoring_run_id"])
    repo.finalise_scoring_run(
        alice.principal, run_id
    )  # seal the run so only provenance can block it
    # A sandbox record is non-production — its throwaway score is segregated from the peers.
    with pytest.raises(ConflictError, match="non-production"):
        repo.ingest_benchmark(alice.principal, run_id, sector=None, now=_NOW)
