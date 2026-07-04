"""App-facing contracts — re-exports from `bcap_contracts` plus any Grassmarket-local models.

Feature code imports contracts from here (`grassmarket.contracts`), not directly from
`bcap_contracts`, so the day a resource needs an app-local extension there is one seam to widen.
For Loop 0 this is a thin re-export; the shared package is the source of truth.
"""

from __future__ import annotations

from bcap_contracts import (
    AcceptInvitationRequest,
    AssessorLevel,
    CoefficientSet,
    Consultant,
    ConsultantTier,
    Currency,
    Deliverable,
    Engagement,
    EvidenceGrade,
    Invitation,
    JWTClaims,
    MaturityLevel,
    Money,
    NonScoreState,
    PipelineStage,
    Prospect,
    Registry,
    Role,
    Score,
    ScoringRun,
    StrengthRating,
    load_registry,
)

__all__ = [
    "AcceptInvitationRequest",
    "AssessorLevel",
    "CoefficientSet",
    "Consultant",
    "ConsultantTier",
    "Currency",
    "Deliverable",
    "Engagement",
    "EvidenceGrade",
    "Invitation",
    "JWTClaims",
    "MaturityLevel",
    "Money",
    "NonScoreState",
    "PipelineStage",
    "Prospect",
    "Registry",
    "Role",
    "Score",
    "ScoringRun",
    "StrengthRating",
    "load_registry",
]
