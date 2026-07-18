"""CRM rebuild — prospect editing + first-class Contact entity tests (GRS-0111).

Pins: a prospect's fields are editable via PATCH (owner-scoped, empty company refused); contacts are
a first-class, owner-scoped entity (many per prospect); making one primary demotes the others and
mirrors name/email onto the prospect (the win-probability scorer reads those); deleting the primary
clears the mirror; and cross-owner access is a 404, never a leak.
"""

from __future__ import annotations

import pytest

from grassmarket.data.repository import ConflictError, Repository, ScopeViolationError
from tests.conftest import SeededConsultant, auth_header


def test_update_prospect_patches_only_sent_fields(
    repo: Repository, alice: SeededConsultant
) -> None:
    p = repo.create_prospect(alice.principal, company_name="Acme", sector="Broking")
    updated = repo.update_prospect(
        alice.principal, p.id, website="https://acme.com", notes="Keen on the workshop."
    )
    assert updated.website == "https://acme.com"
    assert updated.notes == "Keen on the workshop."
    assert updated.sector == "Broking"  # untouched (not sent)
    assert updated.company_name == "Acme"


def test_update_prospect_refuses_empty_company(repo: Repository, alice: SeededConsultant) -> None:
    p = repo.create_prospect(alice.principal, company_name="Acme")
    with pytest.raises(ConflictError):
        repo.update_prospect(alice.principal, p.id, company_name="   ")


def test_contacts_are_first_class_and_owner_scoped(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    p = repo.create_prospect(alice.principal, company_name="Acme")
    c1 = repo.create_contact(alice.principal, p.id, name="Jo Lee", email="jo@acme.com", title="CTO")
    repo.create_contact(alice.principal, p.id, name="Sam Fox", phone="+44 20 7000")
    contacts = repo.list_contacts(alice.principal, p.id)
    assert {c.name for c in contacts} == {"Jo Lee", "Sam Fox"}
    assert c1.title == "CTO"
    # Bob cannot see or touch Alice's contacts or prospect.
    with pytest.raises(ScopeViolationError):
        repo.list_contacts(bob.principal, p.id)


def test_making_a_contact_primary_demotes_others_and_mirrors_to_prospect(
    repo: Repository, alice: SeededConsultant
) -> None:
    p = repo.create_prospect(alice.principal, company_name="Acme")
    a = repo.create_contact(
        alice.principal, p.id, name="Jo Lee", email="jo@acme.com", is_primary=True
    )
    b = repo.create_contact(alice.principal, p.id, name="Sam Fox", email="sam@acme.com")

    # Alice's prospect mirrors the primary (the win-probability scorer reads these fields).
    prospect = repo.get_prospect(alice.principal, p.id)
    assert prospect.primary_contact_name == "Jo Lee"
    assert prospect.primary_contact_email == "jo@acme.com"

    # Promote Sam → Jo is demoted, the mirror updates.
    repo.update_contact(alice.principal, b.id, is_primary=True)
    contacts = {c.id: c for c in repo.list_contacts(alice.principal, p.id)}
    assert contacts[b.id].is_primary is True
    assert contacts[a.id].is_primary is False
    assert repo.get_prospect(alice.principal, p.id).primary_contact_name == "Sam Fox"


def test_deleting_the_primary_clears_the_mirror(repo: Repository, alice: SeededConsultant) -> None:
    p = repo.create_prospect(alice.principal, company_name="Acme")
    c = repo.create_contact(
        alice.principal, p.id, name="Jo Lee", email="jo@acme.com", is_primary=True
    )
    repo.delete_contact(alice.principal, c.id)
    assert repo.list_contacts(alice.principal, p.id) == []
    prospect = repo.get_prospect(alice.principal, p.id)
    assert prospect.primary_contact_name is None and prospect.primary_contact_email is None


# --- HTTP surface -----------------------------------------------------------------------
def test_http_patch_prospect_and_contact_crud(client, alice: SeededConsultant) -> None:
    pid = client.post(
        "/prospects",
        json={"company_name": "Meridian", "website": "https://meridian.co"},
        headers=auth_header(alice),
    ).json()["id"]

    patched = client.patch(
        f"/prospects/{pid}", json={"sector": "Wealth", "notes": "Warm."}, headers=auth_header(alice)
    )
    assert patched.status_code == 200 and patched.json()["sector"] == "Wealth"

    created = client.post(
        f"/prospects/{pid}/contacts",
        json={"name": "Jo Lee", "email": "jo@meridian.co", "is_primary": True},
        headers=auth_header(alice),
    )
    assert created.status_code == 201
    cid = created.json()["id"]

    listed = client.get(f"/prospects/{pid}/contacts", headers=auth_header(alice)).json()
    assert [c["id"] for c in listed] == [cid]
    # Primary mirrored onto the prospect.
    assert (
        client.get(f"/prospects/{pid}", headers=auth_header(alice)).json()["primary_contact_name"]
        == "Jo Lee"
    )

    assert (
        client.patch(
            f"/prospects/{pid}/contacts/{cid}", json={"title": "COO"}, headers=auth_header(alice)
        ).json()["title"]
        == "COO"
    )
    assert (
        client.delete(f"/prospects/{pid}/contacts/{cid}", headers=auth_header(alice)).status_code
        == 204
    )


def test_http_cross_owner_prospect_edit_is_404(
    client, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    pid = client.post(
        "/prospects", json={"company_name": "Alice Co"}, headers=auth_header(alice)
    ).json()["id"]
    assert (
        client.patch(
            f"/prospects/{pid}", json={"sector": "x"}, headers=auth_header(bob)
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/prospects/{pid}/contacts", json={"name": "Mallory"}, headers=auth_header(bob)
        ).status_code
        == 404
    )
