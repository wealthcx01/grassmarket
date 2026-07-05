"""Engine inputs — the contract-typed evidence the ATLAS engine scores (Methodology v1.1 §5).

These are the *engine's* input surface, distinct from the wizard-facing resources (Loop 2 fills
`bcap_contracts.assessments.SubcomponentRating` etc.). Subcomponent ratings reuse that contract
directly; metrics and powers get small engine-local observations here. Everything is fail-loud:
exactly one of level/state, a benefit AND a barrier per power (Helmer, §8), etc.
"""

from __future__ import annotations

from bcap_contracts.assessments import SubcomponentRating
from bcap_contracts.common import NonScoreState, StrengthRating
from pydantic import BaseModel, ConfigDict, model_validator


class MetricObservation(BaseModel):
    """One business-metric observation: a raw value in the metric's declared unit, OR a first-class
    non-score state — never both, never neither (the §3.2 discipline, extended to metrics, B4)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_key: str
    raw: float | None = None
    state: NonScoreState | None = None

    @model_validator(mode="after")
    def _exactly_one_of_raw_or_state(self) -> MetricObservation:
        if (self.raw is None) == (self.state is None):
            raise ValueError(
                f"Metric {self.metric_key!r} carries exactly one of `raw` (observed) or `state` "
                f"(Not Applicable / Not Assessed) — never both, never neither."
            )
        return self


class PowerObservation(BaseModel):
    """Per-power dual strengths (Methodology v1.1 §8): a power carries BOTH a Benefit and a Barrier
    strength; the engine takes the weaker side. Powers are never N/A — all 7 are always in scope."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    power_key: str
    benefit: StrengthRating
    barrier: StrengthRating


class AssessmentInputs(BaseModel):
    """The complete input to one scoring run: 51 subcomponent ratings, the metric register's
    observations, and all 7 powers. Completeness against the registry is checked by the engine
    (fail-loud), not defaulted around."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subcomponents: tuple[SubcomponentRating, ...]
    metrics: tuple[MetricObservation, ...]
    powers: tuple[PowerObservation, ...]
