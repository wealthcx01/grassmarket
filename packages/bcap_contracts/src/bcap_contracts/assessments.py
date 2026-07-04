"""The ATLAS assessment contract surface — including `CoefficientSet`, where ADR-0001's
load-time invariants live.

Loop 0 ships the *types and the validators*; the scoring engine that consumes them is Loop 1.
The point of shipping `CoefficientSet` now is that the class of silent-fallback defects (D1–D7)
becomes a construction/validation error the first time a bad coefficient set is loaded — long
before any client sees a number.
"""

from __future__ import annotations

import math
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from bcap_contracts.base import OwnedResource
from bcap_contracts.common import (
    EvidenceGrade,
    MaturityLevel,
    NonScoreState,
    Score,
    StrengthRating,
    TrendDirection,
    TriadDimension,
    UncertaintyRating,
    UnitInterval,
)
from bcap_contracts.provenance import WeightProvenanceRecord
from bcap_contracts.registry import Registry

_THETA_TOLERANCE = 1e-9

# The provenance families every coefficient set names. A populated family without a provenance
# record is not loadable (ADR-0001 §3).
_PROVENANCE_FAMILIES = (
    "theta",
    "alpha_l",
    "alpha_module",
    "lambda",
    "delta",
    "w_power",
    "w_metric",
)


