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


def draft_v1_coefficient_set(
    registry: Registry,
    *,
    version: str = "v1-draft-pending-elicitation",
    critical_modules_for_l: tuple[str, ...] = _CRITICAL_MODULES_FOR_L,
) -> CoefficientSet:
    """Build the uniform draft coefficient set that covers ``registry`` exactly (ADR-0001).

    Fully-qualified subcomponent keys come straight from the registry (GRS-0002a), so λ can never
    drift from the real key set. Raises via ``CoefficientSet`` construction / ``validate_against``
    if the registry is somehow not coverable — it never silently produces a partial set. The
    ``critical_modules_for_l`` and ``version`` are parameterised so an operating-model profile
    (ADR-0025) can supply its own critical-for-L set over its registry VIEW; the retail defaults
    reproduce the golden master byte-identically.
    """
    groups = sorted({m.group for m in registry.metrics if m.group is not None})
    cs = CoefficientSet(
        version=version,
        methodology_version="1.1",
        theta_b=0.30,
        theta_p=0.30,
        theta_l=0.40,
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
        provenance={family: _DRAFT_PROVENANCE for family in _PROVENANCE_FAMILIES},
    )
    cs.validate_against(registry)  # fail loud now, not at score time
    return cs


def draft_exchange_coefficient_set(registry: Registry) -> CoefficientSet:
    """The DRAFT exchange-profile coefficient set (ADR-0025 / GRS-0078). Covers the exchange
    VIEW exactly, with the exchange critical-for-L modules. `client_usable=False` — the exchange
    weight-elicitation panel replaces this (same activation seam as retail)."""
    return draft_v1_coefficient_set(
        registry,
        version="exchange-v1-draft-pending-elicitation",
        critical_modules_for_l=_EXCHANGE_CRITICAL_MODULES_FOR_L,
    )
