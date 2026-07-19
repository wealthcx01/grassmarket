"""Auth flow tests — invitation-only signup, login, and the current-identity endpoint, plus the
fail-loud branches (wrong password, reused/expired invitations)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from bcap_contracts.common import ConsultantTier, Role

from grassmarket.auth.service import (
    AuthService,
    ForbiddenInvitationError,
    InvalidInvitationError,
)
from grassmarket.data.repository import Repository
from tests.conftest import SeededConsultant, auth_header


def _service(session_factory, settings) -> tuple[AuthService, object]:
    session = session_factory()
    return AuthService(Repository(session), settings), session


def test_invitation_signup_then_login_and_me(session_factory, settings, alice, client) -> None:
    svc, session = _service(session_factory, settings)
    token = svc.create_invitation(
        inviter_id=alice.stored.id,
        inviter_role=alice.principal.role,
        email="carol@bruntsfieldcapital.com",
    )
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


def test_change_password_rotates_the_credential(client, alice: SeededConsultant) -> None:
    # GRS-0148d: a signed-in advisor changes their own password; the old one stops working and the
    # new one logs in.
    resp = client.post(
        "/auth/change-password",
        headers=auth_header(alice),
        json={
            "current_password": "correct-horse-battery-staple",
            "new_password": "a-brand-new-strong-passphrase",
        },
    )
    assert resp.status_code == 204
    old = client.post(
        "/auth/login",
        json={"email": alice.stored.email, "password": "correct-horse-battery-staple"},
    )
    assert old.status_code == 401
    new = client.post(
        "/auth/login",
        json={"email": alice.stored.email, "password": "a-brand-new-strong-passphrase"},
    )
    assert new.status_code == 200


def test_change_password_wrong_current_is_401(client, alice: SeededConsultant) -> None:
    resp = client.post(
        "/auth/change-password",
        headers=auth_header(alice),
        json={"current_password": "not-my-password", "new_password": "a-brand-new-strong-pass"},
    )
    assert resp.status_code == 401


def test_change_password_weak_new_is_422(client, alice: SeededConsultant) -> None:
    resp = client.post(
        "/auth/change-password",
        headers=auth_header(alice),
        json={"current_password": "correct-horse-battery-staple", "new_password": "short"},
    )
    assert resp.status_code == 422  # the 12-char floor is contract-enforced


def test_change_password_requires_auth(client) -> None:
    resp = client.post(
        "/auth/change-password",
        json={"current_password": "x", "new_password": "a-brand-new-strong-pass"},
    )
    assert resp.status_code == 401


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
    token = svc.create_invitation(
        inviter_id=alice.stored.id,
        inviter_role=alice.principal.role,
        email="dave@bruntsfieldcapital.com",
    )
    svc.accept_invitation(token=token, full_name="Dave", password="a-very-strong-passphrase")
    session.commit()
    with pytest.raises(InvalidInvitationError):
        svc.accept_invitation(token=token, full_name="Dave Again", password="another-strong-pass")
    session.close()


def test_expired_invitation_refused(session_factory, settings, alice) -> None:
    svc, session = _service(session_factory, settings)
    long_ago = datetime.now(UTC) - timedelta(hours=settings.invite_ttl_hours + 1)
    token = svc.create_invitation(
        inviter_id=alice.stored.id,
        inviter_role=alice.principal.role,
        email="erin@bruntsfieldcapital.com",
        now=long_ago,
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


# --- GRS-0042: invitation privilege-escalation is refused ---------------------------------


def test_consultant_cannot_invite_an_admin(client, alice: SeededConsultant) -> None:
    """A non-admin inviting role=admin must be refused (403) — otherwise any consultant could
    self-mint an admin and defeat data scoping entirely."""
    resp = client.post(
        "/auth/invitations",
        json={"email": "attacker@bruntsfieldcapital.com", "role": "admin"},
        headers=auth_header(alice),
    )
    assert resp.status_code == 403


def test_consultant_cannot_invite_an_elevated_tier(client, alice: SeededConsultant) -> None:
    resp = client.post(
        "/auth/invitations",
        json={"email": "climber@bruntsfieldcapital.com", "tier": "consultant"},
        headers=auth_header(alice),
    )
    assert resp.status_code == 403


def test_admin_can_invite_an_admin(client, admin: SeededConsultant) -> None:
    resp = client.post(
        "/auth/invitations",
        json={"email": "second-admin@bruntsfieldcapital.com", "role": "admin"},
        headers=auth_header(admin),
    )
    assert resp.status_code == 201
    assert resp.json()["token"]


def test_service_refuses_role_elevation_from_non_admin(session_factory, settings, alice) -> None:
    svc, session = _service(session_factory, settings)
    with pytest.raises(ForbiddenInvitationError):
        svc.create_invitation(
            inviter_id=alice.stored.id,
            inviter_role=Role.CONSULTANT,
            email="x@bruntsfieldcapital.com",
            role=Role.ADMIN,
        )
    session.close()


def test_service_allows_default_invite_and_admin_elevation(
    session_factory, settings, alice
) -> None:
    svc, session = _service(session_factory, settings)
    # default (consultant / entry tier) from a consultant is fine
    assert svc.create_invitation(
        inviter_id=alice.stored.id, inviter_role=Role.CONSULTANT, email="ok@bruntsfieldcapital.com"
    )
    # admin may grant an elevated tier
    assert svc.create_invitation(
        inviter_id=alice.stored.id,
        inviter_role=Role.ADMIN,
        email="tiered@bruntsfieldcapital.com",
        tier=ConsultantTier.CONSULTANT,
    )
    session.close()
