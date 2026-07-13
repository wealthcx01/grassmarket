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

from bcap_contracts.assessments import (
    Assessment,
    AssessmentDocument,
    LiveScore,
    ModuleRatingDraft,
    SubcomponentRating,
)
from bcap_contracts.registry import load_registry
from bcap_contracts.value import ScenarioComparison
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from grassmarket.assessments import (
    compute_score,
    consensus_blockers,
    evaluate_scenarios,
    live_score,
    module_rating_errors,
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


class AssignRaterRequest(BaseModel):
    rater_consultant_id: UUID


class ModuleRatingRequest(BaseModel):
    """A rater's ratings for one module's subcomponents (governance workflow, Methodology §9)."""

    ratings: list[SubcomponentRating] = []


class ConsensusRequest(BaseModel):
    """The lead's resolved (agreed) ratings for a module's assessed subcomponents. `rater_ids` and
    `consensus` are computed server-side from the submitted drafts — anything sent is ignored."""

    resolved: list[SubcomponentRating] = []


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
    # Dual-rating governance (Methodology §9): solo ratings are drafts, never deliverables.
    governance = consensus_blockers(assessment.document)
    if governance:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot finalise — dual-rating consensus incomplete: " + " ".join(governance),
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


# --- Dual-rating governance (Methodology §9) --------------------------------------------
# Two raters per module, working blind of each other until both submit; the lead resolves consensus
# per subcomponent with a mandatory dissent note where they differed. Assignment and consensus are
# the lead's authority (assessment owner); a rater fills only their own blind draft. Scope-refusals
# are 404 (never reveal the assessment); state/consensus refusals are 409; a bad key is 422.


def _conflict(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


def _require_known_module(module_key: str) -> None:
    if module_key not in load_registry().module_keys():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown module {module_key!r}."
        )


def _reject_stray_subcomponents(module_key: str, ratings: list[SubcomponentRating]) -> None:
    errors = module_rating_errors(module_key, tuple(ratings), load_registry())
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=" ".join(errors)
        )


@router.post(
    "/{assessment_id}/modules/{module_key}/raters",
    response_model=ModuleRatingDraft,
    status_code=status.HTTP_201_CREATED,
)
def assign_rater(
    assessment_id: UUID,
    module_key: str,
    payload: AssignRaterRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> ModuleRatingDraft:
    """The lead assigns a rater to a module (creates their empty blind draft). Assign at least two
    per module — a solo-rated module can never finalise."""
    _require_known_module(module_key)
    try:
        return repo.assign_rater(
            principal,
            assessment_id,
            module_key=module_key,
            rater_consultant_id=payload.rater_consultant_id,
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found(exc) from exc
    except ConflictError as exc:
        raise _conflict(exc) from exc


@router.get("/{assessment_id}/modules/{module_key}/my-rating", response_model=ModuleRatingDraft)
def get_my_module_rating(
    assessment_id: UUID,
    module_key: str,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> ModuleRatingDraft:
    """The caller's own blind draft for a module (hidden from co-raters until all submit)."""
    try:
        return repo.get_own_module_draft(principal, assessment_id, module_key)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found(exc) from exc


@router.put("/{assessment_id}/modules/{module_key}/my-rating", response_model=ModuleRatingDraft)
def update_my_module_rating(
    assessment_id: UUID,
    module_key: str,
    payload: ModuleRatingRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> ModuleRatingDraft:
    """A rater fills in their own draft. Refused once submitted (409) or on stray subcomponents."""
    _reject_stray_subcomponents(module_key, payload.ratings)
    try:
        return repo.update_own_module_draft(
            principal, assessment_id, module_key, ratings=tuple(payload.ratings)
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found(exc) from exc
    except ConflictError as exc:
        raise _conflict(exc) from exc


@router.post(
    "/{assessment_id}/modules/{module_key}/my-rating/submit", response_model=ModuleRatingDraft
)
def submit_my_module_rating(
    assessment_id: UUID,
    module_key: str,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> ModuleRatingDraft:
    """Lock the caller's own draft. The blind opens (co-raters become visible) once all have."""
    try:
        return repo.submit_own_module_draft(principal, assessment_id, module_key)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found(exc) from exc
    except ConflictError as exc:
        raise _conflict(exc) from exc


@router.get("/{assessment_id}/modules/{module_key}/ratings", response_model=list[ModuleRatingDraft])
def list_module_ratings(
    assessment_id: UUID,
    module_key: str,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[ModuleRatingDraft]:
    """The consensus screen: every rater's draft for a module — but a co-rater's is withheld until
    all have submitted, so the blind holds. Reachable by the lead, an assigned rater, or admin."""
    try:
        return repo.list_module_drafts(principal, assessment_id, module_key)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found(exc) from exc


@router.post("/{assessment_id}/modules/{module_key}/consensus", response_model=Assessment)
def resolve_module_consensus(
    assessment_id: UUID,
    module_key: str,
    payload: ConsensusRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Assessment:
    """The lead records the agreed rating per assessed subcomponent (with a dissent note where the
    raters differed), writing it into the assessment document. Needs ≥2 raters, all submitted."""
    _reject_stray_subcomponents(module_key, payload.resolved)
    try:
        return repo.resolve_module_consensus(
            principal, assessment_id, module_key, resolved=tuple(payload.resolved)
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found(exc) from exc
    except ConflictError as exc:
        raise _conflict(exc) from exc
