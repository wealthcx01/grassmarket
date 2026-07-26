"""The shared GTM target & contact registry (GRS-0193, ADR-0045).

Every row in this file is built in code. The imported datasets under `data/gtm/` carry named
individuals' business contact details, and §7 of the ticket keeps that PII out of the test fixtures
entirely — these tests prove the machinery, not the data.
"""

from __future__ import annotations

from datetime import date

import pytest
from bcap_contracts.entities import RegistryContact, RegistryTarget
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from grassmarket.data.repository import NotFoundError, Repository
from grassmarket.entities import StubEntityRegistry, active_entity_registry
from grassmarket.gtm import (
    ImportSummary,
    RowError,
    decode_lseg_rating,
    null_if_unset,
    parse_bank_row,
    parse_barclays_analyst_row,
    parse_barclays_owner_row,
    parse_lseg_roster,
    parse_supplier_row,
)
from tests.conftest import SeededConsultant, auth_header

ON = date(2026, 7, 25)


def _target(target_id: str = "lseg-acme", name: str = "Acme Research", **kw) -> RegistryTarget:
    return RegistryTarget(
        target_id=target_id,
        name=name,
        aliases=kw.pop("aliases", ()),
        domain=kw.pop("domain", "acme.example"),
        segment=kw.pop("segment", "Sell-side research"),
        country=kw.pop("country", None),
        ric=kw.pop("ric", None),
        ctb_id=kw.pop("ctb_id", None),
        source=kw.pop("source", "test"),
        imported_on=kw.pop("imported_on", ON),
    )


def _contact(contact_id: str, target_id: str = "lseg-acme", **kw) -> RegistryContact:
    return RegistryContact(
        contact_id=contact_id,
        target_id=target_id,
        full_name=kw.pop("full_name", "Jo Analyst"),
        email=kw.pop("email", "jo@acme.example"),
        phone=kw.pop("phone", None),
        job_role=kw.pop("job_role", "Equity Analyst"),
        linkedin=kw.pop("linkedin", None),
        verified=kw.pop("verified", False),
        source=kw.pop("source", "test"),
        imported_on=kw.pop("imported_on", ON),
    )


# --------------------------------------------------------------------------------- persistence


def test_upsert_registry_target_is_idempotent(repo: Repository) -> None:
    repo.upsert_registry_target(_target())
    repo.upsert_registry_target(_target(name="Acme Research LLP", segment="Bank"))
    stored = repo.get_registry_target("lseg-acme")
    assert repo.count_registry_targets() == 1
    assert stored is not None
    assert stored.name == "Acme Research LLP"
    assert stored.segment == "Bank"


def test_upsert_registry_contact_is_idempotent(repo: Repository) -> None:
    repo.upsert_registry_target(_target())
    repo.upsert_registry_contact(_contact("lseg-acme:jo"))
    repo.upsert_registry_contact(_contact("lseg-acme:jo", job_role="Head of Research"))
    contacts = repo.list_registry_contacts("lseg-acme")
    assert len(contacts) == 1
    assert contacts[0].job_role == "Head of Research"


def test_a_contact_without_its_institution_is_refused(repo: Repository) -> None:
    # Fail loud (#3): an unattributed person is not importable, rather than being stored orphaned.
    with pytest.raises(NotFoundError):
        repo.upsert_registry_contact(_contact("ghost:1", target_id="never-imported"))


def test_listing_contacts_for_an_unknown_target_fails_loud(repo: Repository) -> None:
    # An empty list would read as "nobody works here", which is a different claim from "we have
    # never imported this institution".
    with pytest.raises(NotFoundError):
        repo.list_registry_contacts("never-imported")


def test_contacts_list_verified_first(repo: Repository) -> None:
    repo.upsert_registry_target(_target())
    repo.upsert_registry_contact(_contact("a", full_name="Zoe Unverified", verified=False))
    repo.upsert_registry_contact(_contact("b", full_name="Adam Verified", verified=True))
    assert [c.full_name for c in repo.list_registry_contacts("lseg-acme")] == [
        "Adam Verified",
        "Zoe Unverified",
    ]


# ------------------------------------------------------------------------------------- ranking


def test_search_reproduces_the_stub_ranking(repo: Repository) -> None:
    """The DB corpus must rank exactly as the in-repo stub does — same function, larger corpus."""
    repo.upsert_registry_target(_target("t-exact", "Meridian"))
    repo.upsert_registry_target(_target("t-prefix", "Meridian Securities"))
    repo.upsert_registry_target(_target("t-alias", "Northbank", aliases=("Meridian",)))
    repo.upsert_registry_target(_target("t-substr", "The Meridian Group"))
    names = [t.name for t in repo.search_registry_targets("meridian", limit=10)]
    assert names == ["Meridian", "Meridian Securities", "Northbank", "The Meridian Group"]


