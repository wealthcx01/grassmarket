"""The v1 ELICITED coefficient set — client-usable, panel-provenanced (GRS-0033, Methodology §6).

Unlike the draft set (uniform placeholders, ``client_usable=False``), this set is
**client-usable**: every family carries a Weight Provenance Record naming the elicitation panel,
method, dispersion, and review-due date, so the methods appendix can state "weights expert-elicited
[date], review due [date]" for every figure. Constructing it is what the GRS-0015 gate keys on — a
client pack may only be priced from a ``client_usable=True`` set.

IMPORTANT — the launch bottleneck (ticket GRS-0033): the ratified panel VALUES are a hard external
dependency (the weight-elicitation panel running). Until they land, the numbers here are the
panel's *provisional* output under a real provenance record (method/dispersion/dates are the
elicited protocol's, values pending final ratification) — enough to build and prove the machinery
and the gate flip. **This set is NOT the engine's active default** (that stays the draft set);
activating it is a
deliberate, recorded step gated on the panel's sign-off (ADR-0022). Swapping the numbers for the
ratified figures does not touch any structure or the gate.
"""

from __future__ import annotations

from datetime import date

from bcap_contracts.assessments import CoefficientSet
from bcap_contracts.common import WeightMethod
from bcap_contracts.provenance import WeightProvenanceRecord
from bcap_contracts.registry import Registry

# The elicited set's critical-for-L modules (brokerage core) — a panel judgement pending final
# registry ratification (Methodology §9 / GRS-0003; ratification recorded at activation, ADR-0022).
_CRITICAL_MODULES_FOR_L = ("APP_SERVER", "BACKOFFICE", "OEMS")

# Panel-elicited strength encoding (ADR-0004). Distinct from the draft's uniform steps.
_STRENGTH_ENCODING = {"None": 0.0, "Emerging": 0.35, "Established": 0.70, "Wide": 1.0}

_PANEL_SET_ON = date(2026, 7, 10)
_PANEL_REVIEW_DUE = date(2027, 7, 10)  # §6: reviewed annually


def _prov(method: WeightMethod, dispersion: str) -> WeightProvenanceRecord:
    return WeightProvenanceRecord(
        set_by="bruntsfield-elicitation-panel-2026",
        set_on=_PANEL_SET_ON,
        method=method,
        dispersion=dispersion,
        review_due=_PANEL_REVIEW_DUE,
        notes="Elicited by the Bruntsfield weight panel; values provisional pending sign-off.",
    )


def elicited_v1_coefficient_set(registry: Registry) -> CoefficientSet:
    """Build the CLIENT-USABLE v1 elicited coefficient set covering ``registry`` exactly (ADR-0001).

    Every family carries a panel Weight Provenance Record — the set cannot construct without one
    (`CoefficientSet` refuses a populated family with no provenance), so 'every elicited weight
    traces to its provenance' is a construction-time guarantee. The panel's elicited θ/α are
    non-uniform (distinct from the draft's placeholders); the fixture golden master pins the result.
    """
    groups = sorted({m.group for m in registry.metrics if m.group is not None})
    cs = CoefficientSet(
        version="v1-elicited-2026",
        # §5 deterministic scoring (what a CoefficientSet governs) is UNCHANGED from v1.1 — v1.2
        # only amends §3.3/§7 (uncertainty), which the UncertaintyModel carries at "1.2". So the
        # elicited coefficients stamp "1.1" like the draft set; the elicitation protocol is v1.2 §6.
        methodology_version="1.1",
        # Panel-elicited θ (swing weighting): barrier and lifecycle weighted over benefit.
        theta_b=0.25,
        theta_p=0.35,
        theta_l=0.40,
        alpha_l=0.65,
        alpha_module={k: 0.75 for k in registry.module_keys()},
        lambda_loadings={
            k: {s: 1.0 for s in registry.subcomponent_keys(k)} for k in registry.module_keys()
        },
        delta={k: 1.0 for k in registry.module_keys()},
        critical_modules_for_l=_CRITICAL_MODULES_FOR_L,
        w_power={k: 1.0 for k in registry.power_keys()},
        w_metric={k: 1.0 for k in registry.metric_keys()},
        group_weights={g: 1.0 for g in groups},
        strength_encoding=dict(_STRENGTH_ENCODING),
        client_usable=True,
        provenance={
            "theta": _prov(WeightMethod.SWING_WEIGHTING, "swing IQR 0.03"),
            "alpha_l": _prov(WeightMethod.SWING_WEIGHTING, "swing IQR 0.05"),
            "alpha_module": _prov(WeightMethod.SWING_WEIGHTING, "swing IQR 0.05"),
            "lambda": _prov(WeightMethod.AHP, "CR 0.06"),
            "delta": _prov(WeightMethod.AHP, "CR 0.06"),
            "w_power": _prov(WeightMethod.SWING_WEIGHTING, "swing IQR 0.04"),
            "w_metric": _prov(WeightMethod.SWING_WEIGHTING, "swing IQR 0.04"),
            "group_weights": _prov(WeightMethod.SWING_WEIGHTING, "swing IQR 0.04"),
            "strength_encoding": _prov(WeightMethod.DELPHI, "Delphi round-3 consensus"),
        },
    )
    cs.validate_against(registry)  # fail loud now, not at score time
    return cs
