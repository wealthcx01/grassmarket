"""JSON Schema export + parity check — the mechanism behind the `schema-validate` pre-commit
hook. Committed schemas are a faithful mirror of the Pydantic models; schemas win on conflict
(CLAUDE.md non-negotiable #4). If a model changes but the schema is not regenerated, parity
fails loud and the commit is blocked — no silent drift (a class of the D8 gap).
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from bcap_contracts.arena import ArenaScenario, ArenaSession
from bcap_contracts.assessments import (
    Assessment,
    AssessmentDocument,
    BrokeragePortfolioEntry,
    CoefficientSet,
    LiveScore,
    ModuleRatingDraft,
    PowerAssessment,
    ScoringRun,
    SubcomponentRating,
    TriadResult,
)
from bcap_contracts.audit import AuditEvent, PersonalDataExport
from bcap_contracts.auth import (
    AcceptInvitationRequest,
    Consultant,
    Invitation,
    JWTClaims,
    LoginRequest,
    TokenResponse,
)
from bcap_contracts.bench import BenchQueue, PerformanceSummary
from bcap_contracts.calibration import (
    CalibrationRating,
    CalibrationResult,
    CalibrationSession,
)
from bcap_contracts.certification import CertificationEvent, CertificationRecord
from bcap_contracts.commissions import CommissionLine, EarningsSummary
from bcap_contracts.committee import CommitteeDecision, CommitteeItem, CommitteeQueueEntry
from bcap_contracts.deliverables import Deliverable
from bcap_contracts.engagements import CommsLogEntry, Engagement, Workshop
from bcap_contracts.entities import Prospect
from bcap_contracts.extraction import Extraction, FieldProvenance
from bcap_contracts.fees import RecoveryFeeAttribution
from bcap_contracts.learning import (
    CertificationProgress,
    ContentCompletion,
    DrillCard,
    DrillResult,
    GeneratedQuiz,
    LearningModule,
)
from bcap_contracts.meetings import MeetingTranscript
from bcap_contracts.money import Money
from bcap_contracts.narratives import AINarrative
from bcap_contracts.pipeline import PipelineBoard, PipelineForecast
from bcap_contracts.predictions import BenchmarkRow, Prediction
from bcap_contracts.provenance import WeightProvenanceRecord
from bcap_contracts.registry import Registry
from bcap_contracts.rubric import RubricAnchor
from bcap_contracts.value import ScenarioComparison

# The exported surface. Adding a resource means adding it here and regenerating — deliberate
# friction so the contract surface is always explicit and mirrored.
EXPORTED_MODELS: dict[str, type[BaseModel]] = {
    "Money": Money,
    "WeightProvenanceRecord": WeightProvenanceRecord,
    "CoefficientSet": CoefficientSet,
    "SubcomponentRating": SubcomponentRating,
    "PowerAssessment": PowerAssessment,
    "TriadResult": TriadResult,
    "ScoringRun": ScoringRun,
    "AssessmentDocument": AssessmentDocument,
    "Assessment": Assessment,
    "BrokeragePortfolioEntry": BrokeragePortfolioEntry,
    "ModuleRatingDraft": ModuleRatingDraft,
    "LiveScore": LiveScore,
    "ScenarioComparison": ScenarioComparison,
    "RubricAnchor": RubricAnchor,
    "Registry": Registry,
    "Prospect": Prospect,
    "PipelineForecast": PipelineForecast,
    "PipelineBoard": PipelineBoard,
    "Engagement": Engagement,
    "CommsLogEntry": CommsLogEntry,
    "Workshop": Workshop,
    "RecoveryFeeAttribution": RecoveryFeeAttribution,
    "Deliverable": Deliverable,
    "AINarrative": AINarrative,
    "CommissionLine": CommissionLine,
    "EarningsSummary": EarningsSummary,
    "MeetingTranscript": MeetingTranscript,
    "Extraction": Extraction,
    "FieldProvenance": FieldProvenance,
    "Prediction": Prediction,
    "BenchmarkRow": BenchmarkRow,
    "CommitteeItem": CommitteeItem,
    "CommitteeDecision": CommitteeDecision,
    "CommitteeQueueEntry": CommitteeQueueEntry,
    "CalibrationSession": CalibrationSession,
    "CalibrationRating": CalibrationRating,
    "CalibrationResult": CalibrationResult,
    "CertificationRecord": CertificationRecord,
    "CertificationEvent": CertificationEvent,
    "CertificationProgress": CertificationProgress,
    "DrillResult": DrillResult,
    "DrillCard": DrillCard,
    "LearningModule": LearningModule,
    "ContentCompletion": ContentCompletion,
    "GeneratedQuiz": GeneratedQuiz,
    "ArenaScenario": ArenaScenario,
    "ArenaSession": ArenaSession,
    "BenchQueue": BenchQueue,
    "PerformanceSummary": PerformanceSummary,
    "JWTClaims": JWTClaims,
    "Consultant": Consultant,
    "Invitation": Invitation,
    "LoginRequest": LoginRequest,
    "TokenResponse": TokenResponse,
    "AcceptInvitationRequest": AcceptInvitationRequest,
    "AuditEvent": AuditEvent,
    "PersonalDataExport": PersonalDataExport,
}

_SCHEMA_DIR = Path(__file__).parent / "json_schema"


def _render(model: type[BaseModel]) -> str:
    """Deterministic JSON: sorted keys, 2-space indent, trailing newline (matches the
    end-of-file-fixer hook so parity is byte-stable)."""
    schema = model.model_json_schema()
    return json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _schema_path(name: str) -> Path:
    return _SCHEMA_DIR / f"{name}.json"


def export_all() -> list[Path]:
    """(Re)write every committed schema from the models. Returns the paths written."""
    _SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, model in EXPORTED_MODELS.items():
        path = _schema_path(name)
        path.write_text(_render(model), encoding="utf-8")
        written.append(path)
    return written


def check_parity() -> list[str]:
    """Return the names of models whose committed schema is missing or stale. Empty == in sync."""
    mismatches: list[str] = []
    for name, model in EXPORTED_MODELS.items():
        path = _schema_path(name)
        expected = _render(model)
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            mismatches.append(name)
    return mismatches
