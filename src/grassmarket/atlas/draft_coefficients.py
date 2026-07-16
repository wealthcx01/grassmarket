"""The v1 DRAFT coefficient set — uniform placeholders, NOT client-usable.

Every weight here is a documented uniform placeholder pending the weight-elicitation panel (swing
weighting + Delphi, Methodology §6). It is `client_usable=False` and its provenance is marked
draft-pending-elicitation: loadable so the engine and its tests have a complete, registry-covering
coefficient set to run against, but it must never price a client deliverable. When the panel
ratifies θ/α/λ/δ/W_g and the strength encoding, they replace this set (ADR-0004, ADR-0006).

The values mirror the ratified golden-master fixture's draft coefficients so the engine reproduces
Meridian exactly: θ = (0.30, 0.30, 0.40), α = 0.7, uniform λ/δ/w, group weights 1/3 each, and the
ADR-0004 strength encoding. Dates are fixed constants (the engine is pure — no clock).
"""

from __future__ import annotations

from datetime import date

from bcap_contracts.assessments import CoefficientSet
from bcap_contracts.common import WeightMethod
from bcap_contracts.provenance import WeightProvenanceRecord
from bcap_contracts.registry import Registry

# The draft's critical-for-L modules (brokerage core) — a ratified draft judgement (GRS-0003).
_CRITICAL_MODULES_FOR_L = ("APP_SERVER", "BACKOFFICE", "OEMS")
# The exchange profile's critical-for-L modules (ADR-0025/GRS-0078): the platform, the matching
# engine (OEMS in the exchange view), and clearing/settlement (LIQ_CONNECT). DRAFT — the exchange
# panel refines these; provenance stays draft-pending-elicitation.
_EXCHANGE_CRITICAL_MODULES_FOR_L = ("APP_SERVER", "OEMS", "LIQ_CONNECT")

# The draft's critical-for-C modules (ADR-0023): the customer-facing core — first-trade onboarding,
# the trading experience, and security/regulation (trust). A ratified DRAFT judgement; the θ_C panel
# (post-launch, ADR-0023 I-4) refines these. Provenance stays draft-pending-elicitation.
_CRITICAL_MODULES_FOR_C = (
    "CUST_ONBOARDING",
    "CUST_TRADING_EXPERIENCE",
    "CUST_SECURITY_REGULATION",
)

_STRENGTH_ENCODING = {"None": 0.0, "Emerging": 0.4, "Established": 0.7, "Wide": 1.0}

_DRAFT_PROVENANCE = WeightProvenanceRecord(
    set_by="draft-pending-elicitation",
    set_on=date(2026, 7, 4),
    # DIRECT: these are uniform structural PLACEHOLDERS, not elicited weights — flagged so no one
    # mistakes them for panel output (Methodology §6; WeightMethod.DIRECT note).
    method=WeightMethod.DIRECT,
    dispersion="n/a — uniform draft placeholder",
    review_due=date(2026, 12, 31),
    notes="Uniform draft pending the swing-weighting/Delphi panel; NOT client-usable.",
)

_PROVENANCE_FAMILIES = (
    "theta",
    "alpha_l",
    "alpha_module",
    "lambda",
    "delta",
    "w_power",
    "w_metric",
    "group_weights",
    "strength_encoding",
)


# The DRAFT v1.4 four-index θ split (ADR-0023 Stage 2). PLACEHOLDER, not θ_C-panel output — the
# v1.1 0.30/0.30/0.40 is re-split to carve out θ_C, documented draft-pending-elicitation. The
# four weights are re-elicited TOGETHER by the θ_C panel (ADR-0023 §4); I-4 launch defaults are
# explicitly NOT a basis for a headline-weight change, so any v1.4 set here is client_usable=False.
_V1_4_THETA = (0.25, 0.25, 0.35)  # θ_B, θ_P, θ_L
_V1_4_THETA_C = 0.15


