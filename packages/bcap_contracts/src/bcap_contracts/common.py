"""The shared scale vocabulary and enums — ADR-0001's single source of truth.

Every scale in ATLAS is defined here **once** and re-exported everywhere else. There is no
second definition of the maturity scale, the evidence grades, or the strength ratings. This
is the mechanism that closes feasibility defect D8 (four conflicting scales) and underpins the
registry defence against D1–D7.

Nothing in this module imports from the resource models, so it can be depended on freely.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import Field

# --- Score domain (ADR-0001 §1, ADR-0002 §4) --------------------------------------------
# All continuous indices — q_m, B, P, L, V — live in the closed interval [0, 1] internally.
# The display layer (and only the display layer) multiplies by 100. A `Score` is dimensionless
# and is NEVER money: no operator in this package combines a Score and a Money (see money.py).
Score = Annotated[float, Field(ge=0.0, le=1.0)]

# A blend parameter α (per module and α_L). The prototype's seed value of 2.0 (defect D3) is
# not constructible where this bound is applied.
UnitInterval = Annotated[float, Field(ge=0.0, le=1.0)]


class MaturityLevel(StrEnum):
    """The four maturity levels (Methodology §3.1).

    The numeric ``index`` is for computation only; clients see the label. These four indices
    are the ONLY legal subcomponent indices — any other value is a contract violation, not a
    datum to clamp or round (ADR-0001 §1).
    """

    BASIC = "Basic"
    DEVELOPING = "Developing"
    ADVANCED = "Advanced"
    FRONTIER = "Frontier"

    @property
    def score_index(self) -> float:
        """The computation-only numeric index (0.2/0.5/0.8/1.0). Named `score_index` rather than
        `index` to avoid shadowing `str.index` (StrEnum inherits from str)."""
        return _MATURITY_INDEX[self]

    @property
    def rank(self) -> int:
        """Ordinal rank 1..4, for gate comparisons (Basic < Developing < Advanced < Frontier)."""
        return _MATURITY_RANK[self]


_MATURITY_INDEX: dict[MaturityLevel, float] = {
    MaturityLevel.BASIC: 0.2,
    MaturityLevel.DEVELOPING: 0.5,
    MaturityLevel.ADVANCED: 0.8,
    MaturityLevel.FRONTIER: 1.0,
}
_MATURITY_RANK: dict[MaturityLevel, int] = {
    MaturityLevel.BASIC: 1,
    MaturityLevel.DEVELOPING: 2,
    MaturityLevel.ADVANCED: 3,
    MaturityLevel.FRONTIER: 4,
}

# The only legal subcomponent indices. Frozen so it can be a set-membership guard.
LEGAL_MATURITY_INDICES: frozenset[float] = frozenset(_MATURITY_INDEX.values())


class NonScoreState(StrEnum):
    """First-class non-score states (Methodology §3.2). Never imputed, never scored as zero.

    An unassessed subcomponent contributes to NO score — the empty-module → q_m = 0.0
    behaviour of the prototype (defect D9) is prohibited by construction.
    """

    NOT_APPLICABLE = "Not Applicable"  # out of scope; removed from denominator, weights renorm
    NOT_ASSESSED = "Not Assessed"  # in scope but not evidenced; widens uncertainty / blocks gate


class EvidenceGrade(StrEnum):
    """Evidence-strength grade (Methodology §3.3). Drives uncertainty (§7), not the point score."""

    E1_SELF_REPORTED = "E1"
    E2_INTERVIEW = "E2"
    E3_ARTIFACT = "E3"
    E4_OBSERVED = "E4"

    @property
    def rank(self) -> int:
        return {"E1": 1, "E2": 2, "E3": 3, "E4": 4}[self.value]


class MetricConfidence(StrEnum):
    """Source/recency grade for a business-metric observation (Methodology v1.2 §7, ADR-0008).

    Drives the Monte Carlo distribution width on a metric's raw value the way an evidence grade
    drives a subcomponent's — a coarse read of how much the reported number could move under a
    better source or fresher data. Audited/current is tight; an estimate is wide. Reported as a
    grade, never a decimal (the width is a coefficient, ADR-0008)."""

    ESTIMATED = "estimated"  # derived / stale — widest
    SELF_REPORTED = "self_reported"
    MANAGEMENT = "management_reported"  # management accounts
    AUDITED = "audited"  # audited / current filings — tightest

    @property
    def rank(self) -> int:
        """Ordinal rank 1..4 (estimated weakest → audited strongest), mirroring EvidenceGrade."""
        return {"estimated": 1, "self_reported": 2, "management_reported": 3, "audited": 4}[
            self.value
        ]


class StrengthRating(StrEnum):
    """Power strength and triad rating — ordinal with falsifiable duration semantics (§8).

    Reported as a rating, NEVER as a decimal. Establishing this as an enum (not a float) is the
    ADR-0002 guarantee that no decimal leaks into a triad figure.
    """

    NONE = "None"
    EMERGING = "Emerging"
    ESTABLISHED = "Established"  # "more likely than not to persist 5+ years"
    WIDE = "Wide"  # "near-certain 5, likely 10+ years"


class TrendDirection(StrEnum):
    IMPROVING = "improving"
    STABLE = "stable"
    ERODING = "eroding"


class TriadDimension(StrEnum):
    """The Platform Power triad (Methodology §2), reported as ordinal StrengthRatings."""

    ECONOMIC_VALUE = "economic_value"
    PERCEIVED_VALUE = "perceived_value"
    DEFENCE_VALUE = "defence_value"


class UncertaintyRating(StrEnum):
    """Assessment Uncertainty Rating (Methodology §7), Morningstar pattern."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    VERY_HIGH = "Very High"


class PowerLifecycleStage(StrEnum):
    """Helmer Power Progression window a power is acquirable in (Methodology §8)."""

    ORIGINATION = "origination"
    TAKEOFF = "takeoff"
    STABILITY = "stability"


# --- Identity / access enums (Holy Corner claim shape, PRD §2) --------------------------


class Role(StrEnum):
    """Coarse RBAC role. Data scoping is by ownership (repository layer), not by role;
    ADMIN and COMMITTEE_MEMBER widen *visibility* only where the Methodology requires it."""

    CONSULTANT = "consultant"
    COMMITTEE_MEMBER = "committee_member"
    ADMIN = "admin"


class ConsultantTier(StrEnum):
    """Advisory Network tier (PRD §2)."""

    VENTURE_ASSOCIATE = "venture_associate"
    ADVISOR = "advisor"
    CONSULTANT = "consultant"


class AssessorLevel(StrEnum):
    """Certification ladder (Methodology §9). High-stakes ratings require CERTIFIED_LEAD."""

    TRAINED = "trained"
    SHADOW = "shadow"
    OBSERVED_LEAD = "observed_lead"
    CERTIFIED_LEAD = "certified_lead"


class WeightMethod(StrEnum):
    """Elicitation method recorded in a Weight Provenance Record (Methodology §6)."""

    SWING_WEIGHTING = "swing_weighting"
    AHP = "ahp"
    DELPHI = "delphi"
    COOKE = "cooke_classical"
    DIRECT = "direct"  # only for structural constants, never for elicited weights
