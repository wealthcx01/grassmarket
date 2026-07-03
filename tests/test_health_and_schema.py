"""Health endpoints and schema parity."""

from __future__ import annotations

from bcap_contracts.schemas import check_parity


def test_health_liveness(client) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "grassmarket"


def test_health_readiness_pings_db(client) -> None:
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_committed_schemas_match_models() -> None:
    """The committed JSON Schemas must mirror the Pydantic models — the same check the
    pre-commit `schema-validate` hook runs. Empty list == in sync."""
    assert check_parity() == []
