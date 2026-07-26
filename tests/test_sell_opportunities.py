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
        pid: {
            "modules": ["APP_SERVER"],
            "c_modules": [],
            "powers": [],
            "profiles": ["retail"],
            "pitch": "x",
        }
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
                    "profiles": ["retail"],
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
            {
                "openbb": {
                    "modules": ["NOT_A_MODULE"],
                    "c_modules": [],
                    "powers": [],
                    "profiles": ["retail"],
                    "pitch": "x",
                }
            }
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
                    "openbb": {
                        "modules": [],
                        "c_modules": [],
                        "powers": [],
                        "profiles": ["retail"],
                        "pitch": "x",
                    }
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


def test_market_data_gap_recommends_the_agreed_research_products() -> None:
    """A Market Data gap is addressed by the agreed research products (benzinga, openbb), which
    tie on the same gap and order by product_id. (Replaces the old ConnectTrade/OEMS case: with
    ConnectTrade removed, GRS-0183, no agreed product addresses OEMS, so the positive coverage
    moves to a gap an agreed product genuinely fits.)"""
    levels = dict(_ALL_MODULES)
    levels["MARKET_DATA"] = "Basic"
    out = sell_opportunities(_finalised(showcase_document(_spec_with(levels, {}, _ALL_C))))
    assert [o.product_id for o in out.opportunities] == ["benzinga", "openbb"]
    for o in out.opportunities:
        assert "MARKET_DATA" in {g.key for g in o.gaps}
        assert o.carrot.product_id == o.product_id
        assert o.carrot.yr1_commission.amount_minor > 0


def test_report_with_no_agreed_product_for_its_gaps_recommends_nothing() -> None:
    """Revolut's Market Data is all-Developing, which the rating gate bands Advanced, so no
    market-data product is recommended (a pitch must never contradict the report's own words).
    Its one real gap was OEMS, which ConnectTrade used to address; with ConnectTrade removed
    (GRS-0183) no agreed product fits, so the report honestly recommends nothing rather than a
    product with no agreement."""
    out = sell_opportunities(_finalised(showcase_document(REVOLUT)))
    assert out.opportunities == ()


def test_power_only_gaps_are_listed_and_scoped_to_the_segment() -> None:
    """WeBull: no addressed module gaps, but BRANDING is Emerging, so a Brandfetch product lists
    on the power gap.

    Only the DISTRIBUTION variant, though. WeBull is a retail brokerage, and redistribution is an
    exchange/vendor licence (GRS-0185). Before the re-scoping both variants carried
    `profiles: [retail]` and this test asserted both were offered, which was the founder's
    complaint: the panel could recommend a venue's data-licensing product to a retail broker."""
    out = sell_opportunities(_finalised(showcase_document(WEBULL)))
    assert [o.product_id for o in out.opportunities] == ["brandfetch_distribution"]
    for o in out.opportunities:
        assert [g.kind for g in o.gaps] == [GapKind.POWER]
        assert {g.key for g in o.gaps} == {"BRANDING"}


def test_a_retail_report_never_offers_the_redistribution_licence() -> None:
    """The segment separation, asserted across every retail showcase subject rather than one."""
    for spec in (REVOLUT, WEBULL):
        out = sell_opportunities(_finalised(showcase_document(spec)))
        assert all(o.product_id != "brandfetch_redistribution" for o in out.opportunities), (
            spec.subject
        )


def test_the_two_brandfetch_variants_target_different_segments() -> None:
    """Config-level proof of the split, independent of any one assessment's gaps."""
    fit = load_product_fit()
    distribution = fit.products["brandfetch_distribution"]
    redistribution = fit.products["brandfetch_redistribution"]
    assert distribution.profiles == ("retail",)
    assert redistribution.profiles == ("exchange",)
    # No segment sees both.
    assert set(distribution.profiles).isdisjoint(redistribution.profiles)
    # The fit TARGETS differ too, not just the prose: a retail customer-navigation module does
    # not describe a venue redistributing reference data.
    assert distribution.c_modules == ("CUST_UI_NAVIGATION",)
    assert redistribution.c_modules == ()


def test_an_unknown_operating_model_profile_fails_loud(patched_fit) -> None:
    """Key drift in the fit map must abort at load, not silently drop a product (#3).

    This is what keeps the segment split honest: `information_vendor` is the profile the
    redistribution licence should eventually carry, and until the registry has it, naming it here
    fails the load rather than quietly scoping the product to nothing."""
    raw = _fit_yaml_with({})
    raw["products"]["brandfetch_redistribution"]["profiles"] = ["information_vendor"]
    patched_fit(raw)
    with pytest.raises(ProductFitError):
        load_product_fit()


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
    """A deep Market Data gap is recommended by both agreed research products, which tie on that
    gap and order by product_id, never by commission (benzinga 750bps and openbb 1500bps sort
    identically). (Previously proved ordering against ConnectTrade; retargeted after GRS-0183.)"""
    levels = dict(_ALL_MODULES)
    levels["MARKET_DATA"] = "Basic"
    doc = showcase_document(_spec_with(levels, {}, _ALL_C))
    out = sell_opportunities(_finalised(doc))
    assert [o.product_id for o in out.opportunities] == ["benzinga", "openbb"]
    deepest = [o.gaps[0].q_m for o in out.opportunities]
    assert all(q is not None and q < 0.3 for q in deepest)


