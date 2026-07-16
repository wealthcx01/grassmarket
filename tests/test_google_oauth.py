"""GRS-0073 — Google OAuth sign-in. The callback verifies a (mocked) Google identity and mints the
existing GM JWT, but sign-in stays invite-only: only a pre-provisioned consultant gets a token, and
the PKCE/state handshake is fail-loud. No live Google calls — the client is injected as a fake."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from fastapi import FastAPI
from fastapi.testclient import TestClient

from grassmarket.auth.google_oauth import GoogleIdentity
from grassmarket.auth.security import decode_access_token
from grassmarket.config import Settings
from grassmarket.data.models import ConsultantORM
from grassmarket.web.dependencies import get_google_oauth_client
from tests.conftest import SeededConsultant


@dataclass
class FakeGoogleClient:
    """Stands in for the real Google OAuth client — no network; a fixed verified identity."""

    email: str
    sub: str = "google-sub-abc123"

    def authorization_url(self, *, state: str, code_challenge: str) -> str:
        return f"https://fake-google/consent?state={state}&code_challenge={code_challenge}"

    def exchange_code(self, *, code: str, code_verifier: str) -> GoogleIdentity:
        return GoogleIdentity(email=self.email, email_verified=True, sub=self.sub)


def _run_flow(
    client: TestClient, app: FastAPI, fake: FakeGoogleClient, *, state_override: str | None = None
):
    """Drive /auth/google/start → /auth/google/callback with the fake client, returning the callback
    response. The signed transaction cookie set by /start is carried by the test client's jar."""
    app.dependency_overrides[get_google_oauth_client] = lambda: fake
    start = client.get("/auth/google/start", follow_redirects=False)
    assert start.status_code == 307
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
    return client.get(
        f"/auth/google/callback?code=auth-code&state={state_override or state}",
        follow_redirects=False,
    )


def test_google_callback_happy_path_mints_valid_jwt(
    client: TestClient, app: FastAPI, settings: Settings, alice: SeededConsultant
) -> None:
    resp = _run_flow(client, app, FakeGoogleClient(email=alice.stored.email))
    assert resp.status_code == 303
    location = resp.headers["location"]
    # The JWT rides in the fragment, NEVER a query string.
    assert "#access_token=" in location
    assert urlparse(location).query == ""
    token = location.split("#access_token=", 1)[1]
    claims = decode_access_token(settings, token)  # accepts → valid GM JWT
    assert claims.email == alice.stored.email

    # The Google id is bound on first sign-in.
    session = app.state.session_factory()
    try:
        row = session.get(ConsultantORM, alice.stored.id)
        assert row is not None and row.google_sub == "google-sub-abc123"
    finally:
        session.close()


def test_unprovisioned_google_email_is_403(client: TestClient, app: FastAPI) -> None:
    resp = _run_flow(client, app, FakeGoogleClient(email="stranger@gmail.com"))
    assert resp.status_code == 403


def test_state_mismatch_is_refused(
    client: TestClient, app: FastAPI, alice: SeededConsultant
) -> None:
    resp = _run_flow(
        client, app, FakeGoogleClient(email=alice.stored.email), state_override="tampered-state"
    )
    assert resp.status_code == 400


def test_callback_without_transaction_cookie_is_refused(
    client: TestClient, app: FastAPI, alice: SeededConsultant
) -> None:
    app.dependency_overrides[get_google_oauth_client] = lambda: FakeGoogleClient(
        email=alice.stored.email
    )
    # No /start → no signed cookie in the jar.
    resp = client.get("/auth/google/callback?code=x&state=y", follow_redirects=False)
    assert resp.status_code == 400


def test_inactive_account_is_refused(
    client: TestClient, app: FastAPI, alice: SeededConsultant
) -> None:
    session = app.state.session_factory()
    try:
        row = session.get(ConsultantORM, alice.stored.id)
        row.is_active = False
        session.add(row)
        session.commit()
    finally:
        session.close()
    resp = _run_flow(client, app, FakeGoogleClient(email=alice.stored.email))
    assert resp.status_code == 401


def test_password_login_still_works_after_migration(
    client: TestClient, alice: SeededConsultant
) -> None:
    # hashed_password is now nullable, but a password account keeps its hash and logs in normally.
    resp = client.post(
        "/auth/login",
        json={"email": alice.stored.email, "password": "correct-horse-battery-staple"},
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_google_start_503_when_unconfigured(client: TestClient) -> None:
    # No dependency override → the real factory refuses because no GM_GOOGLE_* env is set.
    resp = client.get("/auth/google/start", follow_redirects=False)
    assert resp.status_code == 503
