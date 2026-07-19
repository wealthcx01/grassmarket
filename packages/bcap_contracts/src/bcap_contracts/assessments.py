"""The ATLAS assessment contract surface — including `CoefficientSet`, where ADR-0001's
load-time invariants live.

Loop 0 ships the *types and the validators*; the scoring engine that consumes them is Loop 1.
The point of shipping `CoefficientSet` now is that the class of silent-fallback defects (D1–D7)
becomes a construction/validation error the first time a bad coefficient set is loaded — long
before any client sees a number.
"""

from __future__ import annotations

import math
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from bcap_contracts.base import OwnedResource
from bcap_contracts.common import (
    EvidenceGrade,
    MaturityLevel,
    MetricConfidence,
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
    "group_weights",  # W_g for the group-weighted B (ADR-0006)
    "strength_encoding",  # ordinal power strength → numeric encoding for P (ADR-0004)
    # C-index families (ADR-0023, Stage 1). Populated only on a set that scores C; a B/P/L-only
    # set leaves them empty, so the golden-master coefficient set is unaffected.
    "alpha_c",
    "alpha_c_module",
    "lambda_c",
    "delta_c",
    "rarity_weight",  # Level-1 widget rarity weighting (ADR-0023); populated in GRS-0084
)

# Closed value sets for the non-registry-keyed coefficient families (ADR-0004, ADR-0006). Kept as
# frozensets of the enum/literal *values* so a typo is a construction-time refusal, not a default.
_LEGAL_METRIC_GROUPS = frozenset({"scale", "unit_economics", "momentum"})
_LEGAL_STRENGTHS = frozenset(s.value for s in StrengthRating)


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
    # The fourth headline weight θ_C — the Customer-Proposition term of the composite V (ADR-0023
    # Stage 2, Methodology v1.4). PRESENT ⇒ the four-index V (B/P/L/C) with Σθ over all FOUR = 1;
    # ABSENT (None) ⇒ the three-index V (Stage 1, §5.1 unchanged), so the ratified golden master and
    # the `1.1` deterministic stamp survive. A four-index V with θ_C absent is IMPOSSIBLE by
    # construction — the engine never defaults θ_C to 0 (ADR-0023 §4, fail-loud). A set carrying
    # θ_C MUST also score C (validated below): you cannot weight a C you do not compute.
    theta_c: Score | None = None

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

    # --- C-index coefficients (ADR-0023, Stage 1: report-alongside) ---
    # OPTIONAL and all-or-nothing. A set with `alpha_c is None` does not score C at all: B/P/L is
    # scored exactly as before and the golden master is untouched (C rides the L aggregation shape
    # over the separate C registry dimension, never mixing into the B/P/L keyspace). When C is
    # scored, all four families + provenance are required and validated against the C registry.
    alpha_c: UnitInterval | None = None
    alpha_c_module: dict[str, UnitInterval] = Field(default_factory=dict)
    lambda_c_loadings: dict[str, dict[str, float]] = Field(
        default_factory=dict, description="Per-C-module subcomponent loadings λ_{m,c}."
    )
    delta_c: dict[str, float] = Field(
        default_factory=dict, description="C-module weights δ_m for the C blend."
    )
    critical_modules_for_c: tuple[str, ...] = ()

    w_power: dict[str, float] = Field(default_factory=dict, description="Power weights w_j.")
    w_metric: dict[str, float] = Field(default_factory=dict, description="Metric weights w_k.")

    # Group weights W_g for the group-weighted Business index B (ADR-0006), keyed by metric group
    # (scale | unit_economics | momentum). Empty until the register is grouped.
    group_weights: dict[str, float] = Field(default_factory=dict)
    # Ordinal power-strength → numeric encoding for the continuous P index (ADR-0004), keyed by
    # StrengthRating value (None / Emerging / Established / Wide). The triad stays ordinal out
    # (ADR-0002); it feeds only P. The engine derives the triad band thresholds from it (ADR-0007).
    strength_encoding: dict[str, float] = Field(default_factory=dict)

    # A draft set (weights not yet elicited) is loadable for tests but MUST NOT price a client
    # deliverable. Ratified/elicited sets flip this true; deliverable generation (later loop) gates
    # on it. Default False — a set is not client-usable until someone says so (fail-safe).
    client_usable: bool = False

    # Every coefficient family present must carry provenance (Methodology §6).
    provenance: dict[str, WeightProvenanceRecord] = Field(default_factory=dict)

    @property
    def scores_c(self) -> bool:
        """Whether this set carries the C-index coefficients (ADR-0023 Stage 1). `alpha_c is not
        None` is the single source of truth — the all-or-nothing validator guarantees that when
        `alpha_c` is set, the other three C families are populated too."""
        return self.alpha_c is not None

    # --- Construction-time invariants (registry-independent) ---
    @model_validator(mode="after")
    def _enforce_c_all_or_nothing(self) -> CoefficientSet:
        """The C families are all-or-nothing: a half-populated C set (e.g. δ_c without α_c) would
        make `scores_c` ambiguous and could validate B/P/L while silently skipping C completeness.
        Refuse it at construction (ADR-0023, ADR-0001 §3)."""
        c_populated = (
            self.alpha_c is not None,
            bool(self.alpha_c_module),
            bool(self.lambda_c_loadings),
            bool(self.delta_c),
        )
        if any(c_populated) and not all(c_populated):
            raise ValueError(
                "C-index coefficients are all-or-nothing (ADR-0023): provide alpha_c, "
                "alpha_c_module, lambda_c_loadings, and delta_c together, or none of them."
            )
        return self

    @model_validator(mode="after")
    def _enforce_theta_sum(self) -> CoefficientSet:
        # Three-index (Stage 1) when θ_C is absent; four-index (Stage 2/v1.4) when present. Σθ
        # equal 1 over exactly the terms in play — never a three-term set with a bolted-on fourth.
        if self.theta_c is None:
            total = self.theta_b + self.theta_p + self.theta_l
            terms = "θ_B+θ_P+θ_L"
        else:
            total = self.theta_b + self.theta_p + self.theta_l + self.theta_c
            terms = "θ_B+θ_P+θ_L+θ_C"
        if not math.isclose(total, 1.0, abs_tol=_THETA_TOLERANCE):
            raise ValueError(
                f"Σθ must equal 1 (got {terms} = {total!r}). Conflicting θ sets summing to "
                f"anything cannot recur (ADR-0001 §3)."
            )
        return self

    @model_validator(mode="after")
    def _theta_c_requires_scoring_c(self) -> CoefficientSet:
        """θ_C weights C INTO V (four-index, v1.4) — so a set that carries θ_C must also compute C
        (`scores_c`). Weighting a C the engine never produces forces a silent θ_C·0 — exactly the
        default this staged design forbids (ADR-0023 §4, ADR-0001)."""
        if self.theta_c is not None and not self.scores_c:
            raise ValueError(
                "θ_C is set (four-index V, v1.4) but the set does not score C: a headline C weight "
                "with no C coefficients would fold a fabricated zero into V (ADR-0023 §4)."
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
        if self.group_weights:
            populated.add("group_weights")
        if self.strength_encoding:
            populated.add("strength_encoding")
        if self.alpha_c is not None:
            populated.add("alpha_c")
        if self.alpha_c_module:
            populated.add("alpha_c_module")
        if self.lambda_c_loadings:
            populated.add("lambda_c")
        if self.delta_c:
            populated.add("delta_c")
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

    @model_validator(mode="after")
    def _enforce_closed_set_keys(self) -> CoefficientSet:
        """group_weights and strength_encoding are keyed by CLOSED value sets, not registry keys
        (ADR-0004/0006). A stray key is a typo and refuses to construct. strength_encoding, when
        present, must cover ALL four StrengthRatings — a partial encoding would silently drop a
        level to nothing at score time. (Registry-keyed completeness stays in validate_against;
        their *presence* is enforced fail-loud by the engine where it reads them.)"""
        unknown_groups = set(self.group_weights) - _LEGAL_METRIC_GROUPS
        if unknown_groups:
            raise ValueError(
                f"group_weights has unknown group key(s) {sorted(unknown_groups)}; legal groups: "
                f"{sorted(_LEGAL_METRIC_GROUPS)} (ADR-0006)."
            )
        if self.strength_encoding and set(self.strength_encoding) != _LEGAL_STRENGTHS:
            raise ValueError(
                f"strength_encoding must cover exactly the four StrengthRatings "
                f"{sorted(_LEGAL_STRENGTHS)}; got {sorted(self.strength_encoding)} (ADR-0004)."
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

        # Group weights (W_g) must cover exactly the distinct metric groups the registry declares
        # (ADR-0006). If the register isn't grouped yet there is nothing to cover.
        groups_present = frozenset(m.group for m in registry.metrics if m.group is not None)
        if groups_present:
            registry.assert_covers_keys(
                "metric_group (group_weights)", groups_present, set(self.group_weights)
            )

        # C-index dimension (ADR-0023). Validated only when the set scores C; a B/P/L-only set
        # leaves the C families empty, so this whole block is a no-op and the golden master path
        # is unchanged. When present, δ_c / α_c_module / λ_c must be EXACTLY the C registry's keys.
        if self.scores_c:
            registry.assert_covers_keys(
                "c_module (delta_c)", registry.c_module_keys(), set(self.delta_c)
            )
            registry.assert_covers_keys(
                "c_module (alpha_c_module)", registry.c_module_keys(), set(self.alpha_c_module)
            )
            unknown_c_critical = set(self.critical_modules_for_c) - registry.c_module_keys()
            if unknown_c_critical:
                from bcap_contracts.registry import UnknownKeyError

                raise UnknownKeyError(
                    "critical_c_module", sorted(unknown_c_critical)[0], registry.c_module_keys()
                )
            registry.assert_covers_keys(
                "c_module (lambda_c)", registry.c_module_keys(), set(self.lambda_c_loadings)
            )
            for module_key in self.lambda_c_loadings:
                registry.assert_covers_keys(
                    f"c_subcomponent[{module_key}]",
                    registry.c_subcomponent_keys(module_key),
                    set(self.lambda_c_loadings[module_key]),
                )


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

    @model_validator(mode="after")
    def _consensus_and_dissent_are_consistent(self) -> SubcomponentRating:
        """Consensus (raters agreed) and a dissent note are mutually exclusive: a note is recorded
        precisely when raters DIFFERED and one yielded (Methodology §9). The ≥2-rater requirement
        for a deliverable is enforced at finalisation (a draft/partial rating carries no raters)."""
        if self.consensus and self.dissent_note is not None:
            raise ValueError(
                "A consensus rating (raters agreed) carries no dissent note; a dissent note means "
                "consensus=False — the raters differed and one yielded (Methodology §9)."
            )
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
    # Which uncertainty model produced the band (§7, ADR-0008). Null for a point-only run.
    uncertainty_version: str | None = None
    content_hash: str = Field(description="SHA-256 over inputs + versions — the immutability seal.")
    finalised: bool = False

    # Score-domain outputs (dimensionless [0,1]); P50 point with P10/P90 band (Methodology §7).
    v_index: Score | None = None
    v_p10: Score | None = None
    v_p90: Score | None = None
    uncertainty_rating: UncertaintyRating | None = None


# --- The intermediate schema (Path A wizard + later Path B feed this ONE document) ------


class MetricEntry(BaseModel):
    """A business-metric entry in the intermediate document: a raw value in the declared unit OR a
    non-score state, with an OPTIONAL source/recency confidence (drives §7 uncertainty, ADR-0008).
    """

    model_config = ConfigDict(extra="forbid")

    metric_key: str
    raw: float | None = None
    state: NonScoreState | None = None
    confidence: MetricConfidence | None = None
    # Optional evidence/rationale for the figure (GRS-0107) — where it came from, as-of when — so a
    # metric carries its justification, never a bare number. Additive; not a scoring input.
    notes: str | None = None

    @model_validator(mode="after")
    def _exactly_one_of_raw_or_state(self) -> MetricEntry:
        if (self.raw is None) == (self.state is None):
            raise ValueError(f"Metric {self.metric_key!r} carries exactly one of `raw` or `state`.")
        # A non-finite raw (NaN/inf) can never be a real figure — refuse it at the boundary so it
        # never persists in a document or reaches scoring (GRS-0144). Sign/range bounds are checked
        # against the metric's registry definition at score time (they need the MetricDef).
        if self.raw is not None and not math.isfinite(self.raw):
            raise ValueError(
                f"Metric {self.metric_key!r} raw must be a finite number, got {self.raw}."
            )
        return self


class PowerEntry(BaseModel):
    """A power entry: dual Benefit + Barrier strengths (Helmer, §8), each with OPTIONAL evidence
    grade (drives §7 uncertainty, ADR-0008) and evidence text. Powers are never N/A (§8)."""

    model_config = ConfigDict(extra="forbid")

    power_key: str
    benefit: StrengthRating
    barrier: StrengthRating
    benefit_grade: EvidenceGrade | None = None
    barrier_grade: EvidenceGrade | None = None
    benefit_evidence: str | None = None
    barrier_evidence: str | None = None
    trend: TrendDirection | None = None


class WidgetObservation(BaseModel):
    """One Level-1 widget observation for the C-index grid (ADR-0023 / GRS-0083).

    A widget is either PRESENT (then scored 1–5 on ease / usability / depth) or NOT present — and a
    non-present widget can still carry a first-class reason it isn't a clean pass:
    `PRESENT_PAYWALLED` (gated behind a paywall) or `PRESENT_DEFECTIVE` (shipped but broken).
    Absent-and-nothing-else is `present=False` with no `state`. The rarity tag is NOT stored here:
    it is read from the registry (a single source of truth), never copied onto the observation."""

    model_config = ConfigDict(extra="forbid")

    widget_key: str
    present: bool
    # A non-present widget's first-class qualifier (ADR-0023). Only PRESENT_PAYWALLED /
    # PRESENT_DEFECTIVE are legal here, and only when `present` is False (validated below).
    state: NonScoreState | None = None
    ease: int | None = Field(default=None, ge=1, le=5)
    usability: int | None = Field(default=None, ge=1, le=5)
    depth: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = None

    @model_validator(mode="after")
    def _present_and_scores_are_consistent(self) -> WidgetObservation:
        scores = (self.ease, self.usability, self.depth)
        if self.present:
            if self.state is not None:
                raise ValueError(
                    f"Widget {self.widget_key!r} is present — it carries no non-score state "
                    f"(paywalled/defective describe a NON-present widget)."
                )
        else:
            if any(s is not None for s in scores):
                raise ValueError(
                    f"Widget {self.widget_key!r} is not present — it carries no 1–5 quality "
                    f"scores (ease/usability/depth are for a present widget)."
                )
            if self.state is not None and self.state not in (
                NonScoreState.PRESENT_PAYWALLED,
                NonScoreState.PRESENT_DEFECTIVE,
            ):
                raise ValueError(
                    f"Widget {self.widget_key!r}: a non-present widget's state must be "
                    f"PRESENT_PAYWALLED or PRESENT_DEFECTIVE (or none), not {self.state.value!r}."
                )
        return self


class BusinessProfile(BaseModel):
    """Descriptive context for the business being assessed (GRS-0068): where it operates, what it
    offers, and how it's regulated. Most fields are purely informational (never a scoring input,
    in the content hash). The one exception is `operating_model` (GRS-0079): the assessment PROFILE
    key (retail / exchange / …), which selects the registry view + coefficient set the assessment
    scores against (ADR-0025). It is not a *value* the engine reads, but it does decide WHICH keys
    and weights apply — so it is scoring-relevant config, not free-text. `segment` stays the
    free-text descriptor. Partial by design: every field is optional; `operating_model` unset means
    the retail default (byte-identical to v1)."""

    model_config = ConfigDict(extra="forbid")

    country: str | None = Field(default=None, description="Primary domicile / HQ jurisdiction.")
    segment: str | None = Field(
        default=None, description="Free-text business descriptor, e.g. 'Neobroker'."
    )
    # The operating-model profile key (ADR-0025). None → retail default. Validated against the
    # profile registry at score time (an unknown key fails loud, ADR-0001).
    operating_model: str | None = Field(
        default=None, description="Operating-model profile key: 'retail' (default), 'exchange', …"
    )
    asset_classes: tuple[str, ...] = Field(
        default=(), description="Asset classes offered (equities, funds, FX, crypto, …)."
    )
    regions: tuple[str, ...] = Field(default=(), description="Markets / regions served.")
    licensing: str | None = Field(
        default=None, description="Regulatory status / key licences (free text)."
    )


class AssessmentDocument(BaseModel):
    """The single intermediate schema BOTH Path A (wizard) and Path B (meeting intelligence) feed.

    It is **partial by design**: a half-filled document is valid and persistable (autosave). It is
    NOT the engine input — the engine requires exact registry coverage; the live-score service
    completes the missing subcomponents/metrics to Not Assessed (first-class, never zero-filled)."""

    model_config = ConfigDict(extra="forbid")

    subject: str = ""
    profile: BusinessProfile | None = None
    subcomponents: tuple[SubcomponentRating, ...] = ()
    metrics: tuple[MetricEntry, ...] = ()
    powers: tuple[PowerEntry, ...] = ()
    # C-index capture (ADR-0023 / GRS-0083). Both partial by design and default-empty, so every
    # existing document deserialises unchanged. `c_subcomponents` are Level-2 C ratings (same shape
    # as B/P/L); `widgets` are the Level-1 grid rows. A non-retail profile captures no widgets.
    c_subcomponents: tuple[SubcomponentRating, ...] = ()
    widgets: tuple[WidgetObservation, ...] = ()
    notes: str | None = None


class AssessmentState(StrEnum):
    """The assessment lifecycle. Finalisation locks inputs (CLAUDE.md non-negotiable #6)."""

    DRAFT = "draft"  # created, not yet edited
    IN_PROGRESS = "in_progress"  # being filled (autosaved)
    FINALISED = "finalised"  # inputs locked; an immutable scoring run exists


class RecordProvenance(StrEnum):
    """Where a record sits relative to production (ADR-0029). Set at creation, IMMUTABLE, and
    carried on the assessment so non-production records are segregated at the data layer.

    A non-production (`demo`/`sandbox`) record may finalise and run the REAL deliverable generation
    WITHOUT the dual-rating + committee gate — so a solo tester/salesperson can walk the flow — but
    is permanently watermarked, never counted as ratified, never enters the benchmark/prediction
    populations, and can never be promoted to production. The AI-approval non-negotiable (#8)
    is intact: these outputs are non-client-facing by construction, not a bypass of approval for
    real work."""

    PRODUCTION = "production"  # the default; the full dual-rating + committee gate applies
    DEMO = "demo"  # a seeded, watermarked worked example (GRS-0117)
    SANDBOX = "sandbox"  # a solo tester's own throwaway record, self-approvable (GRS-0119)


class Assessment(OwnedResource):
    """A scoped, lifecycle-managed assessment wrapping the intermediate document. When finalised it
    is version-stamped and linked to its immutable scoring run (GRS-0006)."""

    subject: str = ""
    # The canonical company this subject resolves to (GRS-0100, ADR-0033) — null when the advisor
    # entered a subject the registry does not cover (the explicit manual fallback). Two assessments
    # of the same company share this id.
    entity_id: str | None = None
    state: AssessmentState = AssessmentState.DRAFT
    document: AssessmentDocument
    # Record provenance (ADR-0029): production (default, full gate) vs demo/sandbox
    # (self-approvable, watermarked, non-promotable). Set at creation, immutable thereafter.
    provenance: RecordProvenance = RecordProvenance.PRODUCTION
    finalised_at: datetime | None = None
    scoring_run_id: UUID | None = None
    # Version stamps recorded at finalisation (null while editable).
    engine_version: str | None = None
    methodology_version: str | None = None
    coefficient_version: str | None = None
    uncertainty_version: str | None = None


class BrokeragePortfolioEntry(BaseModel):
    """One row of the advisor's "Your Brokerages" portfolio home (GRS-0071): a scoped, at-a-glance
    summary of an assessment — its segment (from the business profile), status, and last finalised
    Platform Value with the honest uncertainty rating. `v_index` is the P50 in [0,1]; it is None
    until the assessment is finalised (a draft has no immutable score). Self-scoped, like every read
    (a consultant sees only their own book)."""

    model_config = ConfigDict(extra="forbid")

    assessment_id: UUID
    subject: str
    segment: str | None = None
    state: AssessmentState
    # ADR-0029: a demo/sandbox record is flagged here so its watermark shows everywhere the summary
    # appears (portfolio home, engagement view) — production is the unremarkable default (GRS-0117).
    provenance: RecordProvenance = RecordProvenance.PRODUCTION
    v_index: Score | None = None
    uncertainty_rating: UncertaintyRating | None = None
    # Assessed subcomponents over APPLICABLE ones (Not Applicable excluded) — the coverage notion
    # live panel shows, so a linked assessment's progress reads at a glance (GRS-0116). None when
    # nothing is applicable yet.
    coverage: Score | None = None
    finalised_at: datetime | None = None
    updated_at: datetime


# --- Dual-rating governance (Methodology §9) --------------------------------------------


class ModuleRatingDraft(OwnedResource):
    """One rater's INDEPENDENT rating of one module's subcomponents (Methodology §9 dual rating).

    `owner_consultant_id` is the rater. A module needs ≥2 of these before its subcomponents can
    reach consensus and be finalised — "solo ratings are drafts, never deliverables". Blind by
    construction: the repository refuses to show a rater a co-rater's draft until every assigned
    rater on the module has submitted, so the second opinion is genuinely independent. `submitted`
    locks the draft; the lead then resolves consensus per subcomponent."""

    model_config = ConfigDict(extra="forbid")

    assessment_id: UUID
    module_key: str
    ratings: tuple[SubcomponentRating, ...] = ()
    submitted: bool = False
    submitted_at: datetime | None = None

    @model_validator(mode="after")
    def _ratings_belong_to_this_module_and_submit_is_stamped(self) -> ModuleRatingDraft:
        stray = sorted({r.module_key for r in self.ratings if r.module_key != self.module_key})
        if stray:
            raise ValueError(
                f"Every rating in a module draft must carry this draft's module_key "
                f"({self.module_key!r}); found stray module_key(s) {stray}."
            )
        if self.submitted != (self.submitted_at is not None):
            raise ValueError(
                "A submitted draft carries a submitted_at timestamp, and an unsubmitted one "
                "carries none — the two move together."
            )
        return self


# --- Live-score response (the wizard's live panel) --------------------------------------


class IndexBand(BaseModel):
    """A P10/P50/P90 band for one index with the ADR-0008 honesty flag. `modelled = False` ⟹ a
    point estimate (P10=P50=P90) — the client shows a point labelled 'uncertainty not modelled',
    never a tight band."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    p10: Score
    p50: Score
    p90: Score
    modelled: bool


class LiveScore(BaseModel):
    """The live-score panel output for a (possibly partial) document. When `scoreable`, the bands
    are present; else `blocking` says what is still needed. Not Assessed inputs flow through as
    first-class (excluded, never zero) and are reflected in `coverage`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scoreable: bool
    blocking: tuple[str, ...] = ()
    v: IndexBand | None = None
    b: IndexBand | None = None
    p: IndexBand | None = None
    l_index: IndexBand | None = None
    # C-index (ADR-0023 Stage 1): a DETERMINISTIC value reported alongside V, never summed in and
    # never a Monte Carlo band (uncertainty modelling of C is post-Stage-1). None until C is
    # scoreable (a rated C subcomponent in a critical-for-C module), independent of V-scoreability.
    c: Score | None = None
    module_qm: dict[str, IndexBand] = Field(default_factory=dict)
    # Derived Platform Power triad — ordinal out (ADR-0002), never a decimal to the client.
    triad_economic: StrengthRating | None = None
    triad_perceived: StrengthRating | None = None
    triad_defence: StrengthRating | None = None
    overall_uncertainty: UncertaintyRating | None = None
    subcomponents_assessed: int = 0
    subcomponents_total: int = 0
    coverage: Score | None = None
    # Weights the score was built from — surfaced for the diagnostic visuals (GRS-0070): the θ
    # value-weights drive the B→P→L→V waterfall, the module weights δ_m (κ_m) annotate the module
    # table. Present only when scoreable; this is transparency of the active coefficients, never a
    # client price (the client-facing gate is on deliverables, not the live panel).
    theta_b: Score | None = None
    theta_p: Score | None = None
    theta_l: Score | None = None
    module_weights: dict[str, float] = Field(default_factory=dict)
    engine_version: str
    methodology_version: str
    coefficient_version: str
    uncertainty_version: str
