"""LSEG influencer maps (GRS-0194, ADR-0045).

Every LSEG response here is a fixture built in code, so CI never touches the live connector. The
cells are shaped exactly as it returns them: a flat (ric, field, value) list with no row identity,
which is the whole reason `reconstruct_rows` has to be careful.
"""

from __future__ import annotations

from datetime import date

import pytest
from bcap_contracts.entities import RegistryContact, RegistryTarget
from bcap_contracts.influencer import INFLUENCER_MAP_CAVEAT
from fastapi import FastAPI
from fastapi.testclient import TestClient

from grassmarket.data.repository import Repository
from grassmarket.gtm import (
    LsegCell,
    RowError,
    generate_influencer_map,
    owners_from_registry,
    rank_analysts,
    reconstruct_rows,
)
from grassmarket.web.dependencies import get_lseg_roster_source
from tests.conftest import SeededConsultant, auth_header

ON = date(2026, 7, 25)


class FakeRosterSource:
    """A recording stand-in for the connector: returns fixture cells and remembers the call."""

    connector = "bcap-lseg (test fake)"

    def __init__(self, cells: list[LsegCell]) -> None:
        self._cells = cells
        self.calls: list[tuple[tuple[str, ...], tuple[str, ...]]] = []

    def fetch_cells(self, rics, fields) -> list[LsegCell]:
        self.calls.append((tuple(rics), tuple(fields)))
        return list(self._cells)


def _cells(ric: str, analysts: list[dict[str, str | None]]) -> list[LsegCell]:
    """Flatten analyst dicts into the connector's cell shape: one field at a time, in analyst
    order, with no row identity of its own."""
    field_for = {
        "analyst_name": "TR.AnalystName",
        "email": "TR.AnalystEmail",
        "phone": "TR.AnalystPhone",
        "job_role": "TR.AnalystJobRole",
        "ctb_id": "TR.AnalystCtbID",
        "create_date": "TR.AnalystCreateDate",
        "est_rating": "TR.OverallAnalystEstimateRating",
        "rec_rating_24m": "TR.OverallAnalystRecommendationRatingT24M",
    }
    out: list[LsegCell] = []
    for key, field in field_for.items():
        for analyst in analysts:
            out.append(LsegCell(ric=ric, field=field, value=analyst.get(key)))
    return out


def _analyst(name: str, **kw) -> dict[str, str | None]:
    row: dict[str, str | None] = {
        "analyst_name": name,
        "email": f"{name.split()[0].lower()}@barclays.example",
        "phone": "212-000-0000",
        "job_role": "Equity Analyst",
        "ctb_id": "10333",
        "create_date": "2015-01-01 00:00:00",
        "est_rating": "50",
        "rec_rating_24m": "50",
    }
    row.update(kw)
    return row


# ------------------------------------------------------------------------------- cell parsing


def test_rows_are_rebuilt_by_zipping_the_flat_cells() -> None:
    rows = reconstruct_rows(_cells("AAPL.OQ", [_analyst("Ann One"), _analyst("Bob Two")]))
    assert [r["analyst_name"] for r in rows] == ["Ann One", "Bob Two"]
    assert rows[0]["email"] == "ann@barclays.example"
    assert rows[1]["email"] == "bob@barclays.example"
    assert all(r["ric"] == "AAPL.OQ" for r in rows)


def test_unset_cells_become_null_not_zero() -> None:
    rows = reconstruct_rows(
        _cells("AAPL.OQ", [_analyst("Ann One", email="<NA>", phone="NaT", est_rating="")])
    )
    assert rows[0]["email"] is None
    assert rows[0]["phone"] is None
    assert rows[0]["est_rating"] is None


def test_uneven_field_counts_fail_loud_rather_than_padding() -> None:
    # The index-wise zip is the ONLY thing tying a name to an email. Padding a short field would
    # produce plausible, wrong people, which is worse than refusing the pull.
    cells = _cells("AAPL.OQ", [_analyst("Ann One"), _analyst("Bob Two")])
    cells = [
        c for c in cells if not (c.field == "TR.AnalystEmail" and c.value and "bob" in c.value)
    ]
    with pytest.raises(RowError, match="uneven field counts"):
        reconstruct_rows(cells)


