"""Sell-from-report (GRS-0162, ADR-0039): the product→gap fit map and the deterministic join.

The fit map is configuration validated at load (fail loud on unknown products/keys, missing
catalogue products, or a product addressing nothing — ADR-0001). The join recommends only against
assessed-and-weak targets (Not Assessed is never a gap, D9), ranks by gap severity alone
(commission never enters the ordering — ADR-0002), and is owner-scoped + finalised-only at the
HTTP boundary.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from bcap_contracts import commissions as commissions_module
from bcap_contracts.assessments import (
    Assessment,
    AssessmentDocument,
    AssessmentState,
    PowerEntry,
    SubcomponentRating,
)
from bcap_contracts.commissions import load_commission_config
from bcap_contracts.common import EvidenceGrade
from bcap_contracts.product_fit import (
    GapKind,
    ProductFitError,
    ProductFitMap,
    load_product_fit,
)
from bcap_contracts.registry import load_registry

from grassmarket.demo.brokerage_showcase import (
    HARGREAVES_LANSDOWN,
    REVOLUT,
    WEBULL,
    BrokerageSpec,
    showcase_document,
)
from grassmarket.earnings.opportunities import sell_opportunities

from .conftest import auth_header

# ---------------------------------------------------------------- fit-map loading (ADR-0001)


def test_fit_map_loads_and_covers_the_whole_catalogue() -> None:
    fit_map = load_product_fit()
    assert set(fit_map.products) == set(load_commission_config().products)
    registry = load_registry()
    for fit in fit_map.products.values():
        assert set(fit.modules) <= registry.module_keys()
        assert set(fit.c_modules) <= registry.c_module_keys()
        assert set(fit.powers) <= registry.power_keys()


def _fit_yaml_with(overrides: dict) -> dict:
    """The real catalogue as a raw fit mapping, with per-product overrides applied."""
    products = {
        pid: {"modules": ["APP_SERVER"], "c_modules": [], "powers": [], "pitch": "x"}
        for pid in load_commission_config().products
    }
    products.update(overrides)
    return {"version": "test", "products": products}


@pytest.fixture
def patched_fit(monkeypatch):
    """Point the loader at an in-test mapping; always restore the real cached map after."""

    def apply(raw: dict) -> None:
        load_product_fit.cache_clear()
        monkeypatch.setattr(commissions_module, "_load_yaml", lambda name: raw)

    yield apply
    load_product_fit.cache_clear()


def test_missing_catalogue_product_refuses(patched_fit) -> None:
    raw = _fit_yaml_with({})
    del raw["products"]["benzinga"]
    patched_fit(raw)
    with pytest.raises(ProductFitError, match="missing catalogue products"):
        load_product_fit()


def test_unknown_product_refuses(patched_fit) -> None:
    patched_fit(
        _fit_yaml_with(
            {
                "no_such_product": {
                    "modules": ["APP_SERVER"],
                    "c_modules": [],
                    "powers": [],
                    "pitch": "x",
                }
            }
        )
    )
    with pytest.raises(ProductFitError, match="not in commissions.yaml"):
        load_product_fit()


def test_unknown_registry_key_refuses(patched_fit) -> None:
    patched_fit(
        _fit_yaml_with(
            {"openbb": {"modules": ["NOT_A_MODULE"], "c_modules": [], "powers": [], "pitch": "x"}}
        )
    )
    with pytest.raises(ProductFitError, match="unknown registry"):
        load_product_fit()


def test_product_addressing_nothing_refuses() -> None:
    with pytest.raises(ProductFitError, match="addresses no"):
        ProductFitMap.model_validate(
            {
                "version": "t",
                "products": {
                    "openbb": {"modules": [], "c_modules": [], "powers": [], "pitch": "x"}
                },
            }
        )


# ---------------------------------------------------------------- the join (service level)


def _finalised(document: AssessmentDocument) -> Assessment:
    now = datetime.now(UTC)
    return Assessment(
        id=uuid4(),
        owner_consultant_id=uuid4(),
        created_at=now,
        updated_at=now,
        subject=document.subject,
        state=AssessmentState.FINALISED,
        document=document,
    )


def test_hl_report_recommends_connecttrade_against_its_basic_gaps() -> None:
    out = sell_opportunities(_finalised(showcase_document(HARGREAVES_LANSDOWN)))
    assert [o.product_id for o in out.opportunities] == ["connecttrade"]
    gap_keys = {g.key for g in out.opportunities[0].gaps}
    assert "OEMS" in gap_keys  # the report's Basic-banded execution stack
    assert "CUST_TRADING_EXPERIENCE" in gap_keys
    # The carrot rides along for information.
    assert out.opportunities[0].carrot.product_id == "connecttrade"
    assert out.opportunities[0].carrot.yr1_commission.amount_minor > 0


def test_recommendations_cohere_with_the_report_banding() -> None:
    """Revolut's MARKET_DATA is all-Developing, which the rating gate bands Advanced — so no
    market-data product is recommended (the pitch must never contradict the report's own words).
    Its OEMS bands Developing → ConnectTrade is the one honest recommendation."""
    out = sell_opportunities(_finalised(showcase_document(REVOLUT)))
    assert [o.product_id for o in out.opportunities] == ["connecttrade"]


def test_power_only_gaps_rank_after_module_gaps_and_tie_on_product_id() -> None:
    """WeBull: no addressed module gaps, but BRANDING is Emerging → both Brandfetch products list
    on the power gap, tied severity, product_id order. (Also proves commission never reorders —
    distribution at 750bps and redistribution at 375bps sort identically.)"""
    out = sell_opportunities(_finalised(showcase_document(WEBULL)))
    assert [o.product_id for o in out.opportunities] == [
        "brandfetch_distribution",
        "brandfetch_redistribution",
    ]
    for o in out.opportunities:
        assert [g.kind for g in o.gaps] == [GapKind.POWER]
        assert {g.key for g in o.gaps} == {"BRANDING"}


def _spec_with(
    v_base: dict[str, str], v_over: dict[str, str], c_base: dict[str, str]
) -> BrokerageSpec:
    """A synthetic spec sharing REVOLUT's powers/metrics with custom maturity levels."""
    return BrokerageSpec(
        subject="Synthetic",
        metrics=REVOLUT.metrics,
        powers=REVOLUT.powers,
        v_base=tuple(v_base.items()),
        v_over=tuple(v_over.items()),
        c_base=tuple(c_base.items()),
        product_id="benzinga",
        deal_value_minor=1,
    )


_ALL_MODULES = dict.fromkeys(
    (
        "FRONTEND",
        "APP_SERVER",
        "MARKET_DATA",
        "ORCHESTRATION",
        "CMS",
        "BACKOFFICE",
        "OEMS",
        "EMS_GATEWAY",
        "LIQ_CONNECT",
    ),
    "Frontier",
)
_ALL_C = dict.fromkeys(
    (
        "CUST_ONBOARDING",
        "CUST_UI_NAVIGATION",
        "CUST_TRADING_EXPERIENCE",
        "CUST_FEES_PRICING",
        "CUST_PRODUCT_RANGE",
        "CUST_RESEARCH_EDUCATION",
        "CUST_AI_PERSONALISATION",
        "CUST_SUPPORT_COMMUNITY",
        "CUST_SECURITY_REGULATION",
        "CUST_INNOVATION_DIFFERENTIATORS",
    ),
    "Frontier",
)


def test_strong_everywhere_recommends_nothing() -> None:
    """All-Frontier modules and C — every addressed target is strong. Powers are REVOLUT's (one
    Emerging BRANDING would list Brandfetch), so pin powers strong via overrides on the doc."""
    doc = showcase_document(_spec_with(_ALL_MODULES, {}, _ALL_C))
    strong_powers = tuple(
        PowerEntry(
            power_key=p.power_key,
            benefit="Established",
            barrier="Established",
            benefit_grade=EvidenceGrade.E3_ARTIFACT,
            barrier_grade=EvidenceGrade.E3_ARTIFACT,
        )
        for p in doc.powers
    )
    doc = doc.model_copy(update={"powers": strong_powers})
    out = sell_opportunities(_finalised(doc))
    assert out.opportunities == ()


def test_ranking_is_deepest_module_gap_first_never_commission() -> None:
    """MARKET_DATA all-Basic (deepest) beats OEMS's shallower Developing-banded gap regardless of
    rates: benzinga+openbb (tie → product_id) come before connecttrade."""
    levels = dict(_ALL_MODULES)
    levels["MARKET_DATA"] = "Basic"
    levels["OEMS"] = "Developing"
    doc = showcase_document(_spec_with(levels, {"OEMS_ORDER_TYPES": "Basic"}, _ALL_C))
    out = sell_opportunities(_finalised(doc))
    assert [o.product_id for o in out.opportunities] == ["benzinga", "openbb", "connecttrade"]
    deepest = [o.gaps[0].q_m for o in out.opportunities[:2]]
    assert all(q is not None and q < 0.3 for q in deepest)


def test_not_assessed_is_never_a_gap() -> None:
    """A scoreable-but-sparse document — only OEMS rated (Basic), no C dimension, MARKET_DATA /
    CMS / FRONTEND untouched: ConnectTrade lists on the OEMS gap and reports the unassessed C
    module honestly; no market-data/brandfetch product invents a gap from absence of data.
    (Powers/metric present because a finalised assessment is always V-scoreable — REVOLUT's
    powers keep BRANDING Established, so no power gap either.)"""
    registry = load_registry()
    oems = registry.require_module("OEMS")
    base = showcase_document(REVOLUT)  # for its scoreable powers + metrics
    doc = AssessmentDocument(
        subject="Sparse",
        subcomponents=tuple(
            SubcomponentRating(
                module_key="OEMS",
                subcomponent_key=s.key,
                level="Basic",
                evidence_grade=EvidenceGrade.E3_ARTIFACT,
            )
            for s in oems.subcomponents
        ),
        metrics=base.metrics,
        powers=base.powers,
    )
    out = sell_opportunities(_finalised(doc))
    assert [o.product_id for o in out.opportunities] == ["connecttrade"]
    only = out.opportunities[0]
    assert {g.key for g in only.gaps} == {"OEMS"}  # EMS_GATEWAY unassessed → not a gap
    assert "Trading Experience" in ", ".join(only.not_yet_assessed)


# ---------------------------------------------------------------- HTTP boundary


def _finalise_sandbox(client, headers, document: AssessmentDocument) -> str:
    aid = client.post(
        "/assessments",
        json={"subject": document.subject, "provenance": "sandbox"},
        headers=headers,
    ).json()["id"]
    assert (
        client.put(
            f"/assessments/{aid}", json=document.model_dump(mode="json"), headers=headers
        ).status_code
        == 200
    )
    finalised = client.post(f"/assessments/{aid}/finalise", headers=headers)
    assert finalised.status_code == 200, finalised.text
    return aid


def test_endpoint_returns_the_join_for_a_finalised_assessment(client, alice) -> None:
    headers = auth_header(alice)
    aid = _finalise_sandbox(client, headers, showcase_document(HARGREAVES_LANSDOWN))
    res = client.get(f"/assessments/{aid}/sell-opportunities", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["subject"] == "Hargreaves Lansdown"
    assert [o["product_id"] for o in body["opportunities"]] == ["connecttrade"]
    assert body["fit_version"] == load_product_fit().version


def test_endpoint_refuses_an_unfinalised_assessment(client, alice) -> None:
    headers = auth_header(alice)
    aid = client.post("/assessments", json={"subject": "Draft Co"}, headers=headers).json()["id"]
    res = client.get(f"/assessments/{aid}/sell-opportunities", headers=headers)
    assert res.status_code == 409
    assert "finalise" in res.json()["detail"].lower()


def test_endpoint_is_owner_scoped(client, alice, bob) -> None:
    aid = _finalise_sandbox(client, auth_header(alice), showcase_document(HARGREAVES_LANSDOWN))
    res = client.get(f"/assessments/{aid}/sell-opportunities", headers=auth_header(bob))
    assert res.status_code == 404  # scoping is absolute: not even existence is revealed
