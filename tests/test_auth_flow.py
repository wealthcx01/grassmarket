"""Auth flow tests — invitation-only signup, login, and the current-identity endpoint, plus the
fail-loud branches (wrong password, reused/expired invitations)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from grassmarket.auth.service import (
    AuthService,
    InvalidInvitationError,
)
from grassmarket.data.repository import Repository
from tests.conftest import SeededConsultant, auth_header


def _service(session_factory, settings) -> tuple[AuthService, object]:
    session = session_factory()
    return AuthService(Repository(session), settings), session


def test_invitation_signup_then_login_and_me(session_factory, settings, alice, client) -> None:
    svc, session = _service(session_factory, settings)
    token = svc.create_invitation(inviter_id=alice.stored.id, email="carol@bruntsfieldcapital.com")
    consultant = svc.accept_invitation(
        token=token, full_name="Carol", password="a-very-strong-passphrase"
    )
    session.commit()
    session.close()
    assert consultant.email == "carol@bruntsfieldcapital.com"

    login = client.post(
        "/auth/login",
        json={"email": "carol@bruntsfieldcapital.com", "password": "a-very-strong-passphrase"},
    )
    assert login.status_code == 200
    access = login.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200
    assert me.json()["email"] == "carol@bruntsfieldcapital.com"
    assert "hashed_password" not in me.json()  # the hash never leaves the storage layer


def test_login_wrong_password_is_401(client, alice: SeededConsultant) -> None:
    resp = client.post(
        "/auth/login", json={"email": alice.stored.email, "password": "wrong-password"}
    )
    assert resp.status_code == 401


def test_login_unknown_email_is_401(client) -> None:
    resp = client.post(
        "/auth/login", json={"email": "nobody@bruntsfieldcapital.com", "password": "whatever12345"}
    )
    assert resp.status_code == 401


def test_invitation_cannot_be_reused(session_factory, settings, alice) -> None:
    svc, session = _service(session_factory, settings)
    token = svc.create_invitation(inviter_id=alice.stored.id, email="dave@bruntsfieldcapital.com")
    svc.accept_invitation(token=token, full_name="Dave", password="a-very-strong-passphrase")
    session.commit()
    with pytest.raises(InvalidInvitationError):
        svc.accept_invitation(token=token, full_name="Dave Again", password="another-strong-pass")
    session.close()


def test_expired_invitation_refused(session_factory, settings, alice) -> None:
    svc, session = _service(session_factory, settings)
    long_ago = datetime.now(UTC) - timedelta(hours=settings.invite_ttl_hours + 1)
    token = svc.create_invitation(
        inviter_id=alice.stored.id, email="erin@bruntsfieldcapital.com", now=long_ago
    )
    session.commit()
    with pytest.raises(InvalidInvitationError):
        svc.accept_invitation(token=token, full_name="Erin", password="a-very-strong-passphrase")
    session.close()


def test_create_invitation_endpoint_requires_auth(client) -> None:
    assert client.post("/auth/invitations", json={"email": "x@y.com"}).status_code == 401


def test_create_invitation_endpoint_authenticated(client, alice: SeededConsultant) -> None:
    resp = client.post(
        "/auth/invitations",
        json={"email": "frank@bruntsfieldcapital.com"},
        headers=auth_header(alice),
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "frank@bruntsfieldcapital.com"
    assert resp.json()["token"]  # raw token returned once for out-of-band delivery
