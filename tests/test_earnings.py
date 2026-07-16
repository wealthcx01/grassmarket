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
    compute_engagement_commission,
)
from grassmarket.pipeline.fees import is_within_attribution_window


def _gbp(minor: int, ref: str = "contract:test") -> Money:
    return Money(amount_minor=minor, currency=Currency.GBP, assumption_register_ref=ref)


# --- Commission golden master (hand-computed against commissions.yaml) --------------------


@pytest.mark.parametrize(
    ("value_minor", "tier", "attribution", "expected_minor"),
    [
        # £50,000 × consultant self-sourced (2500 bps = 25%) = £12,500
        (5_000_000, ConsultantTier.CONSULTANT, SourcingAttribution.SELF_SOURCED, 1_250_000),
        # £30,000 × advisor co-sourced (1500 bps = 15%) = £4,500
        (3_000_000, ConsultantTier.ADVISOR, SourcingAttribution.CO_SOURCED, 450_000),
        # £100,000 × venture-associate Bruntsfield-sourced (750 bps = 7.5%) = £7,500
        (
            10_000_000,
            ConsultantTier.VENTURE_ASSOCIATE,
            SourcingAttribution.BRUNTSFIELD_SOURCED,
            750_000,
        ),
    ],
)
def test_commission_golden(value_minor, tier, attribution, expected_minor) -> None:
    config = load_commission_config()
    got = compute_engagement_commission(_gbp(value_minor), tier, attribution, config)
    assert got.amount_minor == expected_minor
    assert got.currency is Currency.GBP
    # The £ is never bare — it cites the config rate reference it derives from.
    assert got.assumption_register_ref == config.rate_ref(tier, attribution)


def test_commission_rounding_is_deterministic_half_to_even() -> None:
    config = load_commission_config()
    # consultant self-sourced = 2500 bps (25%). 10 minor × 0.25 = 2.5 → 2 (round-half-to-even).
    got = compute_engagement_commission(
        _gbp(10), ConsultantTier.CONSULTANT, SourcingAttribution.SELF_SOURCED, config
    )
    assert got.amount_minor == 2
    # 6 minor × 0.25 = 1.5 → 2 (nearest even).
    got2 = compute_engagement_commission(
        _gbp(6), ConsultantTier.CONSULTANT, SourcingAttribution.SELF_SOURCED, config
    )
    assert got2.amount_minor == 2


def test_commission_refuses_cross_currency() -> None:
    config = load_commission_config()  # GBP
    usd = Money(amount_minor=1000, currency=Currency.USD, assumption_register_ref="x")
    with pytest.raises(ValueError, match="no silent FX"):
        compute_engagement_commission(
            usd, ConsultantTier.ADVISOR, SourcingAttribution.SELF_SOURCED, config
        )


def test_commission_refuses_negative_value() -> None:
    config = load_commission_config()
    with pytest.raises(ValueError, match="negative"):
        compute_engagement_commission(
            _gbp(-1), ConsultantTier.ADVISOR, SourcingAttribution.SELF_SOURCED, config
        )


# --- Config completeness fails loud ------------------------------------------------------


def _v7_kwargs() -> dict:
    """A complete, valid v7 config (both streams) — tests mutate a copy to prove fail-loud."""
    return dict(
        version="test-v7",
        currency=Currency.GBP,
        products={
            "connecttrade": ProductRate(
                name="ConnectTrade", yr1_bps=1500, yr2_bps=1000, window_months=24
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
    assert config.product_ref("connecttrade").name == "ConnectTrade"


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
    assert _hash() != _hash(product_id="connecttrade")
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
