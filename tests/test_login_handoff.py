"""GRS-0074 — cross-site login hand-off. The OAuth callback carries a single-use, short-TTL code
(never the JWT) to the advisory app, which exchanges it server-side. The code is single-use and
expires; CORS is multi-origin. No live Google calls — the client is injected as a fake."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

from fastapi import FastAPI
from fastapi.testclient import TestClient

from grassmarket.config import Settings
from grassmarket.data.models import LoginHandoffCodeORM
from grassmarket.web.dependencies import get_google_oauth_client
from tests.conftest import SeededConsultant
from tests.test_google_oauth import FakeGoogleClient, _run_flow


def _issue_code(client: TestClient, app: FastAPI, alice: SeededConsultant) -> str:
    resp = _run_flow(client, app, FakeGoogleClient(email=alice.stored.email))
    assert resp.status_code == 303
    return parse_qs(urlparse(resp.headers["location"]).query)["code"][0]


def test_exchange_is_single_use(client: TestClient, app: FastAPI, alice: SeededConsultant) -> None:
    code = _issue_code(client, app, alice)
    first = client.post("/auth/session/exchange", json={"code": code})
    assert first.status_code == 200
    # A second exchange of the same code is refused (fail loud).
    second = client.post("/auth/session/exchange", json={"code": code})
    assert second.status_code == 400


def test_exchange_of_expired_code_is_refused(
    client: TestClient, app: FastAPI, alice: SeededConsultant
) -> None:
    code = _issue_code(client, app, alice)
    # Force the stored code to have expired.
    session = app.state.session_factory()
    try:
        row = session.query(LoginHandoffCodeORM).one()
        row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        session.add(row)
        session.commit()
    finally:
        session.close()
    resp = client.post("/auth/session/exchange", json={"code": code})
    assert resp.status_code == 400


def test_exchange_of_unknown_code_is_refused(client: TestClient) -> None:
    assert client.post("/auth/session/exchange", json={"code": "nope"}).status_code == 400


def test_no_jwt_in_the_callback_url(
    client: TestClient, app: FastAPI, alice: SeededConsultant
) -> None:
    app.dependency_overrides[get_google_oauth_client] = lambda: FakeGoogleClient(
        email=alice.stored.email
    )
    resp = _run_flow(client, app, FakeGoogleClient(email=alice.stored.email))
    location = resp.headers["location"]
    assert "access_token" not in location and "eyJ" not in location  # no JWT anywhere in the URL


def test_cors_allows_the_advisory_origin_and_denies_others(client: TestClient) -> None:
    # The default test settings allow http://localhost:3000 (frontend_origin).
    allowed = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"
    denied = client.get("/health", headers={"Origin": "https://evil.example.com"})
    assert denied.headers.get("access-control-allow-origin") is None


def test_cors_origins_property_dedupes_and_includes_extras() -> None:
    settings = Settings(
        env="ci",
        jwt_secret="test-secret-that-is-more-than-thirty-two-characters-long-xx",
        frontend_origin="https://app.example.com",
        frontend_origins_extra="https://www.bruntsfieldcapital.com, https://app.example.com",
    )
    # Advisory app first, extras appended, duplicate dropped.
    assert settings.cors_origins == [
        "https://app.example.com",
        "https://www.bruntsfieldcapital.com",
    ]