def test_search_matches_the_stub_on_the_same_corpus(repo: Repository) -> None:
    """Cross-check against the stub itself rather than against a hand-written expectation."""
    rows = [
        _target("a", "Barclays"),
        _target("b", "Barclays Investment Bank"),
        _target("c", "Northbank", aliases=("Barclays Live",)),
    ]
    for row in rows:
        repo.upsert_registry_target(row)
    from grassmarket.entities import to_company_entity

    stub = StubEntityRegistry(tuple(to_company_entity(r) for r in rows))
    assert [t.target_id for t in repo.search_registry_targets("barclays", limit=10)] == [
        e.entity_id for e in stub.search("barclays", limit=10)
    ]


def test_search_ignores_a_blank_query(repo: Repository) -> None:
    repo.upsert_registry_target(_target())
    assert repo.search_registry_targets("   ") == []


# ------------------------------------------------------------------- the entity-registry adapter


def test_registry_falls_back_to_the_stub_on_an_empty_table(repo: Repository) -> None:
    # A fresh development database has no import, and must still resolve the seeded demo subjects.
    registry = active_entity_registry(repo)
    assert registry.get("revolut") is not None
    assert [e.entity_id for e in registry.search("revolut")] == ["revolut"]


def test_registry_serves_the_imported_corpus_once_populated(repo: Repository) -> None:
    repo.upsert_registry_target(_target("lseg-jefferies", "Jefferies"))
    registry = active_entity_registry(repo)
    entity = registry.get("lseg-jefferies")
    assert entity is not None
    assert entity.name == "Jefferies"
    assert [e.entity_id for e in registry.search("jefferies")] == ["lseg-jefferies"]


def test_the_demo_subjects_survive_an_import(repo: Repository) -> None:
    """The merge, not a replacement: an import must not orphan every seeded demo assessment."""
    repo.upsert_registry_target(_target("lseg-jefferies", "Jefferies"))
    registry = active_entity_registry(repo)
    for seeded in ("revolut", "interactive-brokers", "meridian-securities"):
        assert registry.get(seeded) is not None, seeded
    assert [e.entity_id for e in registry.search("meridian")] == ["meridian-securities"]


def test_an_imported_row_wins_over_the_seed_on_an_id_collision(repo: Repository) -> None:
    repo.upsert_registry_target(_target("revolut", "Revolut Group Holdings"))
    entity = active_entity_registry(repo).get("revolut")
    assert entity is not None
    assert entity.name == "Revolut Group Holdings"


def test_no_reader_means_the_stub(repo: Repository) -> None:
    repo.upsert_registry_target(_target("lseg-jefferies", "Jefferies"))
    # The no-argument form is the pre-GRS-0193 behaviour and must stay the seeded stub.
    assert active_entity_registry().get("lseg-jefferies") is None


# ------------------------------------------------------------------------------------- scoping


def test_the_registry_is_network_shared(
    client: TestClient, alice: SeededConsultant, bob: SeededConsultant, repo: Repository
) -> None:
    """ADR-0045 §2: the deliberate exception to owner-scoping. Both advisors read the same rows."""
    repo.upsert_registry_target(_target())
    repo.upsert_registry_contact(_contact("lseg-acme:jo"))

    seen = []
    for who in (alice, bob):
        response = client.get("/entities/lseg-acme/contacts", headers=auth_header(who))
        assert response.status_code == 200, response.text
        seen.append([c["contact_id"] for c in response.json()])
    assert seen[0] == seen[1] == ["lseg-acme:jo"]


def test_the_registry_still_requires_authentication(client: TestClient, repo: Repository) -> None:
    repo.upsert_registry_target(_target())
    assert client.get("/entities/lseg-acme/contacts").status_code == 401


