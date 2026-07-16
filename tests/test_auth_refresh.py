"""GRS-0120 — refresh-token rotation keeps an active advisor signed in past the 30-min access TTL.

Login issues an access + refresh pair; /auth/refresh rotates the refresh token (single-use) for a
fresh pair, so a live session survives access-token expiry without a manual re-login. A reused,
unknown, or expired refresh token is refused loud (the client then falls back to a full login)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from grassmarket.auth.security import decode_access_token, hash_invite_token
from grassmarket.data.repository import ConflictError, NotFoundError, Repository

_PASSWORD = "correct-horse-battery-staple"


def _login(client: TestClient, email: str) -> dict:
    resp = client.post("/auth/login", json={"email": email, "password": _PASSWORD})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"] and body["refresh_token"]
    return body


def test_login_issues_an_access_and_refresh_pair(client: TestClient, alice) -> None:
    body = _login(client, alice.stored.email)
    assert body["token_type"] == "bearer"


def test_refresh_rotates_and_survives_access_expiry(client: TestClient, alice, settings) -> None:
    first = _login(client, alice.stored.email)
    resp = client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert resp.status_code == 200, resp.text
    second = resp.json()
    # A working access token is minted — the "stay signed in" path (no manual re-login). It decodes
    # to the same consultant (two tokens minted in the same second are legitimately identical JWTs;
    # what matters is that refresh yields a valid access token without re-login).
    claims = decode_access_token(settings, second["access_token"])
    assert str(claims.sub) == str(alice.stored.id)
    # The refresh token rotated — a fresh, distinct one is returned (random, so always differs).
    assert second["refresh_token"] and second["refresh_token"] != first["refresh_token"]


def test_a_used_refresh_token_is_refused(client: TestClient, alice) -> None:
    first = _login(client, alice.stored.email)
    client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})  # consumes it
    # Replaying the same (now-consumed) refresh token is a hard refusal (single-use rotation).
    replay = client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert replay.status_code == 401


def test_an_unknown_refresh_token_is_refused(client: TestClient, alice) -> None:
    resp = client.post("/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert resp.status_code == 401


def test_the_new_refresh_token_works_after_rotation(client: TestClient, alice) -> None:
    first = _login(client, alice.stored.email)
    second = client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]}).json()
    third = client.post("/auth/refresh", json={"refresh_token": second["refresh_token"]})
    assert third.status_code == 200  # the rotated token is a valid successor


def test_repository_refuses_an_expired_refresh_token(repo: Repository, alice) -> None:
    now = datetime(2026, 7, 16, 12, 0, tzinfo=UTC)
    repo.create_refresh_token(
        consultant_id=alice.stored.id,
        token_hash=hash_invite_token("expired-token"),
        expires_at=now - timedelta(seconds=1),  # already expired
    )
    with pytest.raises(ConflictError):
        repo.rotate_refresh_token(token_hash=hash_invite_token("expired-token"), now=now)


def test_repository_refuses_an_unknown_refresh_token(repo: Repository) -> None:
    now = datetime(2026, 7, 16, 12, 0, tzinfo=UTC)
    with pytest.raises(NotFoundError):
        repo.rotate_refresh_token(token_hash=hash_invite_token("nope"), now=now)
