"""The critical-control cap (ADR-0038, GRS-0151).

V ≤ κ + (1−κ)·min(q_m over critical-for-L modules): a hard operational-maturity guardrail so a
broken critical control (a CASS/custody failure for wealth, a clearing failure for an exchange)
cannot be out-weighted by a trimmed θ_L. Guarantees under test:

1. A set with NO cap floor (retail draft, every three-index set) reports `critical_control_cap =
   None` and V is byte-identical — the cap is opt-in and the golden master is untouched.
2. On the segment starter sets, a firm strong everywhere EXCEPT a critical control is ceiling'd to
   the cap, and the cap descends with the weakest critical module (κ=0.5, Basic q_m=0.2 ⇒ cap 0.6).
3. The cap only ever LOWERS V (V = min(uncapped, cap)) and is monotone (raising the broken control
   raises V) — the §monotonicity property survives.
4. A cap floor with no critical modules, or with no provenance record, refuses to construct.
"""

from __future__ import annotations

import pytest
from bcap_contracts.assessments import CoefficientSet
from bcap_contracts.common import MaturityLevel, StrengthRating
from bcap_contracts.registry import Registry, load_profile, load_registry
from pydantic import ValidationError

from grassmarket.atlas.draft_coefficients import draft_v1_coefficient_set
from grassmarket.atlas.elicited_coefficients import (
    _WEALTH_CRITICAL_MODULES_FOR_L,
    elicited_exchange_coefficient_set,
    elicited_wealth_coefficient_set,
)
from grassmarket.atlas.engine import score
from tests.test_atlas_engine_properties import build_inputs

_WIDE = (StrengthRating.WIDE, StrengthRating.WIDE)


def _wealth_view() -> Registry:
    return load_registry().for_profile(load_profile("wealth"))


def _all_wide(view: Registry) -> dict[str, tuple[StrengthRating, StrengthRating]]:
    return {p.key: _WIDE for p in view.powers}


def _broken_critical_subs(view: Registry, criticals: tuple[str, ...]) -> dict[str, MaturityLevel]:
    """Every subcomponent of the critical-for-L modules at Basic (a broken control)."""
    return {s: MaturityLevel.BASIC for m in criticals for s in view.subcomponent_keys(m)}


# --- 1. No cap floor ⇒ no cap, V untouched -----------------------------------------------


def test_retail_set_carries_no_cap_and_reports_none() -> None:
    r = load_registry()
    result = score(build_inputs(r), draft_v1_coefficient_set(r), r)
    assert result.critical_control_cap is None  # opt-in; golden-master path unaffected


# --- 2. The cap binds on a broken critical control ---------------------------------------


def test_cap_binds_and_ceilings_v_on_a_broken_wealth_critical() -> None:
    view = _wealth_view()
    cs = elicited_wealth_coefficient_set(view)
    inputs = build_inputs(
        view,
        default_level=MaturityLevel.FRONTIER,  # strong everywhere...
        subs=_broken_critical_subs(view, _WEALTH_CRITICAL_MODULES_FOR_L),  # ...except the criticals
        powers=_all_wide(view),
    )
    result = score(inputs, cs, view)
    cap = result.critical_control_cap
    assert cap is not None
    assert cap.floor == pytest.approx(0.5)
    assert cap.l_min_critical == pytest.approx(0.2)  # a fully-Basic critical module → q_m = 0.2
    assert cap.cap == pytest.approx(0.6)  # 0.5 + 0.5·0.2
    assert cap.binding_module in _WEALTH_CRITICAL_MODULES_FOR_L
    # A Wide-power, all-Frontier firm scores well above 0.6 uncapped — the cap must bite.
    assert cap.v_uncapped > cap.cap
    assert cap.bound is True
    assert result.composite.v_index == pytest.approx(cap.cap)


def test_cap_present_but_does_not_bind_when_criticals_are_strong() -> None:
    view = _wealth_view()
    cs = elicited_wealth_coefficient_set(view)
    result = score(
        build_inputs(view, default_level=MaturityLevel.FRONTIER, powers=_all_wide(view)), cs, view
    )
    cap = result.critical_control_cap
    assert cap is not None
    assert cap.l_min_critical == pytest.approx(1.0)  # all criticals Frontier
    assert cap.cap == pytest.approx(1.0)  # cap relaxes fully
    assert cap.bound is False
    assert result.composite.v_index == pytest.approx(cap.v_uncapped)


def test_exchange_cap_binds_on_a_broken_clearing_control() -> None:
    view = load_registry().for_profile(load_profile("exchange"))
    cs = elicited_exchange_coefficient_set(view)
    criticals = cs.critical_modules_for_l
    result = score(
        build_inputs(
            view,
            default_level=MaturityLevel.FRONTIER,
            subs=_broken_critical_subs(view, criticals),
            powers=_all_wide(view),
        ),
        cs,
        view,
    )
    cap = result.critical_control_cap
    assert cap is not None and cap.bound is True
    assert cap.cap == pytest.approx(0.6)
    assert result.composite.v_index == pytest.approx(0.6)


# --- 3. The cap only lowers V and is monotone --------------------------------------------


def test_v_equals_min_of_uncapped_and_cap_always() -> None:
    view = _wealth_view()
    cs = elicited_wealth_coefficient_set(view)
    # Sweep the critical control from Basic up to Frontier; V is always min(uncapped, cap).
    for level in (MaturityLevel.BASIC, MaturityLevel.DEVELOPING, MaturityLevel.ADVANCED):
        subs = {s: level for m in _WEALTH_CRITICAL_MODULES_FOR_L for s in view.subcomponent_keys(m)}
        result = score(
            build_inputs(view, default_level=MaturityLevel.FRONTIER, subs=subs), cs, view
        )
        cap = result.critical_control_cap
        assert cap is not None
        assert result.composite.v_index == pytest.approx(min(cap.v_uncapped, cap.cap))


def test_raising_a_broken_critical_raises_v_through_the_cap() -> None:
    view = _wealth_view()
    cs = elicited_wealth_coefficient_set(view)

    def v_at(level: MaturityLevel) -> float:
        subs = {s: level for m in _WEALTH_CRITICAL_MODULES_FOR_L for s in view.subcomponent_keys(m)}
        return score(
            build_inputs(view, default_level=MaturityLevel.FRONTIER, subs=subs), cs, view
        ).composite.v_index

    basic, developing, frontier = (
        v_at(MaturityLevel.BASIC),
        v_at(MaturityLevel.DEVELOPING),
        v_at(MaturityLevel.FRONTIER),
    )
    assert developing >= basic - 1e-12
    assert frontier >= developing - 1e-12
    assert frontier > basic  # the cap genuinely relaxes as the control is fixed


# --- 4. Construction invariants ----------------------------------------------------------


def test_cap_floor_without_critical_modules_refuses_construction() -> None:
    view = _wealth_view()
    payload = elicited_wealth_coefficient_set(view).model_dump()
    payload["critical_modules_for_l"] = []  # a cap with nothing to descend with
    with pytest.raises(ValidationError, match="no critical control"):
        CoefficientSet.model_validate(payload)


def test_cap_floor_without_provenance_refuses_construction() -> None:
    view = _wealth_view()
    cs = elicited_wealth_coefficient_set(view)
    payload = cs.model_dump()
    payload["provenance"] = {
        k: v.model_dump() for k, v in cs.provenance.items() if k != "critical_control_cap"
    }
    with pytest.raises(ValidationError, match="critical_control_cap"):
        CoefficientSet.model_validate(payload)
