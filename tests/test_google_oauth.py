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
    hd: str | None = None  # the verified Workspace hosted-domain claim (GRS-0173)

    def authorization_url(self, *, state: str, code_challenge: str) -> str:
        return f"https://fake-google/consent?state={state}&code_challenge={code_challenge}"

    def exchange_code(self, *, code: str, code_verifier: str) -> GoogleIdentity:
        return GoogleIdentity(email=self.email, email_verified=True, sub=self.sub, hd=self.hd)


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


def test_google_callback_hands_off_code_then_exchange_mints_jwt(
    client: TestClient, app: FastAPI, settings: Settings, alice: SeededConsultant
) -> None:
    resp = _run_flow(client, app, FakeGoogleClient(email=alice.stored.email))
    assert resp.status_code == 303
    location = resp.headers["location"]
    # The redirect carries ONLY the opaque one-time code — never the JWT (GRS-0074).
    assert "access_token" not in location
    code = parse_qs(urlparse(location).query)["code"][0]

    exch = client.post("/auth/session/exchange", json={"code": code})
    assert exch.status_code == 200
    claims = decode_access_token(settings, exch.json()["access_token"])  # valid GM JWT
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


# --- Workspace domain SSO auto-provisioning (ADR-0044, GRS-0173) --------------------------------

import pytest  # noqa: E402

from grassmarket.auth.service import (  # noqa: E402
    AuthService,
    InvalidCredentialsError,
    UnprovisionedGoogleAccountError,
)
from grassmarket.data.repository import Principal, Repository  # noqa: E402

_DOMAIN = "bruntsfield.capital"


def _domain_settings(**over) -> Settings:
    return Settings(
        env="ci",
        jwt_secret="test-secret-that-is-more-than-thirty-two-characters-long-xxxxx",
        database_url="sqlite+pysqlite:///:memory:",
        google_workspace_domain=_DOMAIN,
        **over,
    )


def _service(session_factory, settings: Settings) -> tuple[AuthService, object]:
    session = session_factory()
    return AuthService(Repository(session), settings), session


def test_unknown_tier_refuses_at_settings_load() -> None:
    with pytest.raises(ValueError, match="not a valid consultant tier"):
        _domain_settings(google_autoprovision_tier="emperor")


def test_verify_id_token_surfaces_hd(monkeypatch) -> None:
    """`_verify_id_token` carries the `hd` from the JWKS-verified claims; absent → None."""
    import jwt as pyjwt

    from grassmarket.auth.google_oauth import HttpGoogleOAuthClient

    monkeypatch.setattr(
        pyjwt,
        "PyJWKClient",
        lambda uri: type(
            "K", (), {"get_signing_key_from_jwt": lambda self, t: type("S", (), {"key": "k"})()}
        )(),
    )
    base = {
        "iss": "https://accounts.google.com",
        "sub": "s1",
        "email": "a@bruntsfield.capital",
        "email_verified": True,
    }

    def fake_decode(token, key, **kw):
        return {**base, **({"hd": _DOMAIN} if token == "with-hd" else {})}

    monkeypatch.setattr(pyjwt, "decode", fake_decode)
    oauth = HttpGoogleOAuthClient(client_id="cid", client_secret="sec", redirect_uri="https://x/cb")
    assert oauth._verify_id_token("with-hd").hd == _DOMAIN
    assert oauth._verify_id_token("no-hd").hd is None


def test_autoprovisions_a_matching_domain_account(session_factory) -> None:
    svc, session = _service(session_factory, _domain_settings())
    try:
        svc.begin_google_session(
            email="john.smith@bruntsfield.capital", google_sub="g-new", hd=_DOMAIN
        )
        repo = Repository(session)
        stored = repo.get_consultant_by_email("john.smith@bruntsfield.capital")
        assert stored is not None
        assert stored.role.value == "consultant"  # never elevated (GRS-0042)
        assert stored.tier.value == "venture_associate"  # the configured default
        assert stored.full_name == "John Smith"  # derived from the local part
        assert stored.hashed_password is None  # OAuth-only account
        row = session.get(ConsultantORM, stored.id)
        assert row.google_sub == "g-new"
        # The auto-provision audit event is recorded (read the ORM; the log API is admin-only).
        from grassmarket.data.models import AuditEventORM

        events = [
            e for e in session.query(AuditEventORM).all() if e.actor_consultant_id == stored.id
        ]
        assert any(e.event_type == "auth_account_autoprovisioned" for e in events)
    finally:
        session.close()