def test_rows_from_several_rics_are_kept_apart() -> None:
    rows = reconstruct_rows(
        _cells("AAPL.OQ", [_analyst("Ann One")]) + _cells("MSFT.O", [_analyst("Bob Two")])
    )
    assert {r["ric"] for r in rows} == {"AAPL.OQ", "MSFT.O"}
    assert len(rows) == 2


def test_no_cells_yields_no_rows() -> None:
    assert reconstruct_rows([]) == []


# ---------------------------------------------------------------------- contributor filtering


def test_only_the_named_contributors_analysts_are_ranked() -> None:
    rows = reconstruct_rows(_cells("AAPL.OQ", [_analyst("Ours"), _analyst("Theirs", ctb_id="6")]))
    assert [r.full_name for r in rank_analysts(rows, ctb_id=10333)] == ["Ours"]


def test_anonymous_slots_are_never_ranked() -> None:
    # The 311 anonymous contributor slots: populated ratings, blank identity.
    anonymous = {**_analyst("Placeholder"), "analyst_name": None, "email": None, "phone": None}
    rows = reconstruct_rows(_cells("AAPL.OQ", [_analyst("Ours"), anonymous]))
    assert [r.full_name for r in rank_analysts(rows, ctb_id=10333)] == ["Ours"]


def test_an_analyst_seen_on_several_tickers_is_one_row_with_all_of_them() -> None:
    rows = reconstruct_rows(
        _cells("AAPL.OQ", [_analyst("Ann One")]) + _cells("MSFT.O", [_analyst("Ann One")])
    )
    ranked = rank_analysts(rows, ctb_id=10333)
    assert len(ranked) == 1
    assert ranked[0].covered_rics == ("AAPL.OQ", "MSFT.O")


# ------------------------------------------------------------------------------------ ranking


def test_coverage_breadth_leads_the_ranking() -> None:
    rows = reconstruct_rows(
        _cells("AAPL.OQ", [_analyst("Wide One"), _analyst("Narrow One", est_rating="99")])
        + _cells("MSFT.O", [_analyst("Wide One")])
        + _cells("NVDA.O", [_analyst("Wide One")])
    )
    ranked = rank_analysts(rows, ctb_id=10333)
    # Wide One leads despite the far weaker rating: breadth outranks rating across tiers.
    assert [r.full_name for r in ranked] == ["Wide One", "Narrow One"]
    assert [r.rank for r in ranked] == [1, 2]


def test_ratings_break_a_coverage_tie() -> None:
    rows = reconstruct_rows(
        _cells("AAPL.OQ", [_analyst("Lower", est_rating="20"), _analyst("Higher", est_rating="80")])
    )
    assert [r.full_name for r in rank_analysts(rows, ctb_id=10333)] == ["Higher", "Lower"]


def test_tenure_breaks_a_rating_tie() -> None:
    rows = reconstruct_rows(
        _cells(
            "AAPL.OQ",
            [
                _analyst("Newer", create_date="2022-01-01 00:00:00"),
                _analyst("Longer", create_date="1999-01-01 00:00:00"),
            ],
        )
    )
    assert [r.full_name for r in rank_analysts(rows, ctb_id=10333)] == ["Longer", "Newer"]


def test_an_unrated_analyst_sorts_last_rather_than_as_a_zero() -> None:
    rows = reconstruct_rows(
        _cells(
            "AAPL.OQ",
            [
                _analyst("Unrated", est_rating="<NA>", rec_rating_24m="<NA>"),
                _analyst("Rated", est_rating="10"),
            ],
        )
    )
    ranked = rank_analysts(rows, ctb_id=10333)
    # A rating of 10 still beats no rating: "unrated" is not "rated zero".
    assert [r.full_name for r in ranked] == ["Rated", "Unrated"]
    assert ranked[1].estimate_rating is None


def test_ranking_is_deterministic_on_a_complete_tie() -> None:
    rows = reconstruct_rows(_cells("AAPL.OQ", [_analyst("Zoe Last"), _analyst("Ann First")]))
    assert [r.full_name for r in rank_analysts(rows, ctb_id=10333)] == ["Ann First", "Zoe Last"]


