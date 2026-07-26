"""Golden-master + property tests for the earnings engine (GRS-0028).

Commission is a basis-point rate (from config) applied to a contract value; the hand-computed
figures are pinned exactly, the config completeness fails loud, and the recovery-fee attribution
window edges (day 364 / 365 / 366) are nailed down. Pure functions — no DB.
"""

from __future__ import annotations

from datetime import date

import pytest
from bcap_contracts.commissions import (
    CommissionConfig,
    CommissionConfigError,
    CommissionKind,
    CommissionStream,
    ConsultancyRate,
    DeliveryType,
    ProductRate,
    SourcingAttribution,
    load_commission_config,
)
from bcap_contracts.common import ConsultantTier
from bcap_contracts.money import Currency, Money

from grassmarket.earnings.commission import (
    commission_content_hash,
    compute_consultancy_commission,
    compute_product_commission,
)
from grassmarket.pipeline.fees import is_within_attribution_window
from tests.conftest import SeededConsultant, auth_header


def _gbp(minor: int, ref: str = "contract:test") -> Money:
    return Money(amount_minor=minor, currency=Currency.GBP, assumption_register_ref=ref)


# --- Commission golden master (hand-computed against commissions.yaml) --------------------


# Stream A — product commission (hand-computed vs commissions.yaml, £100,000 = 10_000_000 minor)
@pytest.mark.parametrize(
    ("product_id", "contract_year", "expected_minor"),
    [
        ("openbb", 1, 1_500_000),  # yr1 15%
        ("openbb", 2, 1_000_000),  # yr2 10%
        ("openbb", 3, 0),  # Yr3+ / past window → £0
        ("brandfetch_distribution", 1, 750_000),  # 7.5%
        ("brandfetch_distribution", 2, 500_000),  # 5%
        ("brandfetch_redistribution", 1, 375_000),  # 3.75%
        ("brandfetch_redistribution", 2, 375_000),  # 3.75% (flat)
    ],
)
def test_product_commission_golden(product_id, contract_year, expected_minor) -> None:
    config = load_commission_config()
    got = compute_product_commission(_gbp(10_000_000), product_id, contract_year, config)
    assert got.amount_minor == expected_minor
    assert got.assumption_register_ref == config.product_rate_ref(product_id, contract_year)


def test_product_commission_unknown_product_refuses() -> None:
    with pytest.raises(CommissionConfigError, match="No Stream-A product"):
        compute_product_commission(_gbp(100), "nope", 1, load_commission_config())


# Stream B — consultancy commission: all four cells × both periods.
@pytest.mark.parametrize(
    ("sourcing", "delivery", "year", "expected_minor"),
    [
        (SourcingAttribution.SELF_SOURCED, DeliveryType.BRUNTSFIELD_LED, 1, 3_000_000),  # 30%
        (SourcingAttribution.SELF_SOURCED, DeliveryType.BRUNTSFIELD_LED, 2, 2_500_000),  # 25%
        (SourcingAttribution.FIRM_SOURCED, DeliveryType.BRUNTSFIELD_LED, 1, 1_500_000),  # 15%
        (SourcingAttribution.FIRM_SOURCED, DeliveryType.BRUNTSFIELD_LED, 2, 1_000_000),  # 10%
        (SourcingAttribution.SELF_SOURCED, DeliveryType.CONSULTANT_LED, 1, 6_500_000),  # 65%
        (SourcingAttribution.SELF_SOURCED, DeliveryType.CONSULTANT_LED, 2, 5_500_000),  # 55%
        (SourcingAttribution.FIRM_SOURCED, DeliveryType.CONSULTANT_LED, 1, 4_500_000),  # 45%
        (SourcingAttribution.FIRM_SOURCED, DeliveryType.CONSULTANT_LED, 2, 3_500_000),  # 35%
    ],
)
def test_consultancy_commission_golden(sourcing, delivery, year, expected_minor) -> None:
    config = load_commission_config()
    got = compute_consultancy_commission(_gbp(10_000_000), sourcing, delivery, year, config)
    assert got.amount_minor == expected_minor


