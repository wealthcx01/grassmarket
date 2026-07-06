"""The uncertainty model — input-distribution widths for Monte Carlo (Methodology v1.2 §7).

Every input that carries a confidence signal gets a distribution whose width the model sets:

- **subcomponents & powers** — an ordinal evidence grade (E4 tight → E1 wide) drives an
  adjacent-level categorical over the maturity / strength scale (``evidence_spreads``);
- **business metrics** — a source/recency grade (audited tight → estimated wide) drives a relative
  spread on the raw value (``metric_spreads``, ADR-0008).

The per-grade widths are **coefficients**, not magic numbers: they carry a Weight Provenance Record
(§6) and ship draft-pending-elicitation, ``client_usable=False``, until the panel ratifies them.
The *families* (adjacent-level categorical for ordinals, relative multiplicative for metrics) and
the treatment of a Not-Assessed input (uniform / point-with-honest-label) are structural
methodology choices, documented in the GRS-0005/GRS-0007 tickets and ADR-0008 — not tunable weights.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

from bcap_contracts.common import EvidenceGrade, MetricConfidence
from bcap_contracts.provenance import WeightProvenanceRecord

_LEGAL_GRADES = frozenset(g.value for g in EvidenceGrade)
_LEGAL_METRIC_GRADES = frozenset(g.value for g in MetricConfidence)


def _assert_non_increasing_by_rank(spreads: dict[str, float], grades, name: str) -> None:
    """Weaker evidence must be at least as wide — the tight-strong / wide-weak guarantee is enforced
    here, not assumed by the sampler. ``grades`` is ordered weakest→strongest by rank."""
    by_rank = [spreads[g.value] for g in sorted(grades, key=lambda g: g.rank)]
    if any(lo < hi for lo, hi in zip(by_rank, by_rank[1:], strict=False)):
        raise ValueError(f"{name} must be non-increasing by grade strength; got {spreads}.")


class UncertaintyModel(BaseModel):
    """Input-distribution widths for the Monte Carlo uncertainty engine (§7).

    ``evidence_spreads[grade]`` is the probability mass that leaves the point level for the ADJACENT
    level(s) under an evidence grade (subcomponents and powers). ``metric_spreads[grade]`` is the
    relative half-width applied to a metric's raw value under a source/recency grade. Both must
    cover their four grades, lie in [0,1], and be non-increasing by grade strength."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: str
    methodology_version: str
    family: str = "adjacent_level_categorical"
    evidence_spreads: dict[str, float]
    metric_spreads: dict[str, float]
    client_usable: bool = False
    provenance: WeightProvenanceRecord

    @model_validator(mode="after")
    def _validate_spreads(self) -> UncertaintyModel:
        if set(self.evidence_spreads) != _LEGAL_GRADES:
            raise ValueError(
                f"evidence_spreads must cover exactly the four evidence grades "
                f"{sorted(_LEGAL_GRADES)}; got {sorted(self.evidence_spreads)}."
            )
        if set(self.metric_spreads) != _LEGAL_METRIC_GRADES:
            raise ValueError(
                f"metric_spreads must cover exactly the four metric-confidence grades "
                f"{sorted(_LEGAL_METRIC_GRADES)}; got {sorted(self.metric_spreads)}."
            )
        for name, spreads in (
            ("evidence_spreads", self.evidence_spreads),
            ("metric_spreads", self.metric_spreads),
        ):
            if any(not (0.0 <= v <= 1.0) for v in spreads.values()):
                raise ValueError(f"Each {name} value is in [0, 1].")
        _assert_non_increasing_by_rank(self.evidence_spreads, EvidenceGrade, "evidence_spreads")
        _assert_non_increasing_by_rank(self.metric_spreads, MetricConfidence, "metric_spreads")
        return self
