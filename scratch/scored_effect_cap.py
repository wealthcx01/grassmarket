"""Re-run the scored effect WITH the ADR-0038 critical-control cap wired into the segment sets."""

from __future__ import annotations

from bcap_contracts.common import MaturityLevel, StrengthRating
from bcap_contracts.registry import load_profile, load_registry

from grassmarket.atlas.draft_coefficients import (
    draft_exchange_coefficient_set,
    draft_wealth_coefficient_set,
)
from grassmarket.atlas.elicited_coefficients import (
    elicited_exchange_coefficient_set,
    elicited_wealth_coefficient_set,
)
from grassmarket.atlas.engine import score
from tests.test_atlas_engine_properties import build_inputs

_WIDE = (StrengthRating.WIDE, StrengthRating.WIDE)
_NONE = (StrengthRating.NONE, StrengthRating.NONE)


def _best_worst_metrics(view, *, best: bool) -> dict[str, float]:
    out: dict[str, float] = {}
    for m in view.metrics:
        anchors = m.normalisation.anchors
        pick = max(anchors, key=lambda a: a.normalised) if best else min(
            anchors, key=lambda a: a.normalised
        )
        out[m.key] = pick.raw
    return out


def _firms(view, criticals):
    all_wide = {p.key: _WIDE for p in view.powers}
    all_none = {p.key: _NONE for p in view.powers}
    broken = {s: MaturityLevel.BASIC for c in criticals for s in view.subcomponent_keys(c)}
    return {
        "Strong": dict(
            default_level=MaturityLevel.FRONTIER,
            powers=all_wide,
            metrics=_best_worst_metrics(view, best=True),
        ),
        "Strong-except-weak-critical": dict(
            default_level=MaturityLevel.FRONTIER,
            subs=broken,
            powers=all_wide,
            metrics=_best_worst_metrics(view, best=True),
        ),
        "Weak": dict(
            default_level=MaturityLevel.BASIC,
            powers=all_none,
            metrics=_best_worst_metrics(view, best=False),
        ),
    }


def run(name, profile, draft_fn, elicited_fn):
    view = load_registry().for_profile(load_profile(profile))
    draft = draft_fn(view)
    elicited = elicited_fn(view)
    criticals = elicited.critical_modules_for_l
    print(f"\n=== {name} (θ draft {draft.theta_b}/{draft.theta_p}/{draft.theta_l} "
          f"→ elicited {elicited.theta_b}/{elicited.theta_p}/{elicited.theta_l}, κ={elicited.critical_control_cap_floor}) ===")
    print(f"{'Firm':<30} {'Draft':>7} {'Elicited':>9} {'Δ':>7}   cap")
    for firm, kw in _firms(view, criticals).items():
        inp = build_inputs(view, **kw)
        d = score(inp, draft, view).v_display_0_100
        er = score(inp, elicited, view)
        e = er.v_display_0_100
        cap = er.critical_control_cap
        capnote = ""
        if cap and cap.bound:
            capnote = f"CAPPED {cap.v_uncapped*100:.1f}→{cap.cap*100:.1f} ({cap.binding_module})"
        elif cap:
            capnote = f"cap {cap.cap*100:.0f} (slack)"
        print(f"{firm:<30} {d:>7.1f} {e:>9.1f} {e-d:>+7.1f}   {capnote}")


run("WEALTH", "wealth", draft_wealth_coefficient_set, elicited_wealth_coefficient_set)
run("EXCHANGE", "exchange", draft_exchange_coefficient_set, elicited_exchange_coefficient_set)
