"""The Prospecting surface (GRS-0238).

The load-bearing test in this file is `TestScoping`. Two different scoping rules meet in
`list_registry_targets` and getting either wrong is a real failure in opposite directions:

- the **targets** are network-shared reference data (ADR-0045 §2), so an owner filter would hide the
  imported universe from everyone but its importer;
- the **`already_in_my_pipeline` flag** is owner-scoped (#9), so a missing principal filter would
  leak the shape of another advisor's book — which firms they are working.

Everything else here is about not lying to an advisor about data quality: the segment column mixes
firm types with supplier content types, and 128 institutions are named after a domain stem.
"""

from __future__ import annotations

from datetime import date

import pytest
from bcap_contracts.entities import RegistryContact, RegistryTarget
from bcap_contracts.prospecting import (
    SEGMENT_LABELS,
    SegmentKind,
    looks_like_a_domain_stem,
    segment_label,
)

from grassmarket.data.repository import Repository

ON = date(2026, 8, 19)


def _target(target_id: str, name: str, **kw) -> RegistryTarget:
    return RegistryTarget(
        target_id=target_id,
        name=name,
        source=kw.pop("source", "list-of-banks"),
        imported_on=ON,
        **kw,
    )


@pytest.fixture
def registry(repo: Repository, alice, bob) -> Repository:
    repo.upsert_registry_target(_target("bank-barclays", "Barclays", segment="Bank", country="UK"))
    repo.upsert_registry_target(
        _target("bank-natwest", "NatWest", segment="Bank", country="UK", domain="natwest.com")
    )
    repo.upsert_registry_target(
        _target("xs-refinitiv", "Refinitiv", segment="Data", country="US", source="exchange-list")
    )
    # A roster row named by a domain stem — the measured shape of 128 real rows.
    repo.upsert_registry_target(
        _target("lseg-gs", "gs", segment="Sell-side research", source="lseg-roster")
    )
    repo.upsert_registry_contact(
        RegistryContact(
            contact_id="bank-barclays:jo",
            target_id="bank-barclays",
            full_name="Jo Analyst",
            source="list-of-banks",
            imported_on=ON,
        )
    )
    return repo


class TestScoping:
    """The two rules that meet here, asserted in both directions."""

    def test_the_registry_itself_is_network_shared(self, registry: Repository, alice, bob) -> None:
        """A second advisor who imported nothing still sees the whole universe.

        If this ever fails, the registry has been owner-scoped by mistake and the Prospecting page
        is empty for everyone but whoever ran the import.
        """
        mine = registry.list_registry_targets(alice.principal)
        theirs = registry.list_registry_targets(bob.principal)
        assert mine.total == theirs.total == 4
        assert [t.target_id for t in mine.targets] == [t.target_id for t in theirs.targets]

    def test_the_pipeline_flag_is_per_principal(self, registry: Repository, alice, bob) -> None:
        """The half that MUST NOT be shared: which firms an advisor is working is their business."""
        registry.create_prospect(alice.principal, company_name="Barclays")
        mine = {
            t.target_id: t.already_in_my_pipeline
            for t in registry.list_registry_targets(alice.principal).targets
        }
        theirs = {
            t.target_id: t.already_in_my_pipeline
            for t in registry.list_registry_targets(bob.principal).targets
        }
        assert mine["bank-barclays"] is True
        # The other advisor must not learn that anybody claimed Barclays.
        assert theirs["bank-barclays"] is False
        assert not any(theirs.values())