def test_commission_rounding_is_deterministic_half_to_even() -> None:
    config = load_commission_config()
    # brandfetch_redistribution = 375 bps. 40 minor × 0.0375 = 1.5 → 2 (round-half-to-even, odd→up).
    assert (
        compute_product_commission(_gbp(40), "brandfetch_redistribution", 1, config).amount_minor
        == 2
    )
    # 120 minor × 0.0375 = 4.5 → 4 (nearest even, even stays).
    assert (
        compute_product_commission(_gbp(120), "brandfetch_redistribution", 1, config).amount_minor
        == 4
    )


def test_commission_refuses_cross_currency() -> None:
    config = load_commission_config()  # GBP
    usd = Money(amount_minor=1000, currency=Currency.USD, assumption_register_ref="x")
    with pytest.raises(ValueError, match="no silent FX"):
        compute_product_commission(usd, "openbb", 1, config)


def test_commission_refuses_negative_value() -> None:
    config = load_commission_config()
    with pytest.raises(ValueError, match="negative"):
        compute_product_commission(_gbp(-1), "openbb", 1, config)


# --- Config completeness fails loud ------------------------------------------------------


def _v7_kwargs() -> dict:
    """A complete, valid v7 config (both streams) — tests mutate a copy to prove fail-loud."""
    return dict(
        version="test-v7",
        currency=Currency.GBP,
        products={
            "openbb": ProductRate(
                name="OpenBB", yr1_bps=1500, yr2_bps=1000, window_months=24
            )
        },
        consultancy={
            DeliveryType.BRUNTSFIELD_LED: {
                SourcingAttribution.SELF_SOURCED: ConsultancyRate(
                    yr1_bps=3000, thereafter_bps=2500
                ),
                SourcingAttribution.FIRM_SOURCED: ConsultancyRate(
                    yr1_bps=1500, thereafter_bps=1000
                ),
            },
            DeliveryType.CONSULTANT_LED: {
                SourcingAttribution.SELF_SOURCED: ConsultancyRate(
                    yr1_bps=6500, thereafter_bps=5500
                ),
                SourcingAttribution.FIRM_SOURCED: ConsultancyRate(
                    yr1_bps=4500, thereafter_bps=3500
                ),
            },
        },
    )


def test_v7_config_with_no_products_refuses() -> None:
    kwargs = _v7_kwargs()
    kwargs["products"] = {}
    with pytest.raises(CommissionConfigError, match="no products"):
        CommissionConfig(**kwargs)


def test_v7_config_missing_a_stream_b_cell_refuses() -> None:
    kwargs = _v7_kwargs()
    # Drop the firm_sourced cell from consultant_led → completeness must refuse.
    kwargs["consultancy"] = {
        **kwargs["consultancy"],
        DeliveryType.CONSULTANT_LED: {
            SourcingAttribution.SELF_SOURCED: ConsultancyRate(yr1_bps=6500, thereafter_bps=5500),
        },
    }
    with pytest.raises(CommissionConfigError, match="missing sourcing"):
        CommissionConfig(**kwargs)


def test_v7_product_lookup_refuses_unknown() -> None:
    config = CommissionConfig(**_v7_kwargs())
    with pytest.raises(CommissionConfigError, match="No Stream-A product"):
        config.require_product("nonexistent")
    # A known product resolves a validated ProductRef.
    assert config.product_ref("openbb").name == "OpenBB"


# --- Immutability seal -------------------------------------------------------------------