def draft_v1_coefficient_set(
    registry: Registry,
    *,
    version: str = "v1-draft-pending-elicitation",
    methodology_version: str = "1.1",
    critical_modules_for_l: tuple[str, ...] = _CRITICAL_MODULES_FOR_L,
    theta: tuple[float, float, float] = (0.30, 0.30, 0.40),
    theta_c: float | None = None,
    score_c: bool = False,
    critical_modules_for_c: tuple[str, ...] = _CRITICAL_MODULES_FOR_C,
) -> CoefficientSet:
    """Build the uniform draft coefficient set that covers ``registry`` exactly (ADR-0001).

    Fully-qualified subcomponent keys come straight from the registry (GRS-0002a), so λ can never
    drift from the real key set. Raises via ``CoefficientSet`` construction / ``validate_against``
    if the registry is somehow not coverable — it never silently produces a partial set. The
    ``critical_modules_for_l`` and ``version`` are parameterised so an operating-model profile
    (ADR-0025) can supply its own critical-for-L set over its registry VIEW; the retail defaults
    reproduce the golden master byte-identically.

    ``score_c`` opts into the C-index coefficients (ADR-0023 Stage 1): uniform α_C/λ_c/δ_c
    placeholders over the registry's C dimension, reusing the same draft provenance. Default False —
    a set without C scores B/P/L exactly as before, so the golden master is untouched.

    ``theta``/``theta_c``/``methodology_version`` parameterise the headline weights: the default
    three-index v1.1 (θ_C absent) reproduces the golden master; a v1.4 four-index set passes a
    re-split θ + θ_C (ADR-0023 Stage 2). ``theta_c`` requires ``score_c`` (contract-enforced).
    """
    groups = sorted({m.group for m in registry.metrics if m.group is not None})
    c_kwargs: dict[str, object] = {}
    if score_c:
        c_kwargs = {
            "alpha_c": 0.7,
            "alpha_c_module": {k: 0.7 for k in registry.c_module_keys()},
            "lambda_c_loadings": {
                k: {s: 1.0 for s in registry.c_subcomponent_keys(k)}
                for k in registry.c_module_keys()
            },
            "delta_c": {k: 1.0 for k in registry.c_module_keys()},
            "critical_modules_for_c": critical_modules_for_c,
        }
    provenance_families = _PROVENANCE_FAMILIES + (
        ("alpha_c", "alpha_c_module", "lambda_c", "delta_c") if score_c else ()
    )
    cs = CoefficientSet(
        version=version,
        methodology_version=methodology_version,
        theta_b=theta[0],
        theta_p=theta[1],
        theta_l=theta[2],
        theta_c=theta_c,
        alpha_l=0.7,
        alpha_module={k: 0.7 for k in registry.module_keys()},
        lambda_loadings={
            k: {s: 1.0 for s in registry.subcomponent_keys(k)} for k in registry.module_keys()
        },
        delta={k: 1.0 for k in registry.module_keys()},
        critical_modules_for_l=critical_modules_for_l,
        w_power={k: 1.0 for k in registry.power_keys()},
        w_metric={k: 1.0 for k in registry.metric_keys()},
        group_weights={g: 1.0 for g in groups},
        strength_encoding=dict(_STRENGTH_ENCODING),
        client_usable=False,
        provenance={family: _DRAFT_PROVENANCE for family in provenance_families},
        **c_kwargs,  # type: ignore[arg-type]
    )
    cs.validate_against(registry)  # fail loud now, not at score time
    return cs


def draft_v1_4_coefficient_set(registry: Registry) -> CoefficientSet:
    """The DRAFT four-index coefficient set (ADR-0023 Stage 2 / Methodology v1.4): folds C into V as
    ``V = θ_B·B + θ_P·P + θ_L·L + θ_C·C``. The θ split is a documented PLACEHOLDER re-split of the
    v1.1 weights — NOT θ_C-panel output — so it is `client_usable=False`: it never prices a client
    deliverable. Activating the four-index V for the live/client path is the single-point flip in
    `active.py`, gated on the real θ_C elicitation panel (ADR-0023 §4 / §Gating)."""
    return draft_v1_coefficient_set(
        registry,
        version="v1.4-draft-pending-theta-c-panel",
        methodology_version="1.4",
        theta=_V1_4_THETA,
        theta_c=_V1_4_THETA_C,
        score_c=True,
    )


def draft_exchange_coefficient_set(registry: Registry) -> CoefficientSet:
    """The DRAFT exchange-profile coefficient set (ADR-0025 / GRS-0078). Covers the exchange
    VIEW exactly, with the exchange critical-for-L modules. `client_usable=False` — the exchange
    weight-elicitation panel replaces this (same activation seam as retail)."""
    return draft_v1_coefficient_set(
        registry,
        version="exchange-v1-draft-pending-elicitation",
        critical_modules_for_l=_EXCHANGE_CRITICAL_MODULES_FOR_L,
    )
