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


# --- Segment starter sets (GRS-0150, ADR-0037) -------------------------------------------
#
# STARTER elicited sets for the wealth & exchange profiles. These are an ENGINEERING PROPOSAL,
# refined by the ADR-0037 deep-research validation (cited in docs/elicitation/), *pending founder +
# panel ratification*. They are `client_usable=True` structurally (like the retail elicited set) but
# are NOT the active default — `active.profile_scoring_context` still routes both profiles to their
# DRAFT sets, so the "indicative, not client-usable" banner and the client-pack gate are unchanged.
# Activation is the single recorded flip in `profile_scoring_context` on the founder's sign-off
# (ADR-0022). Values are relative weights (the engine normalises).

_STARTER_SET_ON = date(2026, 7, 20)
_STARTER_REVIEW_DUE = date(2027, 7, 20)


def _starter_prov(method: WeightMethod, dispersion: str) -> WeightProvenanceRecord:
    return WeightProvenanceRecord(
        set_by="engineering-starter-research-validated-2026-07",
        set_on=_STARTER_SET_ON,
        method=method,
        dispersion=dispersion,
        review_due=_STARTER_REVIEW_DUE,
        notes="ADR-0037 research-validated STARTER; PENDING founder + panel ratification.",
    )


def _weighted(keys, weights: dict[str, float]) -> dict[str, float]:
    """Map the view's actual keys to their weights (default 1.0 for any key not listed)."""
    return {k: float(weights.get(k, 1.0)) for k in keys}


# Wealth (research: franchise economics lead; momentum leads B; advice-governance is critical).
_WEALTH_CRITICAL_MODULES_FOR_L = ("APP_SERVER", "CMS", "BACKOFFICE", "ORCHESTRATION")
_WEALTH_DELTA = {
    "BACKOFFICE": 1.5,  # Custody, Settlement & CASS — existential (SAR)
    "CMS": 1.4,  # Client Management & Suitability (COBS 9A)
    "ORCHESTRATION": 1.3,  # Advice Workflow & Investment Governance — nine-figure redress source
    "APP_SERVER": 1.2,  # Platform & AUM Economics
    "OEMS": 1.1,  # Portfolio Management & Dealing
    "FRONTEND": 0.8,  # Client Portal & Planning
    "MARKET_DATA": 0.7,  # Investment Data & Research
}
_WEALTH_GROUP_WEIGHTS = {"momentum": 1.3, "unit_economics": 1.2, "scale": 1.0}
_WEALTH_W_METRIC = {
    "WEALTH_AUM": 1.5,
    "WEALTH_ADVISER_HEADCOUNT": 1.0,
    "WEALTH_CLIENT_COUNT": 0.8,
    "WEALTH_REVENUE_MARGIN_BPS": 1.3,
    "WEALTH_COST_INCOME": 1.2,
    "WEALTH_AUM_PER_ADVISER": 1.0,
    "WEALTH_RECURRING_REV_PCT": 1.0,
    "WEALTH_NET_NEW_MONEY_RATE": 1.5,
    "WEALTH_RETENTION": 1.2,
    "WEALTH_AUM_GROWTH": 0.8,
}
_WEALTH_W_POWER = {
    "SWITCHING_COSTS": 1.5,
    "BRANDING": 1.4,
    "SCALE_ECONOMIES": 1.2,
    "PROCESS_POWER": 0.9,
    "CORNERED_RESOURCE": 0.9,
    "COUNTER_POSITIONING": 0.8,
    "NETWORK_ECONOMIES": 0.7,
}

# Exchange (research: infra + network moat; recurring de-risks volume; surveillance is critical).
_EXCHANGE_CRITICAL_MODULES_FOR_L = ("APP_SERVER", "OEMS", "LIQ_CONNECT", "BACKOFFICE")
_EXCHANGE_DELTA = {
    "OEMS": 1.4,  # Matching Engine
    "APP_SERVER": 1.4,  # Core Trading Platform (uptime/resilience)
    "LIQ_CONNECT": 1.4,  # Clearing & Settlement (the most systemic node — CCP)
    "BACKOFFICE": 1.1,  # Post-Trade & Surveillance
    "MARKET_DATA": 1.0,  # Market-Data Dissemination
    "EMS_GATEWAY": 0.9,  # Member Connectivity
    "ORCHESTRATION": 0.8,  # Trading Operations & Controls
    "FRONTEND": 0.6,  # Member Front-End & APIs
}
_EXCHANGE_GROUP_WEIGHTS = {"scale": 1.2, "unit_economics": 1.15, "momentum": 0.9}
_EXCHANGE_W_METRIC = {
    "EXCH_ADV": 1.4,
    "EXCH_DATA_REVENUE": 1.3,
    "EXCH_OPEN_INTEREST": 1.2,
    "EXCH_IPOS_WON": 0.8,
    "EXCH_EBITDA_MARGIN": 1.3,
    "EXCH_TAKE_RATE": 1.2,
    "EXCH_RECURRING_REV_PCT": 1.3,
    "EXCH_NET_REVENUE_GROWTH": 1.2,
    "EXCH_VOLUME_GROWTH": 0.8,
}
_EXCHANGE_W_POWER = {
    "NETWORK_ECONOMIES": 1.6,
    "SWITCHING_COSTS": 1.4,
    "CORNERED_RESOURCE": 1.3,
    "SCALE_ECONOMIES": 1.2,
    "PROCESS_POWER": 0.9,
    "COUNTER_POSITIONING": 0.8,
    "BRANDING": 0.7,
}


