"""Product-course framework tests (GRS-0123).

The three acceptance criteria: a course instantiated from the template exposes all four required
sections (relevance / white-label / sell-motion / commission); the commission figure resolves from
the Earnings v7 compute (ADR-0026), not a hardcoded number; and the template is reusable across
products without bespoke structure.
"""

from __future__ import annotations

from bcap_contracts.commissions import (
    CommissionConfig,
    ConsultancyRate,
    ProductRate,
    load_commission_config,
)
from bcap_contracts.money import Currency

from grassmarket.earnings.product_carrot import (
    product_commission_carrot,
)
from grassmarket.workbench.content.product_course import (
    ProductCourseSpec,
    build_product_course,
)
from tests.conftest import SeededConsultant, auth_header

_SPEC = ProductCourseSpec(
    product_id="openbb",
    slug="openbb",
    display_name="OpenBB",
    relevance="Relevant to a retail broker / wealth manager / exchange because …",
    white_label="White-labelling means …",
    sell_motion="Introduce it by …",
)


def _config_with(product_id: str, *, yr1: int, yr2: int) -> CommissionConfig:
    """A minimal valid v7 config carrying one product at a chosen rate — lets a test prove the
    carrot tracks config, not a constant."""
    return CommissionConfig(
        version="test-sched",
        currency=Currency.GBP,
        products={product_id: ProductRate(name="Test", yr1_bps=yr1, yr2_bps=yr2, window_months=24)},
        consultancy={
            dt: {src: ConsultancyRate(yr1_bps=1000, thereafter_bps=500) for src in src_map}
            for dt, src_map in load_commission_config().consultancy.items()
        },
    )


def test_carrot_resolves_from_the_v7_compute_not_a_constant() -> None:
    # 15% Year-1 on a £100,000 example = £15,000; change the config and the carrot changes with it.
    cfg = _config_with("openbb", yr1=1500, yr2=1000)
    carrot = product_commission_carrot("openbb", cfg)
    assert carrot.yr1_bps == 1500
    assert carrot.yr1_commission.amount_minor == 1_500_000  # £15,000 in pence
    assert carrot.yr2_commission.amount_minor == 1_000_000  # £10,000 in pence
    assert carrot.schedule_version == "test-sched"

    dearer = product_commission_carrot("openbb", _config_with("openbb", yr1=3000, yr2=2000))
    assert dearer.yr1_commission.amount_minor == 3_000_000  # tracks the config, not hardcoded


def test_template_exposes_all_four_sections() -> None:
    carrot = product_commission_carrot("openbb", _config_with("openbb", yr1=1500, yr2=1000))
    tree = build_product_course(_SPEC, carrot)
    titles = [lesson.title for module in tree.modules for lesson in module.lessons]
    assert titles == [
        "Why it's relevant",
        "What white-labelling is",
        "The sell motion",
        "How much you earn",
    ]
    # The commission section carries the LIVE figure, not a typed number.
    commission = tree.modules[0].lessons[3].body
    assert "15%" in commission and "£15,000" in commission
    assert "test-sched" in commission  # stamped with the schedule version


def test_template_is_reusable_across_products() -> None:
    cfg = load_commission_config()  # the real catalogue
    for pid in ("openbb", "brandfetch_distribution", "connecttrade"):
        spec = ProductCourseSpec(
            product_id=pid,
            slug=pid.replace("_", "-"),
            display_name=pid,
            relevance="…",
            white_label="…",
            sell_motion="…",
        )
        tree = build_product_course(spec, product_commission_carrot(pid, cfg))
        # Same four-section spine every time — no bespoke structure per product.
        assert len(tree.modules[0].lessons) == 4


def test_carrot_mismatch_refuses() -> None:
    import pytest

    other = product_commission_carrot("connecttrade", load_commission_config())
    with pytest.raises(ValueError):
        build_product_course(_SPEC, other)  # spec is 'openbb', carrot is 'connecttrade'


def test_unknown_product_fails_loud() -> None:
    import pytest
    from bcap_contracts.commissions import CommissionConfigError

    with pytest.raises(CommissionConfigError):
        product_commission_carrot("no-such-product", load_commission_config())


def test_http_product_commissions_are_live(client, alice: SeededConsultant) -> None:
    resp = client.get("/earnings/product-commissions", headers=auth_header(alice))
    assert resp.status_code == 200
    carrots = resp.json()
    ids = {c["product_id"] for c in carrots}
    assert {"openbb", "connecttrade"} <= ids  # the live catalogue
    for c in carrots:
        assert c["schedule_version"]  # stamped, never bare