class CoefficientSet(BaseModel):
    """A versioned, provenance-carrying set of every coefficient the engine needs.

    Construction enforces the invariants that DON'T need the registry (Σθ=1, α∈[0,1], provenance
    present). :meth:`validate_against` enforces the ones that DO (every weight family is exactly
    the registry's key set for its dimension) and refuses empty dimensions. Neither failure is
    ever swallowed.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: str = Field(min_length=1)
    methodology_version: str = Field(min_length=1)

    # Top-level value weights θ (Methodology §5.4). Σθ = 1 enforced.
    theta_b: Score
    theta_p: Score
    theta_l: Score

    # Blend parameters α ∈ [0,1] (Methodology §5.1). The prototype's α = 2.0 (D3) fails here.
    alpha_l: UnitInterval
    alpha_module: dict[str, UnitInterval] = Field(default_factory=dict)

    # Weight families keyed by registry keys. Validated for completeness in validate_against.
    lambda_loadings: dict[str, dict[str, float]] = Field(
        default_factory=dict, description="Per-module subcomponent loadings λ_{m,c}."
    )
    delta: dict[str, float] = Field(
        default_factory=dict, description="Module weights δ_m for the L blend."
    )
    critical_modules_for_l: tuple[str, ...] = ()
    w_power: dict[str, float] = Field(default_factory=dict, description="Power weights w_j.")
    w_metric: dict[str, float] = Field(default_factory=dict, description="Metric weights w_k.")

    # Every coefficient family present must carry provenance (Methodology §6).
    provenance: dict[str, WeightProvenanceRecord] = Field(default_factory=dict)

    # --- Construction-time invariants (registry-independent) ---
    @model_validator(mode="after")
    def _enforce_theta_sum(self) -> CoefficientSet:
        total = self.theta_b + self.theta_p + self.theta_l
        if not math.isclose(total, 1.0, abs_tol=_THETA_TOLERANCE):
            raise ValueError(
                f"Σθ must equal 1 (got θ_B+θ_P+θ_L = {total!r}). Three conflicting θ sets summing "
                f"to anything cannot recur (ADR-0001 §3)."
            )
        return self

    @model_validator(mode="after")
    def _enforce_provenance(self) -> CoefficientSet:
        # θ is always populated; other families require provenance only when non-empty.
        populated = {"theta", "alpha_l"}
        if self.alpha_module:
            populated.add("alpha_module")
        if self.lambda_loadings:
            populated.add("lambda")
        if self.delta:
            populated.add("delta")
        if self.w_power:
            populated.add("w_power")
        if self.w_metric:
            populated.add("w_metric")
        missing = populated - set(self.provenance)
        if missing:
            raise ValueError(
                f"Coefficient families {sorted(missing)} are populated but carry no Weight "
                f"Provenance Record. A coefficient without provenance is not loadable "
                f"(Methodology §6, ADR-0001 §3)."
            )
        unknown = set(self.provenance) - set(_PROVENANCE_FAMILIES)
        if unknown:
            raise ValueError(
                f"Unknown provenance family key(s) {sorted(unknown)}; legal families: "
                f"{list(_PROVENANCE_FAMILIES)}."
            )
        return self

    # --- Registry completeness (needs the loaded registry) ---
    def validate_against(self, registry: Registry) -> None:
        """Assert every weight family is EXACTLY the registry's key set for its dimension.

        Raises `UnknownKeyError` / `MissingKeyError` / `EmptyDimensionError` — never returns a
        partial pass. This is the load-time gate that makes D1, D4, D7 impossible: a key that is
        not in the registry cannot be scored around.
        """
        # Modules (δ, α_module) must be exactly the registry module set.
        registry.assert_covers_keys("module (delta)", registry.module_keys(), set(self.delta))
        registry.assert_covers_keys(
            "module (alpha_module)", registry.module_keys(), set(self.alpha_module)
        )

        # Critical modules must be a subset of registered modules.
        unknown_critical = set(self.critical_modules_for_l) - registry.module_keys()
        if unknown_critical:
            from bcap_contracts.registry import UnknownKeyError

            raise UnknownKeyError(
                "critical_module", sorted(unknown_critical)[0], registry.module_keys()
            )

        # Per-module subcomponent loadings λ must be exactly that module's subcomponent set.
        registry.assert_covers_keys(
            "module (lambda)", registry.module_keys(), set(self.lambda_loadings)
        )
        for module_key in self.lambda_loadings:
            registry.assert_covers_keys(
                f"subcomponent[{module_key}]",
                registry.subcomponent_keys(module_key),
                set(self.lambda_loadings[module_key]),
            )

        # Powers (w_power) and metrics (w_metric) must be exactly the registry sets.
        registry.assert_covers_keys("power (w_power)", registry.power_keys(), set(self.w_power))
        registry.assert_covers_keys("metric (w_metric)", registry.metric_keys(), set(self.w_metric))


# --- Assessment resources (PRD §3.1) — the data model the wizard/Path B fill (Loop 2+) ---


class SubcomponentRating(BaseModel):
    """One subcomponent's rating: a maturity level OR a first-class non-score state, never both.

    Modelling this as an exclusive union is how "Not Assessed" stays distinct from a score of
    zero (defect D9) — an unassessed subcomponent carries `state`, not `level`, and contributes
    to no computation.
    """

    model_config = ConfigDict(extra="forbid")

    module_key: str
    subcomponent_key: str
    level: MaturityLevel | None = None
    state: NonScoreState | None = None
    evidence_grade: EvidenceGrade | None = None
    evidence_refs: tuple[str, ...] = ()
    notes: str | None = None
    rater_ids: tuple[UUID, ...] = ()  # ≥2 for a deliverable (Methodology §9 dual rating)
    consensus: bool = False
    dissent_note: str | None = None

    @model_validator(mode="after")
    def _exactly_one_of_level_or_state(self) -> SubcomponentRating:
        if (self.level is None) == (self.state is None):
            raise ValueError(
                "A SubcomponentRating carries exactly one of `level` (assessed) or `state` "
                "(Not Applicable / Not Assessed) — never both, never neither (Methodology §3.2)."
            )
        if self.level is not None and self.evidence_grade is None:
            raise ValueError("An assessed subcomponent (level set) requires an evidence_grade.")
        return self


class PowerAssessment(BaseModel):
    """Per-power evidence (Methodology §8): dual Benefit + Barrier, strength, trend, lifecycle."""

    model_config = ConfigDict(extra="forbid")

    power_key: str
    benefit_evidence: str
    barrier_evidence: str
    strength: StrengthRating
    trend: TrendDirection
    lifecycle_plausible: bool
    committee_approved: bool = False
    committee_rationale: str | None = None


class TriadResult(BaseModel):
    """A derived Platform Power triad rating — ordinal in, ordinal out (ADR-0002)."""

    model_config = ConfigDict(extra="forbid")

    dimension: TriadDimension
    rating: StrengthRating
    rationale: str
    committee_approved: bool = False


class ScoringRun(OwnedResource):
    """An immutable, versioned scoring run (Methodology, CLAUDE.md non-negotiable #6).

    Loop 0 ships the *shape* (append-only, hashed, version-stamped). The engine that fills
    `v_index` etc. is Loop 1. Finalisation locks inputs; scenarios stay editable.
    """

    assessment_id: UUID
    engine_version: str
    methodology_version: str
    coefficient_version: str
    content_hash: str = Field(description="SHA-256 over inputs + versions — the immutability seal.")
    finalised: bool = False

    # Score-domain outputs (dimensionless [0,1]); P50 point with P10/P90 band (Methodology §7).
    v_index: Score | None = None
    v_p10: Score | None = None
    v_p90: Score | None = None
    uncertainty_rating: UncertaintyRating | None = None