def _hash(**over) -> str:
    base = dict(
        owner_consultant_id=__import__("uuid").UUID(int=1),
        engagement_id=__import__("uuid").UUID(int=2),
        kind=CommissionKind.ENGAGEMENT,
        amount=_gbp(1000, "commissions-v1:consultant:self_sourced"),
        earned_on=date(2026, 7, 14),
        tier=ConsultantTier.CONSULTANT,
        attribution=SourcingAttribution.SELF_SOURCED,
        rate_ref="commissions-v1:consultant:self_sourced",
        base_value=_gbp(4000),
        source_attribution_id=None,
    )
    base.update(over)
    return commission_content_hash(**base)


def test_seal_excludes_payment_status_but_pins_the_amount() -> None:
    # payment_status is not a hash input (it is the mutable lifecycle), so the seal is stable across
    # status changes…
    assert _hash() == _hash()  # deterministic
    # …but any change to the FINANCIAL figures changes the seal.
    assert _hash() != _hash(amount=_gbp(1001, "commissions-v1:consultant:self_sourced"))
    assert _hash() != _hash(base_value=_gbp(4001))


def test_seal_pins_the_v7_provenance_fields() -> None:
    # Each of the four sealed v7 fields changes the hash; a legacy (all-None) line is stable.
    assert _hash() == _hash(stream=None, product_id=None)  # defaults are the legacy shape
    assert _hash() != _hash(stream=CommissionStream.PRODUCT)
    assert _hash() != _hash(product_id="openbb")
    assert _hash() != _hash(delivery_type=DeliveryType.BRUNTSFIELD_LED)
    assert _hash() != _hash(contract_year=2)
    assert _hash() != _hash(window_end=date(2028, 7, 14))


# --- Recovery-fee attribution window edges (GRS-0012 fn, pinned here per the ticket) ------


def test_recovery_window_boundaries() -> None:
    delivered = date(2026, 1, 1)
    window = 365
    # Day 364 after delivery — eligible.
    assert is_within_attribution_window(delivered, date(2026, 12, 31), window) is True
    # Exactly day 365 — the inclusive boundary — eligible.
    assert is_within_attribution_window(delivered, date(2027, 1, 1), window) is True
    # Day 366 — one past the window — NOT eligible.
    assert is_within_attribution_window(delivered, date(2027, 1, 2), window) is False
    # Contracting before delivery is never eligible.
    assert is_within_attribution_window(delivered, date(2025, 12, 31), window) is False
    # Same day (day 0) is eligible.
    assert is_within_attribution_window(delivered, delivered, window) is True


# --- Stream-B rate card (GRS-0187) --------------------------------------------------------


def test_consultancy_commissions_endpoint_lists_the_matrix(
    client, alice: SeededConsultant
) -> None:
    response = client.get("/earnings/consultancy-commissions", headers=auth_header(alice))
    assert response.status_code == 200, response.text
    rows = response.json()
    assert len(rows) == 4
    assert [(r["delivery_label"], r["sourcing_label"]) for r in rows] == [
        ("Bruntsfield-led", "Self-sourced"),
        ("Bruntsfield-led", "Firm-sourced"),
        ("Consultant-led", "Self-sourced"),
        ("Consultant-led", "Firm-sourced"),
    ]
    assert all(r["schedule_version"] for r in rows)


def test_consultancy_commissions_needs_authentication(client) -> None:
    assert client.get("/earnings/consultancy-commissions").status_code == 401


def test_the_statement_states_how_consulting_pays_even_with_no_consultancy_lines(
    client, alice: SeededConsultant
) -> None:
    """A statement showing no consultancy should still say how consulting would be paid — the
    absence of a line is not an answer to "what do I earn on consulting?"."""
    response = client.get("/earnings/statement", headers=auth_header(alice))
    assert response.status_code == 200, response.text
    # The .docx is a zip; the document text lives in word/document.xml.
    import zipfile
    from io import BytesIO

    with zipfile.ZipFile(BytesIO(response.content)) as bundle:
        xml = bundle.read("word/document.xml").decode("utf-8")
    assert "Consulting commissions (Stream B)" in xml
    assert "Consultant-led" in xml
    assert "65% first year" in xml
