"""The uncertainty model — evidence-grade → input-distribution widths (Methodology v1.1 §7).

Monte Carlo turns each assessed subcomponent rating into a distribution over the maturity scale
whose spread is set by its evidence grade (E4 tight → E1 wide, spanning the adjacent level). The
per-grade widths are **coefficients**, not magic numbers: like every non-input number they carry a
Weight Provenance Record (§6) and ship draft-pending-elicitation, `client_usable=False`, until the
panel ratifies them.

Only the widths are elicited. The *family* (an adjacent-level categorical) and the treatment of a
Not-Assessed subcomponent (uniform over all four levels — maximal ignorance, the max-entropy prior)
are structural methodology choices, documented in the GRS-0005 ticket, not tunable weights.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

from bcap_contracts.common import EvidenceGrade
from bcap_contracts.provenance import WeightProvenanceRecord

_LEGAL_GRADES = frozenset(g.value for g in EvidenceGrade)


class UncertaintyModel(BaseModel):
    """Evidence-grade input-distribution widths for the Monte Carlo uncertainty engine (§7).

    ``evidence_spreads[grade]`` is the total probability mass that leaves the point level for the
    ADJACENT level(s) under that grade — the "width". It must cover all four grades, lie in [0,1],
    and be non-increasing E1 ≥ E2 ≥ E3 ≥ E4 (weaker evidence is at least as wide — the E4-tight /
    E1-wide guarantee is enforced here, not assumed by the sampler)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: str
    methodology_version: str
    family: str = "adjacent_level_categorical"
    evidence_spreads: dict[str, float]
    client_usable: bool = False
    provenance: WeightProvenanceRecord

    @model_validator(mode="after")
    def _validate_spreads(self) -> UncertaintyModel:
        if set(self.evidence_spreads) != _LEGAL_GRADES:
            raise ValueError(
                f"evidence_spreads must cover exactly the four evidence grades "
                f"{sorted(_LEGAL_GRADES)}; got {sorted(self.evidence_spreads)}."
            )
        if any(not (0.0 <= v <= 1.0) for v in self.evidence_spreads.values()):
            raise ValueError("Each evidence spread is a probability mass in [0, 1].")
        # Non-increasing by grade strength (E1 widest → E4 tightest). Ordered by EvidenceGrade.rank.
        ordered = sorted(EvidenceGrade, key=lambda g: g.rank)
        by_rank = [self.evidence_spreads[g.value] for g in ordered]
        if any(lo < hi for lo, hi in zip(by_rank, by_rank[1:], strict=False)):
            raise ValueError(
                f"evidence_spreads must be non-increasing E1 ≥ E2 ≥ E3 ≥ E4 (weaker evidence is at "
                f"least as wide); got {self.evidence_spreads}."
            )
        return self
