"""The invitation-only onboarding flow, end-to-end over HTTP (GRS-0034).

Existing auth tests accept invitations through the service layer; this exercises the exact path the
launch cohort takes over the wire — POST /auth/invitations -> POST /auth/accept-invitation ->
/auth/login -> /auth/me -> a first owner-scoped read. It closes the gap that the /accept-invitation
endpoint itself had no HTTP coverage, and is the "invitation-only flow exercised" launch artifact.
"""

from __future__ import annotations

from tests.conftest import SeededConsultant, auth_header

_NEW_EMAIL = "grace@bruntsfieldcapital.com"
_PASSPHRASE = "a-very-strong-passphrase"  # AcceptInvitationRequest requires >= 12 chars


def _invite(client, inviter: SeededConsultant, email: str = _NEW_EMAIL) -> str:
    resp = client.post("/auth/invitations", json={"email": email}, headers=auth_header(inviter))
    assert resp.status_code == 201, resp.text
    token = resp.json()["token"]
    assert token
    return token


def test_full_invitation_flow_over_http(client, alice: SeededConsultant) -> None:
    token = _invite(client, alice)

    accepted = client.post(
        "/auth/accept-invitation",
        json={"token": token, "full_name": "Grace", "password": _PASSPHRASE},
    )
    assert accepted.status_code == 201, accepted.text
    assert accepted.json()["email"] == _NEW_EMAIL
    assert "hashed_password" not in accepted.json()  # the hash never leaves storage

    login = client.post("/auth/login", json={"email": _NEW_EMAIL, "password": _PASSPHRASE})
    assert login.status_code == 200
    access = login.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200
    assert me.json()["email"] == _NEW_EMAIL

    # The new advisor is owner-scoped from the first request: they see only their own (empty)
    # pipeline, not alice's — scoping is absolute (CLAUDE.md #9), enforced from onboarding onward.
    prospects = client.get("/prospects", headers={"Authorization": f"Bearer {access}"})
    assert prospects.status_code == 200
    assert prospects.json() == []


def test_accept_invitation_with_bad_token_is_400(client, alice: SeededConsultant) -> None:
    resp = client.post(
        "/auth/accept-invitation",
        json={"token": "not-a-real-token", "full_name": "Nobody", "password": _PASSPHRASE},
    )
    assert resp.status_code == 400


def test_invitation_token_cannot_be_reused_over_http(client, alice: SeededConsultant) -> None:
    token = _invite(client, alice, email="heidi@bruntsfieldcapital.com")
    first = client.post(
        "/auth/accept-invitation",
        json={"token": token, "full_name": "Heidi", "password": _PASSPHRASE},
    )
    assert first.status_code == 201
    reuse = client.post(
        "/auth/accept-invitation",
        json={"token": token, "full_name": "Heidi Again", "password": _PASSPHRASE},
    )
    assert reuse.status_code == 400  # a consumed invitation is dead


def test_create_invitation_requires_authentication(client) -> None:
    # The invite endpoint is authenticated — an anonymous caller cannot mint invitations.
    assert client.post("/auth/invitations", json={"email": "x@y.com"}).status_code == 401