def test_the_epoch_encoded_rating_is_decoded_before_ranking() -> None:
    rows = reconstruct_rows(
        _cells(
            "AAPL.OQ",
            [
                _analyst("Strong", est_rating="1970-01-01 00:00:00.000000090"),
                _analyst("Weak", est_rating="1970-01-01 00:00:00.000000010"),
            ],
        )
    )
    ranked = rank_analysts(rows, ctb_id=10333)
    assert [r.full_name for r in ranked] == ["Strong", "Weak"]
    assert ranked[0].estimate_rating == 90


def test_an_lseg_derived_analyst_is_never_verified() -> None:
    rows = reconstruct_rows(_cells("AAPL.OQ", [_analyst("Ann One")]))
    assert all(r.verified is False for r in rank_analysts(rows, ctb_id=10333))


# ------------------------------------------------------------------- the two-source owner layer


def _contact(name: str, *, source: str, verified: bool) -> RegistryContact:
    return RegistryContact(
        contact_id=f"lseg-barclays:{name.lower().replace(' ', '-')}",
        target_id="lseg-barclays",
        full_name=name,
        job_role="Global Head of Research",
        verified=verified,
        source=source,
        imported_on=ON,
    )


def test_owners_exclude_the_lseg_layer() -> None:
    """The two-source split: analysts come from the pull, owners from human research."""
    owners = owners_from_registry(
        [
            _contact("Analyst Person", source="lseg-roster", verified=False),
            _contact("Owner Person", source="barclays-influencer-map", verified=True),
        ]
    )
    assert [o.full_name for o in owners] == ["Owner Person"]


def test_unverified_owners_render_flagged_and_sort_after_verified_ones() -> None:
    owners = owners_from_registry(
        [
            _contact("Aaron Unverified", source="barclays-influencer-map", verified=False),
            _contact("Zoe Verified", source="barclays-influencer-map", verified=True),
        ]
    )
    assert [(o.full_name, o.verified) for o in owners] == [
        ("Zoe Verified", True),
        ("Aaron Unverified", False),
    ]


# ----------------------------------------------------------------------------- the whole map


def _target(**kw) -> RegistryTarget:
    return RegistryTarget(
        target_id="lseg-barclays",
        name="Barclays",
        segment="Sell-side research",
        ctb_id=kw.pop("ctb_id", 10333),
        source="barclays-influencer-map",
        imported_on=ON,
        **kw,
    )


def test_the_generated_map_carries_provenance_rankings_caveat_and_flags() -> None:
    source = FakeRosterSource(
        _cells("AAPL.OQ", [_analyst("Ann One"), _analyst("Other House", ctb_id="6")])
    )
    generated = generate_influencer_map(
        _target(),
        [_contact("Owner Person", source="barclays-influencer-map", verified=True)],
        source,
        sample_rics=["AAPL.OQ", "MSFT.O"],
        generated_on=ON,
    )
    assert generated.target_name == "Barclays"
    assert [i.full_name for i in generated.influencers] == ["Ann One"]
    assert [o.full_name for o in generated.owners] == ["Owner Person"]
    assert generated.caveat == INFLUENCER_MAP_CAVEAT
    assert "warm referral" in generated.caveat
    prov = generated.provenance
    assert prov.ctb_id == 10333
    assert prov.sample_rics == ("AAPL.OQ", "MSFT.O")
    assert prov.connector == "bcap-lseg (test fake)"
    assert prov.rows_returned == 2
    assert prov.rows_for_contributor == 1
    # The raw rows are retained so a reader who disputes the ranking can see its inputs, and they
    # hold only this contributor's analysts.
    assert len(generated.raw_rows) == 1


def test_the_pull_asks_for_the_verified_roster_fields() -> None:
    source = FakeRosterSource(_cells("AAPL.OQ", [_analyst("Ann One")]))
    generate_influencer_map(_target(), [], source, sample_rics=["AAPL.OQ"], generated_on=ON)
    rics, fields = source.calls[0]
    assert rics == ("AAPL.OQ",)
    assert "TR.AnalystCtbID" in fields
    assert "TR.OverallAnalystRecommendationRatingT24M" in fields


def test_a_target_without_a_contributor_id_is_refused() -> None:
    # Generating from every contributor's analysts would be a confidently wrong map.
    source = FakeRosterSource([])
    with pytest.raises(RowError, match="no curated LSEG contributor id"):
        generate_influencer_map(
            _target(ctb_id=None), [], source, sample_rics=["AAPL.OQ"], generated_on=ON
        )