def test_unknown_email_without_hd_is_refused(session_factory) -> None:
    svc, session = _service(session_factory, _domain_settings())
    try:
        with pytest.raises(UnprovisionedGoogleAccountError):
            svc.begin_google_session(email="stranger@gmail.com", google_sub="g", hd=None)
    finally:
        session.close()


def test_unknown_email_with_other_domain_is_refused(session_factory) -> None:
    svc, session = _service(session_factory, _domain_settings())
    try:
        with pytest.raises(UnprovisionedGoogleAccountError):
            svc.begin_google_session(email="x@other.example", google_sub="g", hd="other.example")
    finally:
        session.close()


def test_matching_hd_but_feature_off_is_refused(session_factory) -> None:
    """With the domain UNSET, matching hd changes nothing — today's invite-only flow exactly."""
    off = Settings(
        env="ci",
        jwt_secret="test-secret-that-is-more-than-thirty-two-characters-long-xxxxx",
        database_url="sqlite+pysqlite:///:memory:",
    )
    svc, session = _service(session_factory, off)
    try:
        with pytest.raises(UnprovisionedGoogleAccountError):
            svc.begin_google_session(email="new@bruntsfield.capital", google_sub="g", hd=_DOMAIN)
    finally:
        session.close()


def test_existing_invited_domain_consultant_is_not_duplicated(
    session_factory, alice: SeededConsultant
) -> None:
    svc, session = _service(session_factory, _domain_settings())
    try:
        svc.begin_google_session(email=alice.stored.email, google_sub="g-bind", hd=_DOMAIN)
        # Bound, no autoprovision event, one row for the email (read the ORM directly).
        from grassmarket.data.models import AuditEventORM

        row = session.get(ConsultantORM, alice.stored.id)
        assert row.google_sub == "g-bind"
        events = [
            e
            for e in session.query(AuditEventORM).all()
            if e.actor_consultant_id == alice.stored.id
        ]
        assert not any(e.event_type == "auth_account_autoprovisioned" for e in events)
    finally:
        session.close()


def test_inactive_domain_consultant_is_refused_not_reprovisioned(
    session_factory, alice: SeededConsultant
) -> None:
    # Deactivate alice, then a domain sign-in must be refused, not auto-provision a duplicate.
    s0 = session_factory()
    row = s0.get(ConsultantORM, alice.stored.id)
    row.is_active = False
    s0.add(row)
    s0.commit()
    s0.close()
    svc, session = _service(session_factory, _domain_settings())
    try:
        with pytest.raises(InvalidCredentialsError):
            svc.begin_google_session(email=alice.stored.email, google_sub="g", hd=_DOMAIN)
        # No duplicate created.
        rows = [r for r in session.query(ConsultantORM).all() if r.email == alice.stored.email]
        assert len(rows) == 1
    finally:
        session.close()


def test_second_sign_in_resolves_the_same_autoprovisioned_account(session_factory) -> None:
    settings = _domain_settings()
    svc1, s1 = _service(session_factory, settings)
    svc1.begin_google_session(email="jo@bruntsfield.capital", google_sub="g-jo", hd=_DOMAIN)
    s1.close()
    svc2, s2 = _service(session_factory, settings)
    try:
        svc2.begin_google_session(email="jo@bruntsfield.capital", google_sub="g-jo", hd=_DOMAIN)
        rows = [r for r in s2.query(ConsultantORM).all() if r.email == "jo@bruntsfield.capital"]
        assert len(rows) == 1  # exactly one consultant row
    finally:
        s2.close()


def test_autoprovisioned_account_has_an_empty_scoped_book(session_factory) -> None:
    svc, session = _service(session_factory, _domain_settings())
    try:
        svc.begin_google_session(email="fresh@bruntsfield.capital", google_sub="g-f", hd=_DOMAIN)
        repo = Repository(session)
        stored = repo.get_consultant_by_email("fresh@bruntsfield.capital")
        principal = Principal(consultant_id=stored.id, role=stored.role)
        assert repo.list_assessments(principal) == []
        assert repo.list_prospects(principal) == []
        assert repo.list_commission_lines(principal) == []
    finally:
        session.close()