class TestFilteringAndPaging:
    def test_filters_by_segment_and_country(self, registry: Repository, alice) -> None:
        banks = registry.list_registry_targets(alice.principal, segment="Bank")
        assert {t.name for t in banks.targets} == {"Barclays", "NatWest"}
        us = registry.list_registry_targets(alice.principal, country="US")
        assert [t.name for t in us.targets] == ["Refinitiv"]

    def test_search_is_a_substring_match_on_name(self, registry: Repository, alice) -> None:
        assert [
            t.name for t in registry.list_registry_targets(alice.principal, q="wes").targets
        ] == ["NatWest"]

    def test_total_counts_the_filtered_set_not_the_page(self, registry: Repository, alice) -> None:
        """A pager reporting the page size as the total tells an advisor the universe is tiny."""
        page = registry.list_registry_targets(alice.principal, limit=1)
        assert len(page.targets) == 1
        assert page.total == 4

    def test_paging_walks_the_whole_set_without_repeating(
        self, registry: Repository, alice
    ) -> None:
        seen: list[str] = []
        for offset in range(0, 4, 2):
            seen += [
                t.target_id
                for t in registry.list_registry_targets(
                    alice.principal, offset=offset, limit=2
                ).targets
            ]
        assert len(seen) == len(set(seen)) == 4

    def test_contact_counts_are_joined(self, registry: Repository, alice) -> None:
        counts = {
            t.target_id: t.contact_count
            for t in registry.list_registry_targets(alice.principal).targets
        }
        assert counts["bank-barclays"] == 1
        assert counts["bank-natwest"] == 0


class TestFacets:
    def test_segments_come_from_the_data(self, registry: Repository) -> None:
        """Built from rows, not from the label map — a new source must appear, not vanish."""
        assert dict(registry.registry_segments()) == {"Bank": 2, "Data": 1, "Sell-side research": 1}

    def test_countries_come_from_the_data(self, registry: Repository) -> None:
        assert dict(registry.registry_countries()) == {"UK": 2, "US": 1}


class TestHonestLabels:
    """Scope 3. The measured problem is that one column holds two different kinds of thing."""

    def test_firm_types_and_content_types_are_distinguished(self) -> None:
        assert segment_label("Bank")[1] is SegmentKind.FIRM_TYPE
        assert segment_label("Indices")[1] is SegmentKind.CONTENT_TYPE
        # A supplier's content type must never read as a sector.
        assert segment_label("Indices")[0].startswith("Supplies:")

    def test_an_unmapped_value_is_shown_verbatim_not_prettified(self) -> None:
        """The ugliness is the signal that a source arrived without anyone labelling its vocabulary.

        Title-casing it would produce something that reads curated and is not.
        """
        label, kind = segment_label("Some New Vendor Category")
        assert label == "Some New Vendor Category"
        assert kind is SegmentKind.UNKNOWN

    def test_a_missing_segment_is_named_rather_than_blank(self) -> None:
        assert segment_label(None) == ("Unclassified", SegmentKind.UNKNOWN)

    @pytest.mark.parametrize("value", sorted(SEGMENT_LABELS))
    def test_every_curated_label_is_readable(self, value: str) -> None:
        label, kind = segment_label(value)
        assert kind is not SegmentKind.UNKNOWN
        assert label and label[0].isupper()


class TestUnverifiedNames:
    """The finding the ticket did not anticipate: 128 institutions are named by a domain stem."""

    def test_a_domain_stem_is_marked(self, registry: Repository, alice) -> None:
        rows = {t.target_id: t for t in registry.list_registry_targets(alice.principal).targets}
        assert rows["lseg-gs"].name_unverified is True
        assert rows["bank-barclays"].name_unverified is False

    def test_the_stem_is_marked_but_never_replaced(self, registry: Repository, alice) -> None:
        """`gs` must not become "Goldman Sachs" anywhere in this path.

        Deriving a company name from a domain stem is a guess, and a guess written into a field a
        client-facing pipeline reads is indistinguishable from a fact afterwards (#3).
        """
        row = next(
            t
            for t in registry.list_registry_targets(alice.principal).targets
            if t.target_id == "lseg-gs"
        )
        assert row.name == "gs"

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("gs", True),
            ("jpmorgan", True),
            ("uk", True),
            ("Barclays", False),
            ("Hargreaves Lansdown", False),
            # Two lower-case words is a name someone typed, not a domain stem.
            ("stock exchange", False),
        ],
    )
    def test_stem_detection(self, name: str, expected: bool) -> None:
        assert looks_like_a_domain_stem(name) is expected