def test_prospect_contacts_stay_owner_private(
    client: TestClient, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    """The other half of the split: sharing the registry must not have leaked into the pipeline."""
    created = client.post(
        "/prospects", json={"company_name": "Northbank"}, headers=auth_header(alice)
    )
    assert created.status_code == 201, created.text
    prospect_id = created.json()["id"]
    added = client.post(
        f"/prospects/{prospect_id}/contacts",
        json={"name": "Private Person", "email": "private@northbank.example"},
        headers=auth_header(alice),
    )
    assert added.status_code == 201, added.text
    assert (
        client.get(f"/prospects/{prospect_id}/contacts", headers=auth_header(bob)).status_code
        == 404
    )


def test_unknown_target_contacts_is_404(client: TestClient, alice: SeededConsultant) -> None:
    response = client.get("/entities/never-imported/contacts", headers=auth_header(alice))
    assert response.status_code == 404


# ------------------------------------------------------------------------------- LSEG caveats


def test_null_if_unset_treats_the_lseg_sentinels_as_missing() -> None:
    for token in ("", "  ", "<NA>", "NaT", "nan", "None"):
        assert null_if_unset(token) is None
    assert null_if_unset("Barclays") == "Barclays"
    assert null_if_unset(None) is None


def test_decode_lseg_rating_handles_the_epoch_nanosecond_encoding() -> None:
    # GRS-0200 method fact 3: 1970-01-01 00:00:00.000000054 IS the rating 54.
    assert decode_lseg_rating("1970-01-01 00:00:00.000000054") == 54
    assert decode_lseg_rating("1970-01-01T00:00:00.000000007") == 7
    assert decode_lseg_rating("64") == 64
    assert decode_lseg_rating("<NA>") is None


def test_decode_lseg_rating_refuses_a_value_it_cannot_explain() -> None:
    with pytest.raises(RowError):
        decode_lseg_rating("not-a-rating")
    with pytest.raises(RowError):
        decode_lseg_rating("4200")


def _roster_row(**kw) -> dict[str, object]:
    row = {
        "ric": "AAPL.OQ",
        "analyst_name": "Jo Analyst",
        "email": "jo@acme.example",
        "phone": "212-000-0000",
        "job_role": "Equity Analyst",
        "ctb_id": "9584",
        "uid": "1",
        "create_date": "1995-05-29 00:00:00",
        "est_rating": "52",
        "rec_rating_24m": "64",
    }
    row.update(kw)
    return row


MAP = {9584: {"inferred_domain": "acme.example", "inferred_institution": "acme"}}


def test_lseg_roster_drops_the_anonymous_slots() -> None:
    summary = ImportSummary(source="lseg-roster")
    targets, contacts = parse_lseg_roster(
        [_roster_row(), _roster_row(analyst_name="", ctb_id="", email="")],
        MAP,
        imported_on=ON,
        summary=summary,
    )
    assert len(targets) == 1
    assert [c.full_name for c in contacts] == ["Jo Analyst"]
    assert summary.rows_read == 2
    assert any("anonymous" in reason for reason in summary.skipped)


def test_lseg_roster_dedupes_an_analyst_across_sampled_tickers() -> None:
    _, contacts = parse_lseg_roster([_roster_row(), _roster_row(ric="MSFT.O")], MAP, imported_on=ON)
    assert len(contacts) == 1


def test_lseg_roster_nulls_unset_cells_rather_than_zeroing_them() -> None:
    _, contacts = parse_lseg_roster(
        [_roster_row(email="<NA>", phone="NaT", job_role="")], MAP, imported_on=ON
    )
    assert contacts[0].email is None
    assert contacts[0].phone is None
    assert contacts[0].job_role is None


def test_lseg_roster_never_marks_an_inferred_row_verified() -> None:
    # The institution is inferred from the email domain (method fact 2), so it is not verified.
    _, contacts = parse_lseg_roster([_roster_row()], MAP, imported_on=ON)
    assert contacts[0].verified is False


def test_lseg_roster_refuses_a_named_analyst_with_no_contributor() -> None:
    with pytest.raises(RowError):
        parse_lseg_roster([_roster_row(ctb_id="")], MAP, imported_on=ON)


def test_lseg_roster_records_an_uncurated_contributor_as_skipped() -> None:
    summary = ImportSummary(source="lseg-roster")
    targets, contacts = parse_lseg_roster(
        [_roster_row(ctb_id="99999")], MAP, imported_on=ON, summary=summary
    )
    assert (targets, contacts) == ([], [])
    assert any("99999" in reason for reason in summary.skipped)


def test_lseg_roster_skips_a_contributor_the_map_could_not_name() -> None:
    # Five of the 134 contributors in the first-draft map published no email domain to infer an
    # institution from. That is a gap in the map, not a malformed row: it is counted and skipped,
    # never attributed to a guessed employer, and never fatal to the run.
    summary = ImportSummary(source="lseg-roster")
    targets, contacts = parse_lseg_roster(
        [_roster_row(ctb_id="3202")],
        {3202: {"inferred_domain": "", "inferred_institution": ""}},
        imported_on=ON,
        summary=summary,
    )
    assert (targets, contacts) == ([], [])
    assert any(
        "3202" in reason and "no inferred institution" in reason for reason in summary.skipped
    )


def test_lseg_roster_fails_on_a_malformed_rating() -> None:
    with pytest.raises(RowError):
        parse_lseg_roster([_roster_row(rec_rating_24m="banana")], MAP, imported_on=ON)


# ------------------------------------------------------------------------ the other three shapes


def test_supplier_row_yields_a_target_and_its_audited_contact() -> None:
    target, contacts = parse_supplier_row(
        {
            "Supplier": "4Cast ",
            "Supplier Service": "4Cast News",
            "Content Type": "News",
            "Audit: New URL": "https://www.4castsolutions.co.uk/about",
            "Audit: New Email": "sales@4castsolutions.co.uk",
            "Audit: Contact Name": "Sam Seller",
            "Audit: Contact Title": "Head of Sales",
            "Audit: Contact LinkedIn": "https://linkedin.com/in/samseller",
        },
        imported_on=ON,
    )
    assert target.target_id == "xs-4cast"
    assert target.domain == "4castsolutions.co.uk"
    assert target.segment == "News"
    assert [c.full_name for c in contacts] == ["Sam Seller"]
    assert contacts[0].linkedin == "https://linkedin.com/in/samseller"
    assert contacts[0].verified is False


def test_supplier_row_without_a_contact_yields_no_contact() -> None:
    _, contacts = parse_supplier_row(
        {"Supplier": "ABS Benchmarks", "Content Type": "Fixings"}, imported_on=ON
    )
    assert contacts == []


def test_supplier_row_without_a_name_is_fatal() -> None:
    with pytest.raises(RowError):
        parse_supplier_row({"Supplier": None, "Content Type": "Data"}, imported_on=ON)


def test_bank_row_yields_a_target_with_no_contacts() -> None:
    target = parse_bank_row({"Country": "China", "Company": "Bank of Changsha"}, imported_on=ON)
    assert target.target_id == "bank-bank-of-changsha"
    assert target.segment == "Bank"
    assert target.country == "China"


def test_bank_row_without_a_company_is_fatal() -> None:
    with pytest.raises(RowError):
        parse_bank_row({"Country": "China", "Company": ""}, imported_on=ON)


def test_barclays_analyst_rows_are_never_verified() -> None:
    contact = parse_barclays_analyst_row(
        {
            "Rank": 1,
            "Name": "Kannan Venkateshwar",
            "Title (I/B/E/S)": "Managing Director, Equity Analyst",
            "Email": "kannan.venkateshwar@barclays.example",
            "Phone": "212-000-0000",
        },
        target_id="lseg-barclays",
        imported_on=ON,
    )
    assert contact.verified is False
    assert contact.job_role == "Managing Director, Equity Analyst"


def test_barclays_owner_rows_carry_the_workbook_verification() -> None:
    """The two-source rule: only a cleanly verified ownership row imports as verified."""
    cases = {
        "Verified": True,
        "Verified (appointment Sep 2023; still current per LinkedIn)": True,
        "Partially verified - treat title with caution": False,
        "Unverified - gap": False,
        "": False,
    }
    for verification, expected in cases.items():
        contact = parse_barclays_owner_row(
            {
                "Name": "Some Owner",
                "Title": "Global Head of Research",
                "Verification": verification,
            },
            target_id="lseg-barclays",
            imported_on=ON,
        )
        assert contact.verified is expected, verification


def test_barclays_owner_row_without_a_name_is_fatal() -> None:
    with pytest.raises(RowError):
        parse_barclays_owner_row(
            {"Name": None, "Verification": "Verified"}, target_id="lseg-barclays", imported_on=ON
        )


# ------------------------------------------------------------------------------------- summary


def test_import_summary_reports_what_it_did_and_what_it_skipped() -> None:
    summary = ImportSummary(source="list-of-banks", rows_read=3, targets_upserted=2)
    summary.skip("blank row")
    assert summary.as_dict() == {
        "source": "list-of-banks",
        "rows_read": 3,
        "targets_upserted": 2,
        "contacts_upserted": 0,
        "skipped": ["blank row"],
    }


def test_search_survives_a_session_boundary(session_factory: sessionmaker[Session]) -> None:
    """The rows are really persisted, not just held in one identity map."""
    with session_factory() as session:
        Repository(session).upsert_registry_target(_target("lseg-jefferies", "Jefferies"))
        session.commit()
    with session_factory() as session:
        assert Repository(session).count_registry_targets() == 1
