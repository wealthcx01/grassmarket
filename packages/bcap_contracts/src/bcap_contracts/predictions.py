"""Prediction register + anonymised benchmark population (GRS-0031, Methodology v1.2 §11).

The falsifiability machinery. At deliverable finalisation, each value-bridge lever becomes a
**prediction**: what value it will move, by when, with what confidence, linked to the immutable
scoring run. Later a follow-up records the realised value and the prediction is scored — a
hit/miss and a Brier score for the probabilistic claim. Separately, each finalised score is ingested
into an **anonymised benchmark population**: a `BenchmarkRow` carries ONLY the score, uncertainty,
methodology versions — no client name, entity id, contact, owner, or run id survives (provably
de-identified).
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from bcap_contracts.base import OwnedResource
from bcap_contracts.common import Score, UncertaintyRating, UnitInterval
from bcap_contracts.money import Money
from bcap_contracts.value import LeverKind


class PredictionOutcome(StrEnum):
    """A prediction is PENDING until its follow-up scores it a HIT or a MISS (directional)."""

    PENDING = "pending"
    HIT = "hit"
    MISS = "miss"


class BenchmarkSector(StrEnum):
    """A CONTROLLED industry vocabulary for a benchmark row. A closed set (not free text) so a
    client name can never be typed into the one otherwise-descriptive field — the anonymisation
    guarantee has no data-entry soft spot."""

    BROKERAGE = "brokerage"
    ASSET_MANAGEMENT = "asset_management"
    WEALTH_MANAGEMENT = "wealth_management"
    EXCHANGE = "exchange"
    MARKET_INFRASTRUCTURE = "market_infrastructure"
    BANKING = "banking"
    INSURANCE = "insurance"
    FINTECH = "fintech"
    OTHER = "other"


class Prediction(OwnedResource):
    """One lever-level prediction, pre-registered against a scoring run. The `probability`
    is the model's confidence the value moves in the predicted direction — used for the Brier score.
    Realised value + scores are stamped on follow-up; before that they are None."""

    model_config = ConfigDict(extra="forbid")

    scoring_run_id: UUID
    lever: LeverKind
    predicted_delta: Money = Field(description="The predicted signed value impact (currency).")
    horizon_months: int = Field(gt=0)
    probability: UnitInterval = Field(
        description="Confidence the value moves in the predicted direction (for the Brier score)."
    )
    follow_up_due: date
    outcome: PredictionOutcome = PredictionOutcome.PENDING
    realised_delta: Money | None = None
    brier_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="(probability − outcome)²; lower is better."
    )
    scored_at: datetime | None = None


class BenchmarkRow(BaseModel):
    """An anonymised finalised score in the benchmark population. Provably de-identified: it carries
    ONLY the score, its uncertainty, the methodology/coefficient versions, and a non-identifying
    sector — NEVER a name, entity id, contact, owner, assessment id, or scoring-run id."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    v_index: Score
    v_p10: Score | None = None
    v_p90: Score | None = None
    uncertainty_rating: UncertaintyRating | None = None
    methodology_version: str = Field(min_length=1)
    coefficient_version: str = Field(min_length=1)
    sector: BenchmarkSector | None = Field(
        default=None, description="A non-identifying industry category (closed vocabulary)."
    )
    ingested_at: datetime


class CBenchmarkRow(BaseModel):
    """A NAMED peer's Customer-Proposition (C) score in the C benchmark set (ADR-0023 / GRS-0084).

    Unlike the anonymised V benchmark, C peers are PUBLIC brokerage apps (Saxo, IBKR, Revolut, …) —
    a named, shared reference set, not client data. AI/consultant-derived scores are APPROVAL-GATED
    (ADR-0009, CLAUDE.md #8): a row is `approved=False` on ingestion and only an approved row is
    'live' for peer comparison — nothing AI-proposed enters the benchmark without a recorded human
    sign-off. `module_scores` are per-C-module q_m, keyed to the C registry (validated at ingest —
    an unknown key fails loud, never silently dropped)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    peer_name: str = Field(min_length=1, description="Public app/product name, e.g. 'Saxo'.")
    profile_key: str = Field(min_length=1, description="Operating-model profile scored under.")
    c_index: Score
    module_scores: dict[str, Score] = Field(
        default_factory=dict, description="Per-C-module q_m, keyed to the registry's C module keys."
    )
    methodology_version: str = Field(min_length=1)
    coefficient_version: str = Field(min_length=1)
    # A non-committed provenance pointer to the source review (e.g. a review slug) — never the
    # review content itself, which stays the founder's IP (read reference-only, never committed).
    source_ref: str | None = None
    approved: bool = False
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    ingested_at: datetime

    @model_validator(mode="after")
    def _approval_is_consistent(self) -> CBenchmarkRow:
        """`approved` ⟺ both `approved_by` and `approved_at` are set — the ADR-0009
        recorded-approval invariant, so an approved row can't lack its approver/timestamp, nor
        the reverse."""
        stamped = self.approved_by is not None and self.approved_at is not None
        if self.approved != stamped:
            raise ValueError(
                "A C benchmark row is approved IFF it records both approved_by and approved_at "
                "(ADR-0009): AI proposes, a human approves, and the approval is recorded."
            )
        return self
