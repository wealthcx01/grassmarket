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


def test_config_missing_a_tier_refuses_to_load() -> None:
    with pytest.raises(CommissionConfigError, match="no rates for tier"):
        CommissionConfig(
            version="broken",
            currency=Currency.GBP,
            rates_bps={
                ConsultantTier.ADVISOR: {a: 1000 for a in SourcingAttribution},
                ConsultantTier.CONSULTANT: {a: 1000 for a in SourcingAttribution},
                # venture_associate missing entirely
            },
        )


def test_config_missing_an_attribution_refuses_to_load() -> None:
    with pytest.raises(CommissionConfigError, match="missing attribution"):
        CommissionConfig(
            version="broken",
            currency=Currency.GBP,
            rates_bps={
                tier: {SourcingAttribution.SELF_SOURCED: 1000}  # only one of three attributions
                for tier in ConsultantTier
            },
        )


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
