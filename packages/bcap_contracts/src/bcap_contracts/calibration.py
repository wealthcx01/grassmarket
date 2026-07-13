"""Calibration contracts (GRS-0022, Methodology §9) — inter-rater reliability as managed data.

Quarterly, all active assessors rate a few shared case vignettes on the maturity scale; per anchor
(a subcomponent) the weighted kappa and Gwet's AC1 measure how much they agree, and anchors below
κ 0.6 are flagged for rewrite. The vignettes double as Practice Arena content (GRS-0025).

Collection is **blind**: an assessor submits their own ratings while the session is OPEN and can
never see the aggregate distribution or the coefficients until the facilitator CLOSES the session —
so a late rater cannot anchor on what others said (that would defeat the measurement). The result is
computed once, on close, from every submitted rating, and is immutable thereafter.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from bcap_contracts.base import OwnedResource
from bcap_contracts.common import MaturityLevel


class CalibrationStatus(StrEnum):
    """A session collects while OPEN and is scored once, on CLOSE. Results exist only if CLOSED."""

    OPEN = "open"
    CLOSED = "closed"


class VignetteAnchor(BaseModel):
    """One thing a vignette asks an assessor to rate: a subcomponent, with the facilitator's
    reference level (the 'model answer' — used for Practice Arena scoring and misgrading direction,
    not for the inter-rater coefficients, which are assessor-vs-assessor)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subcomponent_key: str = Field(min_length=1)
    reference_level: MaturityLevel


class CalibrationVignette(BaseModel):
    """A shared case excerpt and the anchors it asks assessors to rate."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)
    anchors: tuple[VignetteAnchor, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _anchors_are_distinct(self) -> CalibrationVignette:
        keys = [a.subcomponent_key for a in self.anchors]
        if len(set(keys)) != len(keys):
            raise ValueError("A vignette rates each subcomponent at most once (distinct anchors).")
        return self


class CalibrationSession(OwnedResource):
    """A calibration round owned by its facilitator. Holds the shared vignettes; its status gates
    blind (OPEN collects, CLOSED reveals); the computed result is stamped on close."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    status: CalibrationStatus = CalibrationStatus.OPEN
    vignettes: tuple[CalibrationVignette, ...] = Field(min_length=1)
    opened_at: datetime
    closed_at: datetime | None = None


class RatingEntry(BaseModel):
    """One assessor's rating of one vignette anchor."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    vignette_index: int = Field(ge=0)
    subcomponent_key: str = Field(min_length=1)
    level: MaturityLevel


class CalibrationRating(OwnedResource):
    """One assessor's blind rating set for a session. `owner_consultant_id` is the assessor. Locked
    on submit; invisible to co-raters (and to the results) until the session closes."""

    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    entries: tuple[RatingEntry, ...] = ()
    submitted: bool = False
    submitted_at: datetime | None = None

    @model_validator(mode="after")
    def _submit_is_stamped(self) -> CalibrationRating:
        if self.submitted != (self.submitted_at is not None):
            raise ValueError(
                "A submitted rating carries a submitted_at timestamp; the two move together."
            )
        return self

    @model_validator(mode="after")
    def _entries_are_distinct(self) -> CalibrationRating:
        keys = [(e.vignette_index, e.subcomponent_key) for e in self.entries]
        if len(set(keys)) != len(keys):
            raise ValueError(
                "A rating has at most one entry per (vignette, anchor) — a duplicate would be "
                "silently dropped at compute (Methodology §9, fail-loud)."
            )
        return self


class AnchorAgreement(BaseModel):
    """The per-anchor inter-rater result. `kappa_w` is the target (≥0.75); `flagged` is True when it
    is below the 0.6 rewrite threshold (§9). `ac1` is reported alongside (skew-robust)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subcomponent_key: str
    n_raters: int = Field(ge=2)
    n_vignettes: int = Field(ge=1)
    # Chance-corrected agreement coefficients ∈ [-1, 1] (kappa can be negative), so NOT Score/[0,1].
    kappa_w: float = Field(ge=-1.0, le=1.0)
    ac1: float = Field(ge=-1.0, le=1.0)
    flagged: bool = Field(description="kappa_w below the 0.6 rewrite threshold (§9).")


class CalibrationResult(BaseModel):
    """A closed session's computed agreement, per anchor, plus the flagged-anchor report."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: UUID
    computed_at: datetime
    n_raters: int = Field(ge=2)
    anchors: tuple[AnchorAgreement, ...]

    @property
    def flagged_anchors(self) -> tuple[AnchorAgreement, ...]:
        return tuple(a for a in self.anchors if a.flagged)
