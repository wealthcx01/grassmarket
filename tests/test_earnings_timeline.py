"""Earnings timeline tests (GRS-0133) — the incentive chart's data.

Pins that the timeline is aggregated server-side from the computed commission lines (ADR-0002):
cumulative-over-time is monotonic, buckets by calendar month, and splits the two v7 streams. No rate
or lifecycle logic here — it only sums figures the Earnings v7 kernel already computed.
"""

from __future__ import annotations

from uuid import uuid4

from tests.conftest import SeededConsultant, auth_header


def _consultancy(advisor_id: str, *, minor: int, earned_on: str) -> dict:
    return {
        "advisor_id": advisor_id,
        "engagement_id": str(uuid4()),
        "base_value_minor": minor,
        "currency": "GBP",
        "base_value_ref": "contract:acme-2026",
        "sourcing": "firm_sourced",
        "delivery_type": "bruntsfield_led",
        "contract_year": 1,
        "earned_on": earned_on,
    }


def _product(advisor_id: str, *, minor: int, earned_on: str) -> dict:
    return {
        "advisor_id": advisor_id,
        "engagement_id": str(uuid4()),
        "base_value_minor": minor,
        "currency": "GBP",
        "base_value_ref": "deal:openbb-2026",
        "product_id": "openbb",
        "contract_year": 1,
        "earned_on": earned_on,
    }


def test_empty_timeline(client, alice: SeededConsultant) -> None:
    tl = client.get("/earnings/timeline", headers=auth_header(alice)).json()
    assert tl["points"] == []
    assert tl["stream_product"]["amount_minor"] == 0
    assert tl["stream_consultancy"]["amount_minor"] == 0
    assert tl["owner_consultant_id"] == str(alice.stored.id)


def test_timeline_buckets_by_month_and_is_cumulative(
    client, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    aid = str(alice.stored.id)
    # Two consultancy deals (Stream B), different months; one product deal (Stream A).
    client.post(
        "/earnings/commissions/consultancy",
        json=_consultancy(aid, minor=40_000_00, earned_on="2026-03-01"),
        headers=auth_header(admin),
    )
    client.post(
        "/earnings/commissions/consultancy",
        json=_consultancy(aid, minor=20_000_00, earned_on="2026-05-10"),
        headers=auth_header(admin),
    )
    client.post(
        "/earnings/commissions/product",
        json=_product(aid, minor=100_000_00, earned_on="2026-03-20"),
        headers=auth_header(admin),
    )

    tl = client.get("/earnings/timeline", headers=auth_header(alice)).json()
    periods = [p["period"] for p in tl["points"]]
    assert periods == ["2026-03", "2026-05"]  # sorted, one bucket per active month

    # Cumulative is monotonic non-decreasing and its last value equals total earned.
    cumulatives = [p["cumulative"]["amount_minor"] for p in tl["points"]]
    assert cumulatives == sorted(cumulatives)
    total = sum(p["earned"]["amount_minor"] for p in tl["points"])
    assert cumulatives[-1] == total

    # The two v7 streams are split; product (Stream A) and consultancy (Stream B) both non-zero.
    assert tl["stream_product"]["amount_minor"] > 0
    assert tl["stream_consultancy"]["amount_minor"] > 0
    assert tl["stream_product"]["amount_minor"] + tl["stream_consultancy"]["amount_minor"] == total


def test_timeline_is_self_scoped(
    client, admin: SeededConsultant, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    client.post(
        "/earnings/commissions/consultancy",
        json=_consultancy(str(alice.stored.id), minor=40_000_00, earned_on="2026-03-01"),
        headers=auth_header(admin),
    )
    # Bob sees only his own timeline — Alice's line does not appear.
    bob_tl = client.get("/earnings/timeline", headers=auth_header(bob)).json()
    assert bob_tl["points"] == []
