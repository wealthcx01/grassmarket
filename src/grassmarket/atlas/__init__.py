"""ATLAS scoring engine — Loop 1 (GRS-0004 deterministic kernel, GRS-0005 uncertainty).

Implements ``docs/ATLAS-Methodology-v1.1.md`` §5 exactly: two-track aggregation (continuous
q_m/L/B/P/V + rule-based rating gate), the derived Platform Power triad (ordinal out, ADR-0002),
against a registry-validated `CoefficientSet`. `score()` is pure and fail-loud — no DB, no I/O, no
clock, no randomness. The Monte Carlo uncertainty engine (§7) WRAPS `score()`; its only randomness
comes from an injected, seeded RNG, so the golden-master determinism guarantee is preserved.
"""

from __future__ import annotations

from grassmarket.atlas.active import active_coefficient_set, active_uncertainty_model
from grassmarket.atlas.engine import ENGINE_VERSION, score, score_customer
from grassmarket.atlas.inputs import AssessmentInputs, MetricObservation, PowerObservation
from grassmarket.atlas.montecarlo import (
    DEFAULT_DRAWS,
    Band,
    TornadoEntry,
    UncertaintyResult,
    WeightStabilityInterval,
    draft_v1_uncertainty_model,
    elicited_v1_uncertainty_model,
    run_monte_carlo,
)
from grassmarket.atlas.results import (
    AtlasResult,
    BusinessResult,
    CompositeResult,
    CustomerResult,
    LResult,
    MetricRow,
    ModuleResult,
    PowerRow,
    PowersResult,
    SubcomponentRow,
    TriadDimensionResult,
    TriadResult,
)

__all__ = [
    "ENGINE_VERSION",
    "active_coefficient_set",
    "active_uncertainty_model",
    "score",
    "score_customer",
    "AssessmentInputs",
    "MetricObservation",
    "PowerObservation",
    "AtlasResult",
    "BusinessResult",
    "CompositeResult",
    "CustomerResult",
    "LResult",
    "MetricRow",
    "ModuleResult",
    "PowerRow",
    "PowersResult",
    "SubcomponentRow",
    "TriadDimensionResult",
    "TriadResult",
    # Uncertainty engine (GRS-0005)
    "DEFAULT_DRAWS",
    "Band",
    "TornadoEntry",
    "UncertaintyResult",
    "WeightStabilityInterval",
    "draft_v1_uncertainty_model",
    "elicited_v1_uncertainty_model",
    "run_monte_carlo",
]