def test_an_empty_ticker_sample_is_refused() -> None:
    source = FakeRosterSource([])
    with pytest.raises(RowError, match="at least one sampled ticker"):
        generate_influencer_map(_target(), [], source, sample_rics=[], generated_on=ON)


# ------------------------------------------------------------------------------------ the route


def _install_source(app: FastAPI, source: FakeRosterSource) -> None:
    app.dependency_overrides[get_lseg_roster_source] = lambda: source


def _seed_target(repo: Repository) -> None:
    repo.upsert_registry_target(_target())
    repo.upsert_registry_contact(
        _contact("Owner Person", source="barclays-influencer-map", verified=True)
    )


def test_an_admin_can_generate_a_map(
    app: FastAPI, client: TestClient, admin: SeededConsultant, repo: Repository
) -> None:
    _seed_target(repo)
    _install_source(app, FakeRosterSource(_cells("AAPL.OQ", [_analyst("Ann One")])))
    response = client.post(
        "/entities/lseg-barclays/influencer-map",
        json={"sample_rics": ["AAPL.OQ"]},
        headers=auth_header(admin),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert [i["full_name"] for i in body["influencers"]] == ["Ann One"]
    assert body["provenance"]["ctb_id"] == 10333
    assert body["caveat"] == INFLUENCER_MAP_CAVEAT


def test_a_non_admin_cannot_trigger_a_pull(
    app: FastAPI, client: TestClient, alice: SeededConsultant, repo: Repository
) -> None:
    """A live vendor pull is an operator action, never something one advisor can start."""
    _seed_target(repo)
    _install_source(app, FakeRosterSource(_cells("AAPL.OQ", [_analyst("Ann One")])))
    response = client.post(
        "/entities/lseg-barclays/influencer-map",
        json={"sample_rics": ["AAPL.OQ"]},
        headers=auth_header(alice),
    )
    assert response.status_code == 403


def test_generating_a_map_needs_authentication(
    app: FastAPI, client: TestClient, repo: Repository
) -> None:
    _seed_target(repo)
    _install_source(app, FakeRosterSource([]))
    assert (
        client.post(
            "/entities/lseg-barclays/influencer-map", json={"sample_rics": ["AAPL.OQ"]}
        ).status_code
        == 401
    )


def test_an_unknown_target_is_404(
    app: FastAPI, client: TestClient, admin: SeededConsultant
) -> None:
    _install_source(app, FakeRosterSource([]))
    response = client.post(
        "/entities/never-imported/influencer-map",
        json={"sample_rics": ["AAPL.OQ"]},
        headers=auth_header(admin),
    )
    assert response.status_code == 404


def test_a_target_with_no_contributor_id_is_422_with_the_reason(
    app: FastAPI, client: TestClient, admin: SeededConsultant, repo: Repository
) -> None:
    repo.upsert_registry_target(_target(ctb_id=None))
    _install_source(app, FakeRosterSource([]))
    response = client.post(
        "/entities/lseg-barclays/influencer-map",
        json={"sample_rics": ["AAPL.OQ"]},
        headers=auth_header(admin),
    )
    assert response.status_code == 422
    assert "contributor id" in response.json()["detail"]


def test_an_empty_sample_is_rejected_by_the_contract(
    app: FastAPI, client: TestClient, admin: SeededConsultant, repo: Repository
) -> None:
    _seed_target(repo)
    _install_source(app, FakeRosterSource([]))
    response = client.post(
        "/entities/lseg-barclays/influencer-map",
        json={"sample_rics": []},
        headers=auth_header(admin),
    )
    assert response.status_code == 422


def test_an_unconfigured_deployment_refuses_the_pull_loudly(
    client: TestClient, admin: SeededConsultant, repo: Repository
) -> None:
    """With no connector wired, the route 503s rather than returning an empty map, which would
    read as the false claim that this bank has no analysts."""
    _seed_target(repo)
    response = client.post(
        "/entities/lseg-barclays/influencer-map",
        json={"sample_rics": ["AAPL.OQ"]},
        headers=auth_header(admin),
    )
    assert response.status_code == 503
    assert "No LSEG connector is configured" in response.json()["detail"]
