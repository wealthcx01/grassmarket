"""Prediction register + benchmark over HTTP (GRS-0031). The maths + anonymisation are proven at the
repository level in tests/test_predictions.py; here we pin the router wiring end to end.
"""

from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from grassmarket.data.repository import Repository
from tests.conftest import SeededConsultant, auth_header
from tests.test_scoring_run_persistence import _create

_LEVERS = [
    {
        "lever": "cost_to_serve",
        "npv": {"amount_minor": 10_000_000, "currency": "GBP", "assumption_register_ref": "a1"},
        "assumption_refs": ["a1"],
    },
]


def _finalised_run_id(session_factory: sessionmaker[Session], owner: SeededConsultant) -> str:
    session = session_factory()
    try:
        repo = Repository(session)
        run = _create(repo, owner)
        repo.finalise_scoring_run(owner.principal, run.id)
        session.commit()
        return str(run.id)
    finally:
        session.close()


def _run_id(session_factory: sessionmaker[Session], owner: SeededConsultant) -> str:
    session = session_factory()
    try:
        run = _create(Repository(session), owner)
        session.commit()
        return str(run.id)
    finally:
        session.close()


def test_register_list_and_realise_over_http(
    client, alice: SeededConsultant, session_factory
) -> None:
    run_id = _run_id(session_factory, alice)
    registered = client.post(
        "/predictions",
        json={
            "scoring_run_id": run_id,
            "levers": _LEVERS,
            "horizon_months": 12,
            "probability": 0.8,
            "follow_up_due": "2026-01-01",
        },
        headers=auth_header(alice),
    )
    assert registered.status_code == 201, registered.text
    pred = registered.json()[0]
    assert pred["lever"] == "cost_to_serve"
    assert pred["outcome"] == "pending"

    assert len(client.get("/predictions", headers=auth_header(alice)).json()) == 1
    # The follow-up (past due) is surfaced.
    due = client.get("/predictions/follow-ups/due", headers=auth_header(alice)).json()
    assert [p["id"] for p in due] == [pred["id"]]

    realised = client.post(
        f"/predictions/{pred['id']}/realise",
        json={"realised_delta_minor": 12_000_000, "currency": "GBP", "realised_ref": "actuals"},
        headers=auth_header(alice),
    )
    assert realised.status_code == 200
    body = realised.json()
    assert body["outcome"] == "hit"
    assert round(body["brier_score"], 6) == 0.04


def test_benchmark_ingest_and_list_over_http(
    client, alice: SeededConsultant, session_factory
) -> None:
    run_id = _finalised_run_id(session_factory, alice)
    ingested = client.post(
        "/benchmark/ingest",
        json={"scoring_run_id": run_id, "sector": "brokerage"},
        headers=auth_header(alice),
    )
    assert ingested.status_code == 201, ingested.text
    row = ingested.json()
    assert row["sector"] == "brokerage"
    assert "owner_consultant_id" not in row  # de-identified
    assert row["id"] in {
        r["id"] for r in client.get("/benchmark", headers=auth_header(alice)).json()
    }


def test_benchmark_sector_is_a_closed_vocabulary(
    client, alice: SeededConsultant, session_factory
) -> None:
    # A free-text sector (where a client name could be typed) is refused — the closed vocabulary is
    # the anonymisation guarantee's last soft spot, and it is shut.
    run_id = _finalised_run_id(session_factory, alice)
    resp = client.post(
        "/benchmark/ingest",
        json={"scoring_run_id": run_id, "sector": "Meridian Securities Ltd"},
        headers=auth_header(alice),
    )
    assert resp.status_code == 422


def test_prediction_endpoints_require_authentication(client) -> None:
    assert client.get("/predictions").status_code == 401
    assert client.post("/predictions", json={}).status_code == 401
    assert client.get("/benchmark").status_code == 401
