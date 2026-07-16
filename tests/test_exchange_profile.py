"""GRS-0078 — the exchange operating-model profile (ADR-0025). An exchange scores over the exchange
module set (matching engine, surveillance, member connectivity, clearing/settlement, data
distribution) via the GRS-0077 profile view — WITHOUT N/A-stretching the retail taxonomy — and its
draft coefficient set carries the exchange criticals. Retail is untouched (golden master), and
the two profiles' coefficient sets are mutually incompatible, so an exchange's L can never be
silently pooled with a broker's."""

from __future__ import annotations

import pytest
from bcap_contracts.registry import (
    MissingKeyError,
    UnknownKeyError,
    load_profile,
    load_registry,
)

from grassmarket.atlas.active import profile_scoring_context
from grassmarket.atlas.draft_coefficients import (
    draft_exchange_coefficient_set,
    draft_v1_coefficient_set,
)
from grassmarket.atlas.engine import score
from tests.test_atlas_engine_properties import build_inputs

_EXCHANGE_ADDITIONS = {
    "OEMS_MATCHING_ENGINE",
    "BACKOFFICE_MARKET_SURVEILLANCE",
    "EMS_GATEWAY_MEMBER_CONNECTIVITY",
    "LIQ_CONNECT_CLEARING_SETTLEMENT_IF",
    "MARKET_DATA_DISTRIBUTION",
}


def _exchange_view():
    return load_registry().for_profile(load_profile("exchange"))


def test_exchange_view_selects_market_infra_and_not_the_retail_cms() -> None:
    view = _exchange_view()
    module_keys = {m.key for m in view.modules}
    assert "CMS" not in module_keys  # retail client-management system is not an exchange concern
    sub_keys = view.all_subcomponent_keys()
    assert _EXCHANGE_ADDITIONS <= sub_keys  # the market-infra subcomponents are present
    # No retail-only CMS subcomponent leaks into the exchange run.
    assert not any(k.startswith("CMS_") for k in sub_keys)


def test_exchange_criticals_reflect_market_infrastructure() -> None:
    view = _exchange_view()
    crit = {s.key: s.critical for m in view.modules for s in m.subcomponents}
    assert crit["OEMS_MATCHING_ENGINE"] is True  # the heart of an exchange
    assert crit["BACKOFFICE_MARKET_SURVEILLANCE"] is True  # regulatory imperative
    # A broker's pre-trade risk gate is overridden non-critical for the exchange.
    assert crit["OEMS_PRE_TRADE_RISK"] is False


def test_exchange_coefficient_set_covers_the_exchange_view_exactly() -> None:
    view = _exchange_view()
    coeffs = draft_exchange_coefficient_set(view)
    coeffs.validate_against(view)  # exact coverage, fail-loud otherwise
    assert coeffs.critical_modules_for_l == ("APP_SERVER", "OEMS", "LIQ_CONNECT")
    assert coeffs.client_usable is False  # draft until the exchange panel ratifies
    # A DISTINCT coefficient_version → benchmark rows are segmentable by profile (never pooled with
    # retail; a benchmark comparison filters on it — GRS-0084).
    assert coeffs.version == "exchange-v1-draft-pending-elicitation"
    assert coeffs.version != draft_v1_coefficient_set(load_registry().for_profile(
        load_profile("retail")
    )).version


def test_an_exchange_assessment_scores_over_the_exchange_module_set() -> None:
    view, coeffs = profile_scoring_context("exchange")
    result = score(build_inputs(view), coeffs, view)
    assert result.composite.v_index is not None  # a real V over the exchange taxonomy
    # The scored modules are the exchange set, not the retail one.
    scored_modules = {m.key for m in result.modules}
    assert "CMS" not in scored_modules and "OEMS" in scored_modules


def test_profiles_are_not_pooled_the_coeff_sets_are_mutually_incompatible() -> None:
    r = load_registry()
    retail_view = r.for_profile(load_profile("retail"))
    exchange_view = _exchange_view()
    exchange_coeffs = draft_exchange_coefficient_set(exchange_view)
    retail_coeffs = draft_v1_coefficient_set(retail_view)
    # An exchange coefficient set cannot validate against the retail view, or vice versa — so an
    # exchange's L can never be silently scored/pooled under a broker's coefficients (ADR-0025).
    with pytest.raises((UnknownKeyError, MissingKeyError)):
        exchange_coeffs.validate_against(retail_view)
    with pytest.raises((UnknownKeyError, MissingKeyError)):
        retail_coeffs.validate_against(exchange_view)


def test_retail_is_unchanged_by_the_exchange_profile() -> None:
    # Adding the exchange profile must not alter retail — its view still selects all 9 modules, no
    # exchange addition leaks in.
    retail_view = load_registry().for_profile(load_profile("retail"))
    assert len(retail_view.modules) == 9
    assert not (_EXCHANGE_ADDITIONS & retail_view.all_subcomponent_keys())


def test_unknown_profile_still_fails_loud() -> None:
    with pytest.raises(UnknownKeyError):
        profile_scoring_context("not_a_profile")