def _elicited_segment_set(
    registry: Registry,
    *,
    version: str,
    theta: tuple[float, float, float],
    alpha_l: float,
    critical_modules_for_l: tuple[str, ...],
    delta: dict[str, float],
    group_weights: dict[str, float],
    w_metric: dict[str, float],
    w_power: dict[str, float],
) -> CoefficientSet:
    """Build a client-usable STARTER elicited set covering the profile VIEW exactly (ADR-0037). Same
    shape as ``elicited_v1_coefficient_set``; non-uniform δ/w_metric/w_power/group_weights from the
    research validation. NOT wired active — activation is a recorded flip (ADR-0022)."""
    groups = sorted({m.group for m in registry.metrics if m.group is not None})
    cs = CoefficientSet(
        version=version,
        methodology_version="1.1",
        theta_b=theta[0],
        theta_p=theta[1],
        theta_l=theta[2],
        alpha_l=alpha_l,
        alpha_module={k: 0.75 for k in registry.module_keys()},
        lambda_loadings={
            k: {s: 1.0 for s in registry.subcomponent_keys(k)} for k in registry.module_keys()
        },
        delta=_weighted(registry.module_keys(), delta),
        critical_modules_for_l=critical_modules_for_l,
        w_power=_weighted(registry.power_keys(), w_power),
        w_metric=_weighted(registry.metric_keys(), w_metric),
        group_weights={g: float(group_weights.get(g, 1.0)) for g in groups},
        strength_encoding=dict(_STRENGTH_ENCODING),
        client_usable=True,
        provenance={
            "theta": _starter_prov(WeightMethod.SWING_WEIGHTING, "starter — research-refined"),
            "alpha_l": _starter_prov(WeightMethod.SWING_WEIGHTING, "starter"),
            "alpha_module": _starter_prov(WeightMethod.SWING_WEIGHTING, "starter"),
            "lambda": _starter_prov(WeightMethod.AHP, "starter — uniform"),
            "delta": _starter_prov(WeightMethod.AHP, "starter — research-refined"),
            "w_power": _starter_prov(WeightMethod.SWING_WEIGHTING, "starter — research-refined"),
            "w_metric": _starter_prov(WeightMethod.SWING_WEIGHTING, "starter — research-refined"),
            "group_weights": _starter_prov(
                WeightMethod.SWING_WEIGHTING, "starter — research-refined"
            ),
            "strength_encoding": _starter_prov(WeightMethod.DELPHI, "convex maturity curve"),
        },
    )
    cs.validate_against(registry)  # fail loud now, not at score time
    return cs


def elicited_wealth_coefficient_set(registry: Registry) -> CoefficientSet:
    """STARTER client-usable wealth set (ADR-0037, GRS-0150) — research-refined, NOT yet active."""
    return _elicited_segment_set(
        registry,
        version="wealth-v1-elicited-starter-2026",
        theta=(0.45, 0.30, 0.25),  # franchise economics lead; L trimmed (hygiene, priced into B)
        alpha_l=0.75,
        critical_modules_for_l=_WEALTH_CRITICAL_MODULES_FOR_L,
        delta=_WEALTH_DELTA,
        group_weights=_WEALTH_GROUP_WEIGHTS,
        w_metric=_WEALTH_W_METRIC,
        w_power=_WEALTH_W_POWER,
    )


def elicited_exchange_coefficient_set(registry: Registry) -> CoefficientSet:
    """STARTER client-usable exchange set (ADR-0037) — research-refined, not yet active."""
    return _elicited_segment_set(
        registry,
        version="exchange-v1-elicited-starter-2026",
        theta=(0.30, 0.37, 0.33),  # moat (P) is the top term; B up (volume ~half of revenue)
        alpha_l=0.80,
        critical_modules_for_l=_EXCHANGE_CRITICAL_MODULES_FOR_L,
        delta=_EXCHANGE_DELTA,
        group_weights=_EXCHANGE_GROUP_WEIGHTS,
        w_metric=_EXCHANGE_W_METRIC,
        w_power=_EXCHANGE_W_POWER,
    )
