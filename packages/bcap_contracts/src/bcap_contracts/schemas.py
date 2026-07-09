"""JSON Schema export + parity check — the mechanism behind the `schema-validate` pre-commit
hook. Committed schemas are a faithful mirror of the Pydantic models; schemas win on conflict
(CLAUDE.md non-negotiable #4). If a model changes but the schema is not regenerated, parity
fails loud and the commit is blocked — no silent drift (a class of the D8 gap).
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from bcap_contracts.assessments import (
    Assessment,
    AssessmentDocument,
    CoefficientSet,
    LiveScore,
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
from bcap_contracts.commissions import CommissionLine
from bcap_contracts.deliverables import Deliverable
from bcap_contracts.engagements import Engagement, Workshop
from bcap_contracts.entities import Prospect
from bcap_contracts.learning import CertificationProgress, DrillResult
from bcap_contracts.money import Money
from bcap_contracts.pipeline import PipelineBoard, PipelineForecast
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
    "LiveScore": LiveScore,
    "ScenarioComparison": ScenarioComparison,
    "RubricAnchor": RubricAnchor,
    "Registry": Registry,
    "Prospect": Prospect,
    "PipelineForecast": PipelineForecast,
    "PipelineBoard": PipelineBoard,
    "Engagement": Engagement,
    "Workshop": Workshop,
    "Deliverable": Deliverable,
    "CommissionLine": CommissionLine,
    "CertificationProgress": CertificationProgress,
    "DrillResult": DrillResult,
    "JWTClaims": JWTClaims,
    "Consultant": Consultant,
    "Invitation": Invitation,
    "LoginRequest": LoginRequest,
    "TokenResponse": TokenResponse,
    "AcceptInvitationRequest": AcceptInvitationRequest,
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
