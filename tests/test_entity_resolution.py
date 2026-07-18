"""Entity resolution (GRS-0100, ADR-0033).

A subject resolves to a canonical company through the injectable registry (a seeded stub). The
registry only proposes candidates — an ambiguous query returns several, never one silent pick. The
create endpoint validates the chosen id (a fabricated link is a 400), null is the manual fallback,
and two assessments of the same company share the id (owner-scoped dedup).
"""

from __future__ import annotations

from grassmarket.data.repository import Repository
from grassmarket.entities import StubEntityRegistry, active_entity_registry
from tests.conftest import SeededConsultant, auth_header


def test_registry_ranks_exact_prefix_and_alias() -> None:
    r = StubEntityRegistry()
    assert r.search("revolut")[0].entity_id == "revolut"  # exact/prefix wins
    # An alias resolves to the same canonical entity ("Revolut Ltd" -> revolut).
    assert any(e.entity_id == "revolut" for e in r.search("revolut ltd"))
    assert r.get("monzo") is not None
    assert r.get("does-not-exist") is None


def test_ambiguous_query_returns_several_never_one_silent_pick() -> None:
    r = StubEntityRegistry()
    hits = r.search("ba")  # substring shared by several (coinbase, nubank, starling, ...)
    assert len(hits) > 1  # the human picks; nothing is auto-resolved


def test_create_with_entity_id_and_owner_scoped_dedup(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    a1 = repo.create_assessment(alice.principal, subject="Revolut", entity_id="revolut")
    a2 = repo.create_assessment(alice.principal, subject="Revolut Ltd", entity_id="revolut")
    assert a1.entity_id == a2.entity_id == "revolut"
    # Both of Alice's assessments dedup to the one entity.
    mine = repo.list_assessments_for_entity(alice.principal, "revolut")
    assert {a.id for a in mine} == {a1.id, a2.id}
    # A manual (unlinked) subject stays null.
    manual = repo.create_assessment(alice.principal, subject="Some Private Firm")
    assert manual.entity_id is None
    # Owner-scoped: Bob's book is his own.
    repo.create_assessment(bob.principal, subject="Revolut", entity_id="revolut")
    assert len(repo.list_assessments_for_entity(bob.principal, "revolut")) == 1
    assert len(repo.list_assessments_for_entity(alice.principal, "revolut")) == 2


def test_http_search_create_validates_and_lists(alice: SeededConsultant, client) -> None:
    # Search proposes candidates.
    s = client.get("/entities/search", params={"q": "monzo"}, headers=auth_header(alice))
    assert s.status_code == 200 and any(e["entity_id"] == "monzo" for e in s.json())

    # A fabricated entity link is refused (fail loud, #3).
    bad = client.post(
        "/assessments",
        json={"subject": "X", "entity_id": "not-a-real-entity"},
        headers=auth_header(alice),
    )
    assert bad.status_code == 400

    # A valid link is stored and dedup-listable.
    good = client.post(
        "/assessments", json={"subject": "Monzo", "entity_id": "monzo"}, headers=auth_header(alice)
    )
    assert good.status_code == 201 and good.json()["entity_id"] == "monzo"
    listed = client.get("/assessments/for-entity/monzo", headers=auth_header(alice))
    assert listed.status_code == 200 and len(listed.json()) == 1


def test_active_registry_is_the_stub() -> None:
    assert active_entity_registry().get("revolut") is not None