def test_not_assessed_is_never_a_gap() -> None:
    """A scoreable-but-sparse document with only Market Data rated (Basic) and the rest untouched:
    the agreed research products list on the Market Data gap and report the unassessed Research &
    Education C module honestly, rather than inventing a gap from absence of data. (Retargeted from
    OEMS/ConnectTrade to Market Data/openbb after GRS-0183.) Powers and a metric are present
    because a finalised assessment is always V-scoreable; REVOLUT's powers keep BRANDING
    Established, so there is no power gap either."""
    registry = load_registry()
    base = showcase_document(REVOLUT)  # for its scoreable powers + metrics
    # Market Data Basic is the gap. APP_SERVER (a critical-for-L module) rated Frontier makes the
    # document V-scoreable without itself being a gap; no agreed product addresses it anyway.
    subs = tuple(
        SubcomponentRating(
            module_key="MARKET_DATA",
            subcomponent_key=s.key,
            level="Basic",
            evidence_grade=EvidenceGrade.E3_ARTIFACT,
        )
        for s in registry.require_module("MARKET_DATA").subcomponents
    ) + tuple(
        SubcomponentRating(
            module_key="APP_SERVER",
            subcomponent_key=s.key,
            level="Frontier",
            evidence_grade=EvidenceGrade.E3_ARTIFACT,
        )
        for s in registry.require_module("APP_SERVER").subcomponents
    )
    doc = AssessmentDocument(
        subject="Sparse", subcomponents=subs, metrics=base.metrics, powers=base.powers
    )
    out = sell_opportunities(_finalised(doc))
    assert [o.product_id for o in out.opportunities] == ["benzinga", "openbb"]
    for o in out.opportunities:
        assert {g.key for g in o.gaps} == {"MARKET_DATA"}
        # The addressed C module was never assessed, so it is reported honestly, not a gap.
        assert "Research & Education" in ", ".join(o.not_yet_assessed)


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
    # A Market Data gap yields the agreed research products (post-GRS-0183; HL's own gaps are now
    # served by no agreed product, so the join-returns-opportunities case uses a fitted gap).
    levels = dict(_ALL_MODULES)
    levels["MARKET_DATA"] = "Basic"
    doc = showcase_document(_spec_with(levels, {}, _ALL_C)).model_copy(
        update={"subject": "Market Data Gap Co"}
    )
    aid = _finalise_sandbox(client, headers, doc)
    res = client.get(f"/assessments/{aid}/sell-opportunities", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["subject"] == "Market Data Gap Co"
    assert [o["product_id"] for o in body["opportunities"]] == ["benzinga", "openbb"]
    assert body["fit_version"] == load_product_fit().version


def test_connecttrade_never_appears_in_any_recommendation() -> None:
    """GRS-0183 guard: the removed product must not surface for any showcase assessment, and the
    two loaders no longer know it."""
    from bcap_contracts.commissions import load_commission_config

    assert "connecttrade" not in load_commission_config().products
    assert "connecttrade" not in load_product_fit().products
    for spec in (REVOLUT, HARGREAVES_LANSDOWN, WEBULL):
        out = sell_opportunities(_finalised(showcase_document(spec)))
        assert all(o.product_id != "connecttrade" for o in out.opportunities)


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


# ---------------------------------------------------------------- segment scoping (GRS-0169)


def test_wealth_assessment_gets_no_retail_products_and_an_honest_note() -> None:
    """The staging-rerun finding: a wealth report was pitched Brandfetch off a power gap, citing a
    retail C-module its taxonomy doesn't contain. The catalogue is retail-only, so a wealth
    assessment now gets ZERO recommendations plus the explicit segment-not-covered note — never a
    wrong-segment pitch, and never a silent empty state."""
    from bcap_contracts.assessments import BusinessProfile, MetricEntry
    from bcap_contracts.registry import load_profile

    # A minimal genuinely-scoreable WEALTH document: one rated core subcomponent from the wealth
    # view, one in-domain wealth metric (first anchor's raw), all 7 powers (shared across
    # profiles) — with a WEAK BRANDING power, the exact gap Brandfetch used to pitch off.
    view = load_registry().for_profile(load_profile("wealth"))
    core_sub = next(s for m in view.modules if m.key == "APP_SERVER" for s in m.subcomponents)
    metric = view.metrics[0]
    base = showcase_document(WEBULL)  # its powers carry the Emerging BRANDING gap
    doc = AssessmentDocument(
        subject="Wealth Co",
        profile=BusinessProfile(operating_model="wealth"),
        subcomponents=(
            SubcomponentRating(
                module_key="APP_SERVER",
                subcomponent_key=core_sub.key,
                level="Basic",
                evidence_grade=EvidenceGrade.E3_ARTIFACT,
            ),
        ),
        metrics=(
            MetricEntry(
                metric_key=metric.key,
                raw=metric.normalisation.anchors[0].raw,
                confidence="estimated",
            ),
        ),
        powers=base.powers,
    )
    out = sell_opportunities(_finalised(doc))
    assert out.opportunities == ()  # no wrong-segment Brandfetch pitch despite the BRANDING gap
    assert out.note is not None and "wealth" in out.note
    # And retail keeps its recommendations + no note (in-segment behaviour unchanged).
    retail = sell_opportunities(_finalised(showcase_document(WEBULL)))
    assert retail.opportunities and retail.note is None


def test_unknown_profile_in_fit_map_refuses(patched_fit) -> None:
    patched_fit(
        _fit_yaml_with(
            {
                "openbb": {
                    "modules": ["MARKET_DATA"],
                    "c_modules": [],
                    "powers": [],
                    "profiles": ["hedge_fund"],
                    "pitch": "x",
                }
            }
        )
    )
    with pytest.raises(ProductFitError, match="unknown operating-model profile"):
        load_product_fit()
