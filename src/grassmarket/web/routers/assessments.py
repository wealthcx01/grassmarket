"""Assessments router — the backend the Wizard Path A drives (GRS-0009).

Every handler is scoped through the repository (a consultant sees/edits only their own). At the HTTP
boundary a `ScopeViolationError` is a 404 (the API never reveals a resource it won't show exists).
Autosave persists a partial document without scoring; finalisation locks inputs and creates the
immutable scoring run; the live-score endpoint scores what it can and labels B/P honestly.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime
from uuid import UUID

from bcap_contracts.assessments import Assessment, AssessmentDocument, LiveScore
from bcap_contracts.registry import load_registry
from bcap_contracts.value import ScenarioComparison
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from grassmarket.assessments import (
    compute_score,
    evaluate_scenarios,
    live_score,
    scoreability_blockers,
)
from grassmarket.atlas.draft_coefficients import draft_v1_coefficient_set
from grassmarket.atlas.montecarlo import draft_v1_uncertainty_model
from grassmarket.data.repository import (
    ConflictError,
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(prefix="/assessments", tags=["assessments"])

# A fixed seed so the live band is deterministic for a given document (no flicker on refresh). The
# RNG is injected per request (never module-global) — the GRS-0005 discipline.
_LIVE_SEED = 20260706


class CreateAssessmentRequest(BaseModel):
    subject: str = ""


class NamedScenario(BaseModel):
    name: str
    document: AssessmentDocument


class ScenariosRequest(BaseModel):
    scenarios: list[NamedScenario]


def _not_found(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")


@router.post("", response_model=Assessment, status_code=status.HTTP_201_CREATED)
def create_assessment(
    payload: CreateAssessmentRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Assessment:
    return repo.create_assessment(principal, subject=payload.subject)


@router.get("", response_model=list[Assessment])
def list_assessments(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[Assessment]:
    return repo.list_assessments(principal)


@router.get("/{assessment_id}", response_model=Assessment)
def get_assessment(
    assessment_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Assessment:
    try:
        return repo.get_assessment(principal, assessment_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found(exc) from exc


@router.put("/{assessment_id}", response_model=Assessment)
def update_assessment(
    assessment_id: UUID,
    document: AssessmentDocument,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Assessment:
    """Autosave the (possibly partial) document. A finalised assessment refuses edits (409)."""
    try:
        return repo.update_assessment(principal, assessment_id, document=document)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found(exc) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{assessment_id}/live-score", response_model=LiveScore)
def get_live_score(
    assessment_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> LiveScore:
    try:
        assessment = repo.get_assessment(principal, assessment_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found(exc) from exc
    registry = load_registry()
    return live_score(
        assessment.document,
        draft_v1_coefficient_set(registry),
        registry,
        draft_v1_uncertainty_model(),
        random.Random(_LIVE_SEED),
    )


@router.post("/{assessment_id}/scenarios", response_model=ScenarioComparison)
def evaluate_assessment_scenarios(
    assessment_id: UUID,
    payload: ScenariosRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> ScenarioComparison:
    """Rank candidate upgrade scenarios against the assessment's baseline document by ΔV — the
    Upgrade Priority Index (score domain only, ADR-0002; no currency here)."""
    try:
        assessment = repo.get_assessment(principal, assessment_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found(exc) from exc
    registry = load_registry()
    named = [(s.name, s.document) for s in payload.scenarios]
    return evaluate_scenarios(
        assessment.document, named, draft_v1_coefficient_set(registry), registry
    )


@router.post("/{assessment_id}/finalise", response_model=Assessment)
def finalise_assessment(
    assessment_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Assessment:
    """Lock inputs and create the immutable scoring run. Refuses if already finalised or not yet
    scoreable — both 409 (the run and the lock happen in one transaction)."""
    try:
        assessment = repo.get_assessment(principal, assessment_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found(exc) from exc
    if assessment.state.value == "finalised":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already finalised.")

    registry = load_registry()
    coefficients = draft_v1_coefficient_set(registry)
    model = draft_v1_uncertainty_model()
    blockers = scoreability_blockers(assessment.document, registry)
    if blockers:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot finalise — not yet scoreable: " + " ".join(blockers),
        )

    art = compute_score(
        assessment.document, coefficients, registry, model, random.Random(_LIVE_SEED)
    )
    run = repo.create_scoring_run(
        principal,
        assessment_id=assessment_id,
        inputs=art.inputs,
        result=art.result,
        v_p10=art.uncertainty.v_band.p10,
        v_p90=art.uncertainty.v_band.p90,
        uncertainty_rating=art.uncertainty.overall_uncertainty.value,
        uncertainty_version=model.version,
    )
    try:
        return repo.finalise_assessment(
            principal,
            assessment_id,
            scoring_run_id=run.id,
            engine_version=art.result.engine_version,
            methodology_version=art.result.methodology_version,
            coefficient_version=art.result.coefficient_version,
            uncertainty_version=model.version,
            finalised_at=datetime.now(UTC),
        )
    except ConflictError as exc:  # a concurrent finalise won the race — roll back this run
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
