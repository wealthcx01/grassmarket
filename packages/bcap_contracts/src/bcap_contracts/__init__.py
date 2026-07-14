"""bcap-contracts — shared Bruntsfield Capital contracts (the future Holy Corner API surface).

Import the scale vocabulary, the registry, and the resource models from here. Two invariants
this package guarantees structurally: ADR-0001 (one scale, one registry; unknown key = refusal)
and ADR-0002 (score and currency never mix).
"""

from __future__ import annotations

from bcap_contracts.arena import (
    ArenaScenario,
    ArenaScore,
    ArenaSession,
    ArenaSpeaker,
    ArenaStatus,
    ArenaTurn,
    PowerProbeResult,
)
from bcap_contracts.assessments import (
    CoefficientSet,
    ModuleRatingDraft,
    PowerAssessment,
    ScoringRun,
    SubcomponentRating,
    TriadResult,
)
from bcap_contracts.auth import (
    AcceptInvitationRequest,
    Consultant,
    Invitation,
    JWTClaims,
    LoginRequest,
    TokenResponse,
)
from bcap_contracts.bench import (
    ArenaTrendPoint,
    BenchItemKind,
    BenchQueue,
    BenchQueueItem,
    PerformanceSummary,
)
from bcap_contracts.calibration import (
    AnchorAgreement,
    CalibrationRating,
    CalibrationResult,
    CalibrationSession,
    CalibrationStatus,
    CalibrationVignette,
    RatingEntry,
    VignetteAnchor,
)
from bcap_contracts.certification import (
    CertificationEvent,
    CertificationEventKind,
    CertificationRecord,
)
from bcap_contracts.commissions import (
    CommissionConfig,
    CommissionKind,
    CommissionLine,
    EarningsSummary,
    PaymentStatus,
    SourcingAttribution,
    load_commission_config,
)
from bcap_contracts.committee import (
    CommitteeDecision,
    CommitteeDecisionStatus,
    CommitteeItem,
    CommitteeItemType,
    CommitteeQueueEntry,
)
from bcap_contracts.common import (
    AssessorLevel,
    ConsultantTier,
    EvidenceGrade,
    MaturityLevel,
    NonScoreState,
    PowerLifecycleStage,
    Role,
    Score,
    StrengthRating,
    TrendDirection,
    TriadDimension,
    UncertaintyRating,
    UnitInterval,
    WeightMethod,
)
from bcap_contracts.deliverables import ApprovalStatus, Deliverable, DeliverableType
from bcap_contracts.engagements import Engagement, EngagementStatus, Workshop
from bcap_contracts.entities import PipelineStage, Prospect
from bcap_contracts.learning import (
    CertificationCredit,
    CertificationProgress,
    ContentCompletion,
    DrillCard,
    DrillResult,
    GeneratedQuiz,
    LearningKind,
    LearningModule,
    QuizQuestion,
    QuizStatus,
)
from bcap_contracts.meetings import MediaKind, MeetingTranscript
from bcap_contracts.money import Currency, Money
from bcap_contracts.provenance import WeightProvenanceRecord
from bcap_contracts.registry import (
    AnchorPoint,
    EmptyDimensionError,
    MetricDef,
    MissingKeyError,
    ModuleDef,
    NormalisationSpec,
    PowerDef,
    Registry,
    RegistryError,
    SubcomponentDef,
    UnknownKeyError,
    load_registry,
)

__all__ = [
    # scale vocabulary
    "Score",
    "UnitInterval",
    "MaturityLevel",
    "NonScoreState",
    "EvidenceGrade",
    "StrengthRating",
    "TrendDirection",
    "TriadDimension",
    "UncertaintyRating",
    "PowerLifecycleStage",
    "WeightMethod",
    "Role",
    "ConsultantTier",
    "AssessorLevel",
    # money (ADR-0002)
    "Currency",
    "Money",
    # provenance
    "WeightProvenanceRecord",
    # registry (ADR-0001)
    "Registry",
    "RegistryError",
    "UnknownKeyError",
    "MissingKeyError",
    "EmptyDimensionError",
    "ModuleDef",
    "PowerDef",
    "SubcomponentDef",
    "MetricDef",
    "AnchorPoint",
    "NormalisationSpec",
    "load_registry",
    # assessments
    "CoefficientSet",
    "SubcomponentRating",
    "PowerAssessment",
    "TriadResult",
    "ScoringRun",
    "ModuleRatingDraft",
    # resources
    "Prospect",
    "PipelineStage",
    "Engagement",
    "EngagementStatus",
    "Workshop",
    "Deliverable",
    "DeliverableType",
    "ApprovalStatus",
    "CommissionLine",
    "CommissionKind",
    "CommissionConfig",
    "EarningsSummary",
    "SourcingAttribution",
    "PaymentStatus",
    "load_commission_config",
    "MeetingTranscript",
    "MediaKind",
    "CommitteeItem",
    "CommitteeItemType",
    "CommitteeDecision",
    "CommitteeDecisionStatus",
    "CommitteeQueueEntry",
    "CalibrationSession",
    "CalibrationRating",
    "CalibrationResult",
    "CalibrationStatus",
    "CalibrationVignette",
    "VignetteAnchor",
    "RatingEntry",
    "AnchorAgreement",
    "CertificationRecord",
    "CertificationEvent",
    "CertificationEventKind",
    "CertificationProgress",
    "DrillResult",
    "DrillCard",
    "LearningModule",
    "LearningKind",
    "CertificationCredit",
    "ContentCompletion",
    "GeneratedQuiz",
    "QuizStatus",
    "QuizQuestion",
    "ArenaScenario",
    "ArenaSession",
    "ArenaScore",
    "ArenaTurn",
    "ArenaSpeaker",
    "ArenaStatus",
    "PowerProbeResult",
    "BenchQueue",
    "BenchQueueItem",
    "BenchItemKind",
    "PerformanceSummary",
    "ArenaTrendPoint",
    # auth
    "JWTClaims",
    "Consultant",
    "Invitation",
    "LoginRequest",
    "TokenResponse",
    "AcceptInvitationRequest",
]
