"""Stream-B consultancy carrots (GRS-0187, ADR-0026).

The earnings page showed "Consultancy (Stream B) £0.00" and nothing else, so an advisor could not
tell whether the zero meant "you have earned nothing yet" or "this is not a thing you earn on".
The computation already existed; what these tests pin is that what gets surfaced is READ from the
schedule rather than typed beside it, because a rate card that can drift from the real schedule is
worse than no rate card.
"""

from __future__ import annotations

import pytest
from bcap_contracts.commissions import (
    CommissionConfig,
    CommissionConfigError,
    ConsultancyRate,
    DeliveryType,
    SourcingAttribution,
    load_commission_config,
)
from bcap_contracts.money import Currency, Money

from grassmarket.earnings.commission import compute_consultancy_commission
from grassmarket.earnings.consultancy_carrot import (
    all_consultancy_carrots,
    consultancy_commission_carrot,
)

EXAMPLE_MINOR = 10_000_000  # £100,000, the same teaching figure the product carrot uses


def _config() -> CommissionConfig:
    return load_commission_config()


def test_the_matrix_surfaces_as_four_cells_in_a_stable_order() -> None:
    carrots = all_consultancy_carrots(_config())
    assert [(c.delivery_type, c.sourcing) for c in carrots] == [
        (DeliveryType.BRUNTSFIELD_LED, SourcingAttribution.SELF_SOURCED),
        (DeliveryType.BRUNTSFIELD_LED, SourcingAttribution.FIRM_SOURCED),
        (DeliveryType.CONSULTANT_LED, SourcingAttribution.SELF_SOURCED),
        (DeliveryType.CONSULTANT_LED, SourcingAttribution.FIRM_SOURCED),
    ]


def test_the_rates_are_the_shipped_schedule() -> None:
    """The v7 matrix as agreed (ADR-0026), asserted in bps so a typo in the YAML fails here."""
    carrots = all_consultancy_carrots(_config())
    assert [(c.yr1_bps, c.thereafter_bps) for c in carrots] == [
        (3000, 2500),
        (1500, 1000),
        (6500, 5500),
        (4500, 3500),
    ]


def test_each_worked_example_is_the_live_computation_not_a_written_figure() -> None:
    config = _config()
    for carrot in all_consultancy_carrots(config):
        expected_yr1 = compute_consultancy_commission(
            carrot.example_deal, carrot.sourcing, carrot.delivery_type, 1, config
        )
        expected_after = compute_consultancy_commission(
            carrot.example_deal, carrot.sourcing, carrot.delivery_type, 2, config
        )
        # Minor units: the integer money discipline, not a float comparison.
        assert carrot.yr1_commission.amount_minor == expected_yr1.amount_minor
        assert carrot.thereafter_commission.amount_minor == expected_after.amount_minor


def test_the_example_prices_the_illustrative_hundred_thousand() -> None:
    carrots = all_consultancy_carrots(_config())
    assert all(c.example_deal.amount_minor == EXAMPLE_MINOR for c in carrots)
    # Consultant-led, self-sourced at 65% of £100,000.
    consultant_self = carrots[2]
    assert consultant_self.yr1_commission.amount_minor == 6_500_000
    assert consultant_self.thereafter_commission.amount_minor == 5_500_000


def test_the_example_carries_its_provenance_ref() -> None:
    # A bare figure is the thing ADR-0002 forbids; the ref says which assumption produced it.
    carrot = all_consultancy_carrots(_config())[0]
    assert carrot.example_deal.assumption_register_ref == "grs-0187:illustrative-example-deal"


def test_the_carrot_moves_with_the_schedule_rather_than_being_written_down() -> None:
    """The property that matters: change the config and the carrot changes. If any of these
    numbers were typed into the carrot module, this test would fail."""
    live = _config()
    altered = live.model_copy(
        update={
            "version": "test-schedule",
            "consultancy": {
                DeliveryType.CONSULTANT_LED: {
                    SourcingAttribution.SELF_SOURCED: ConsultancyRate(
                        yr1_bps=9000, thereafter_bps=100
                    ),
                    SourcingAttribution.FIRM_SOURCED: live.require_consultancy_rate(
                        DeliveryType.CONSULTANT_LED, SourcingAttribution.FIRM_SOURCED
                    ),
                },
                DeliveryType.BRUNTSFIELD_LED: live.consultancy[DeliveryType.BRUNTSFIELD_LED],
            },
        }
    )
    carrot = consultancy_commission_carrot(
        DeliveryType.CONSULTANT_LED, SourcingAttribution.SELF_SOURCED, altered
    )
    assert carrot.yr1_bps == 9000
    assert carrot.thereafter_bps == 100
    assert carrot.yr1_commission.amount_minor == 9_000_000
    assert carrot.thereafter_commission.amount_minor == 100_000
    assert carrot.schedule_version == "test-schedule"


def test_the_labels_travel_with_the_rate() -> None:
    """Wording lives beside the number, so a label and the figure it describes cannot be edited
    apart from each other in the UI."""
    carrots = all_consultancy_carrots(_config())
    assert [(c.delivery_label, c.sourcing_label) for c in carrots] == [
        ("Bruntsfield-led", "Self-sourced"),
        ("Bruntsfield-led", "Firm-sourced"),
        ("Consultant-led", "Self-sourced"),
        ("Consultant-led", "Firm-sourced"),
    ]


def test_an_unknown_cell_refuses_rather_than_inventing_a_rate() -> None:
    config = _config()
    # A legacy sourcing value is not part of the v7 matrix and has no cell.
    with pytest.raises(CommissionConfigError, match="No Stream-B rate configured"):
        consultancy_commission_carrot(
            DeliveryType.CONSULTANT_LED, SourcingAttribution.CO_SOURCED, config
        )


def test_a_caller_may_price_its_own_example() -> None:
    config = _config()
    deal = Money(amount_minor=50_000_00, currency=Currency.GBP, assumption_register_ref="test:deal")
    carrot = consultancy_commission_carrot(
        DeliveryType.CONSULTANT_LED, SourcingAttribution.SELF_SOURCED, config, example_deal=deal
    )
    assert carrot.example_deal.amount_minor == 50_000_00
    assert carrot.yr1_commission.amount_minor == 3_250_000  # 65% of £50,000


def test_the_schedule_version_is_stamped() -> None:
    config = _config()
    assert all(c.schedule_version == config.version for c in all_consultancy_carrots(config))
