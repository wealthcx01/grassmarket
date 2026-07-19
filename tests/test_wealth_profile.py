"""GRS-0147 — the wealth operating-model profile (ADR-0035, extends ADR-0025). A wealth / investment
manager scores over a wealth module set (suitability, mandate mix, custody/CASS, AUM economics,
financial planning, investment governance) via the profile view — WITHOUT being mislabelled as a
retail brokerage — and over a wealth-NATIVE B index (AUM, net-new-money, margin, retention…) rather
than retail AUA/ARPU. Its draft coefficient set carries the wealth criticals. Retail is untouched
(golden master), and the profiles' coefficient sets are mutually incompatible, so a wealth firm's
L/B can never be silently pooled with a broker's."""

from __future__ import annotations

import pytest
from bcap_contracts.registry import (
    RegistryError,
    load_profile,
    load_registry,
)

from grassmarket.atlas.active import profile_scoring_context
from grassmarket.atlas.draft_coefficients import (
    draft_v1_coefficient_set,
    draft_wealth_coefficient_set,
)
from grassmarket.atlas.engine import score
from tests.test_atlas_engine_properties import build_inputs

_WEALTH_SUB_ADDITIONS = {
    "WEALTH_SUITABILITY",
    "WEALTH_CUSTODY_CASS",
    "WEALTH_MODEL_PORTFOLIOS",
    "WEALTH_PLANNING_TOOLS",
    "WEALTH_PLATFORM_RESILIENCE",
    "WEALTH_ADVICE_WORKFLOW",
}
_WEALTH_METRICS = {
    "WEALTH_AUM",
    "WEALTH_ADVISER_HEADCOUNT",
    "WEALTH_CLIENT_COUNT",
    "WEALTH_REVENUE_MARGIN_BPS",
    "WEALTH_COST_INCOME",
    "WEALTH_AUM_PER_ADVISER",
    "WEALTH_RECURRING_REV_PCT",
    "WEALTH_NET_NEW_MONEY_RATE",
    "WEALTH_AUM_GROWTH",
    "WEALTH_RETENTION",
}


def _wealth_view():
    return load_registry().for_profile(load_profile("wealth"))


def test_wealth_view_selects_advisory_modules_and_drops_brokerage_connectivity() -> None:
    view = _wealth_view()
    module_keys = {m.key for m in view.modules}
    # A wealth manager doesn't run exchange/broker member gateways or liquidity connectivity.
    assert "EMS_GATEWAY" not in module_keys
    assert "LIQ_CONNECT" not in module_keys
    assert {"CMS", "BACKOFFICE", "APP_SERVER"} <= module_keys
    assert _WEALTH_SUB_ADDITIONS <= view.all_subcomponent_keys()


def test_wealth_b_index_is_wealth_native_not_retail() -> None:
    view = _wealth_view()
    metric_keys = view.metric_keys()
    assert metric_keys == frozenset(_WEALTH_METRICS)
    # None of the retail superset metrics leak into a wealth assessment.
    assert "AUA" not in metric_keys and "TAKE_RATE_LEVEL" not in metric_keys
    # The superset itself is unchanged (golden master safe).
    assert "AUA" in load_registry().metric_keys()


def test_wealth_criticals_reflect_suitability_and_custody() -> None:
    view = _wealth_view()
    crit = {s.key: s.critical for m in view.modules for s in m.subcomponents}
    assert crit["WEALTH_SUITABILITY"] is True  # COBS 9A advice process
    assert crit["WEALTH_CUSTODY_CASS"] is True  # client-money protection
    assert crit["WEALTH_PLATFORM_RESILIENCE"] is True  # operational resilience


def test_wealth_infrastructure_is_wealth_native_not_retail() -> None:
    # GRS-0147d: the Infrastructure Deep Dive drops every retail subcomponent from the selected
    # modules and renames the modules for a wealth manager — no OEMS/watchlists/time-to-first-trade.
    r = load_registry()
    view = _wealth_view()
    retail_subs = {s.key for m in r.modules for s in m.subcomponents}
    assert not (view.all_subcomponent_keys() & retail_subs)  # zero retail leak
    names = {m.name for m in view.modules}
    assert "Custody, Settlement & CASS" in names
    assert "Portfolio Management & Dealing" in names
    assert "Client Management & Suitability" in names
    # The superset OEMS module still carries its retail subcomponents (golden master safe).
    oems = r.require_module("OEMS")
    assert len(oems.subcomponents) > 0 and not any(
        s.key.startswith("WEALTH_") for s in oems.subcomponents
    )


def test_wealth_coefficient_set_covers_the_wealth_view_exactly() -> None:
    view = _wealth_view()
    coeffs = draft_wealth_coefficient_set(view)
    coeffs.validate_against(view)  # exact coverage, fail-loud otherwise
    assert coeffs.critical_modules_for_l == ("APP_SERVER", "CMS", "BACKOFFICE")
    assert coeffs.client_usable is False  # draft until the wealth panel ratifies
    assert coeffs.version == "wealth-v1-draft-pending-elicitation"
    retail = draft_v1_coefficient_set(load_registry().for_profile(load_profile("retail")))
    assert coeffs.version != retail.version  # benchmark rows segment by profile, never pooled


def test_retail_coefficient_set_is_incompatible_with_the_wealth_view() -> None:
    # A wealth firm's B can never be silently scored with retail weights — the retail set's w_metric
    # doesn't cover the wealth metrics, so validate_against refuses (fail-loud, ADR-0001).
    wealth_view = _wealth_view()
    retail = draft_v1_coefficient_set(load_registry().for_profile(load_profile("retail")))
    with pytest.raises(
        RegistryError
    ):  # unknown retail metric keys / missing wealth keys — either way
        retail.validate_against(wealth_view)


def test_a_full_wealth_assessment_scores_end_to_end() -> None:
    view, coeffs = profile_scoring_context("wealth")
    result = score(build_inputs(view), coeffs, view)
    v = result.composite.v_index
    assert 0.0 <= v <= 1.0  # a real, bounded wealth V — the wealth firm is no longer mislabelled


def test_wealth_signed_metric_allows_a_net_outflow() -> None:
    # Net new money rate is legitimately negative in an outflow year — it must be a valid input, not
    # refused (GRS-0144 sign handling carried into the wealth set).
    view = _wealth_view()
    nnm = view.require_metric("WEALTH_NET_NEW_MONEY_RATE")
    assert nnm.min_raw is None
    assert nnm.domain_violation(-3) is None
    # A non-negative wealth magnitude still refuses a negative.
    assert view.require_metric("WEALTH_AUM").domain_violation(-1) is not None
