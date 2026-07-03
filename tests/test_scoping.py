"""Data-scoping tests — MANDATORY from day one (CLAUDE.md non-negotiable #9).

A consultant sees only their own resources. These tests prove it at both layers: the repository
(the single enforcement point) and the HTTP surface (which must not even reveal existence).
"""

from __future__ import annotations

import uuid

import pytest

from grassmarket.data.repository import (
    NotFoundError,
    Repository,
    ScopeViolationError,
)
from tests.conftest import SeededConsultant, auth_header


# --------------------------------------------------------------------- repository layer
def test_consultant_sees_only_own_prospects(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    repo.create_prospect(alice.principal, company_name="Alice Co")
    repo.create_prospect(bob.principal, company_name="Bob Co")

    alice_list = repo.list_prospects(alice.principal)
    bob_list = repo.list_prospects(bob.principal)

    assert [p.company_name for p in alice_list] == ["Alice Co"]
    assert [p.company_name for p in bob_list] == ["Bob Co"]
    assert all(p.owner_consultant_id == alice.principal.consultant_id for p in alice_list)


def test_cross_owner_get_is_refused(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    prospect = repo.create_prospect(alice.principal, company_name="Alice Co")
    with pytest.raises(ScopeViolationError):
        repo.get_prospect(bob.principal, prospect.id)


def test_cross_owner_stage_update_is_refused(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    from bcap_contracts.entities import PipelineStage

    prospect = repo.create_prospect(alice.principal, company_name="Alice Co")
    with pytest.raises(ScopeViolationError):
        repo.update_prospect_stage(bob.principal, prospect.id, PipelineStage.QUALIFIED)


def test_missing_prospect_raises_not_found(repo: Repository, alice: SeededConsultant) -> None:
    with pytest.raises(NotFoundError):
        repo.get_prospect(alice.principal, uuid.uuid4())


def test_admin_can_access_any_prospect(
    repo: Repository, alice: SeededConsultant, admin: SeededConsultant
) -> None:
    prospect = repo.create_prospect(alice.principal, company_name="Alice Co")
    # Admin visibility is explicit and tested — it is the one widening of scope.
    fetched = repo.get_prospect(admin.principal, prospect.id)
    assert fetched.id == prospect.id
    assert len(repo.list_prospects(admin.principal)) == 1


def test_create_prospect_owner_is_principal_not_caller_input(
    repo: Repository, alice: SeededConsultant
) -> None:
    # The owner is taken from the principal; there is no way to create a prospect for someone else.
    prospect = repo.create_prospect(alice.principal, company_name="Alice Co")
    assert prospect.owner_consultant_id == alice.principal.consultant_id


# --------------------------------------------------------------------- HTTP layer
def test_http_cross_owner_get_is_404_not_403(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    created = client.post(
        "/prospects", json={"company_name": "Alice Co"}, headers=auth_header(alice)
    )
    assert created.status_code == 201
    prospect_id = created.json()["id"]

    # Bob must not learn that the resource exists: 404, never 403.
    resp = client.get(f"/prospects/{prospect_id}", headers=auth_header(bob))
    assert resp.status_code == 404


def test_http_list_is_scoped(client, alice: SeededConsultant, bob: SeededConsultant) -> None:
    client.post("/prospects", json={"company_name": "Alice Co"}, headers=auth_header(alice))
    client.post("/prospects", json={"company_name": "Bob Co"}, headers=auth_header(bob))

    alice_resp = client.get("/prospects", headers=auth_header(alice))
    assert [p["company_name"] for p in alice_resp.json()] == ["Alice Co"]


def test_http_requires_authentication(client) -> None:
    assert client.get("/prospects").status_code == 401
