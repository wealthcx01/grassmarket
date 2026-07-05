"""ATLAS scoring engine — Loop 1 (GRS-0004).

Implements ``docs/ATLAS-Methodology-v1.1.md`` §5 exactly: two-track aggregation (continuous
q_m/L/B/P/V + rule-based rating gate), the derived Platform Power triad (ordinal out, ADR-0002),
against a registry-validated `CoefficientSet`. Pure and fail-loud — no DB, no I/O, no clock, no
randomness (persistence and Monte Carlo are later boundaries). The golden-master fixture and the
property tests gate every line (CLAUDE.md testing rules).
"""

from __future__ import annotations

from grassmarket.atlas.engine import ENGINE_VERSION, score
from grassmarket.atlas.inputs import AssessmentInputs, MetricObservation, PowerObservation
from grassmarket.atlas.results import (
    AtlasResult,
    BusinessResult,
    CompositeResult,
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
    "score",
    "AssessmentInputs",
    "MetricObservation",
    "PowerObservation",
    "AtlasResult",
    "BusinessResult",
    "CompositeResult",
    "LResult",
    "MetricRow",
    "ModuleResult",
    "PowerRow",
    "PowersResult",
    "SubcomponentRow",
    "TriadDimensionResult",
    "TriadResult",
]
