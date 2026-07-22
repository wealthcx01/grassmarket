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
    BrokeragePortfolioEntry,
    CoefficientSet,
    LiveScore,
    ModuleRatingDraft,
    RecordProvenance,
    SubcomponentRating,
)
from bcap_contracts.common import AssessorLevel
from bcap_contracts.product_fit import SellOpportunities
from bcap_contracts.registry import Registry, UnknownKeyError, load_registry
from bcap_contracts.value import ScenarioComparison
from bcap_contracts.wizard import WizardSuggestions
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
from grassmarket.assessments.suggester import SUGGESTER_VERSION, suggest_for
from grassmarket.atlas.active import (
    active_uncertainty_model,
    profile_key_of,
    profile_scoring_context,
)
from grassmarket.atlas.committee import committee_blockers, required_committee_items
from grassmarket.data.repository import (
    ConflictError,
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
from grassmarket.entities import active_entity_registry
from grassmarket.web.dependencies import get_current_principal, get_repository
from grassmarket.workbench.certification import requires_certified_lead

router = APIRouter(prefix="/assessments", tags=["assessments"])

# A fixed seed so the live band is deterministic for a given document (no flicker on refresh). The
# RNG is injected per request (never module-global) — the GRS-0005 discipline.
_LIVE_SEED = 20260706


class CreateAssessmentRequest(BaseModel):
    subject: str = ""
    # ADR-0029: a sandbox record self-approves (solo finalise, watermarked, non-promotable). Default
    # production — the full dual-rating + committee gate. Demo records are seeded server-side.
    provenance: RecordProvenance = RecordProvenance.PRODUCTION
    # GRS-0100/ADR-0033: the canonical company the subject resolved to; null for a manual subject.
    entity_id: str | None = None


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


def _profile_context(document: AssessmentDocument) -> tuple[Registry, CoefficientSet]:
    """The (registry VIEW, coefficient set) an assessment scores against, by its operating-model
    profile (ADR-0025/GRS-0079). Retail (default) is byte-identical to the full registry. An
    unknown profile key on the document is a 422 (fail loud, never a silent retail fallback)."""
    try:
        return profile_scoring_context(profile_key_of(document))
    except UnknownKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.post("", response_model=Assessment, status_code=status.HTTP_201_CREATED)
def create_assessment(
    payload: CreateAssessmentRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Assessment:
    # A client may create a production or a sandbox record; demo records are seeded server-side,
    # never accepted from a client request (ADR-0029).
    provenance = (
        RecordProvenance.SANDBOX
        if payload.provenance is RecordProvenance.SANDBOX
        else RecordProvenance.PRODUCTION
    )
    # A supplied entity_id must be a real registry entity — a fabricated link can never be stored
    # (GRS-0100/ADR-0033, fail loud #3). Null is the explicit manual/unlinked fallback.
    if payload.entity_id is not None and active_entity_registry().get(payload.entity_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown company entity '{payload.entity_id}'.",
        )
    return repo.create_assessment(
        principal, subject=payload.subject, provenance=provenance, entity_id=payload.entity_id
    )


@router.get("/for-entity/{entity_id}", response_model=list[Assessment])
def list_assessments_for_entity(
    entity_id: str,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[Assessment]:
    """The caller's own assessments of one canonical company (GRS-0100 dedup legibility) — so the
    advisor sees "you already have N assessments of this company" before starting another."""
    return repo.list_assessments_for_entity(principal, entity_id)


@router.get("", response_model=list[Assessment])
def list_assessments(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[Assessment]:
    return repo.list_assessments(principal)


# Declared BEFORE `/{assessment_id}` so "portfolio" isn't parsed as an assessment UUID.
@router.get("/portfolio", response_model=list[BrokeragePortfolioEntry])
def brokerage_portfolio(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[BrokeragePortfolioEntry]:
    """The advisor's "Your Brokerages" home — one summary row per assessment (segment, last score,
    status, last updated), newest-touched first. Self-scoped."""
    return repo.list_brokerage_portfolio(principal)


class RatingRequestSummary(BaseModel):
    """One module the caller has been asked to rate (co-rater's work-queue, §9)."""

    assessment_id: UUID
    subject: str
    module_key: str
    module_name: str
    submitted: bool


# Declared BEFORE `/{assessment_id}` so "rating-requests" isn't parsed as an assessment UUID.
@router.get("/rating-requests", response_model=list[RatingRequestSummary])
def my_rating_requests(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[RatingRequestSummary]:
    """Every module the caller has been assigned to rate on an in-progress assessment — how a
    co-rater finds the ratings requested of them."""
    registry = load_registry()
    module_names = {m.key: m.name for m in registry.modules}
    return [
        RatingRequestSummary(
            assessment_id=draft.assessment_id,
            subject=subject or "Untitled assessment",
            module_key=draft.module_key,
            module_name=module_names.get(draft.module_key, draft.module_key),
            submitted=draft.submitted,
        )
        for draft, subject in repo.list_my_rating_assignments(principal)
    ]


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
    # Score against the document's operating-model profile view + coeffs (ADR-0025/GRS-0079);
    # retail (default) is byte-identical to before.
    registry, coefficients = _profile_context(assessment.document)
    return live_score(
        assessment.document,
        coefficients,
        registry,
        active_uncertainty_model(profile_key_of(assessment.document)),
        random.Random(_LIVE_SEED),
    )


@router.get("/{assessment_id}/sell-opportunities", response_model=SellOpportunities)
def get_sell_opportunities(
    assessment_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> SellOpportunities:
    """The deterministic "what can I sell against this report?" join (GRS-0162, ADR-0039):
    products whose authored fit addresses this assessment's assessed-and-weak targets, deepest gap
    first, with the live commission carrot alongside (never in the ordering). Owner-scoped;
    refused until finalised — the sales case quotes a locked score, not a moving draft.
    Advisor-facing only: never rendered into a client deliverable."""
    from grassmarket.earnings.opportunities import sell_opportunities

    try:
        assessment = repo.get_assessment(principal, assessment_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found(exc) from exc
    if assessment.state.value != "finalised":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sell opportunities read a locked score — finalise the assessment first.",
        )
    return sell_opportunities(assessment)


@router.get("/{assessment_id}/suggestions", response_model=WizardSuggestions)
def get_wizard_suggestions(
    assessment_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> WizardSuggestions:
    """AI-assisted input suggestions (GRS-0101 / ADR-0032): deterministic proposals derived from the
    current document. A finalised (locked) assessment returns none — there is nothing to assist.
    Owner-scoped; every proposal is applied only by the advisor's explicit accept/edit in the UI."""
    try:
        assessment = repo.get_assessment(principal, assessment_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found(exc) from exc
    if assessment.state.value == "finalised":
        return WizardSuggestions(
            assessment_id=assessment_id, suggester_version=SUGGESTER_VERSION, suggestions=()
        )
    registry, _ = _profile_context(assessment.document)
    return WizardSuggestions(
        assessment_id=assessment_id,
        suggester_version=SUGGESTER_VERSION,
        suggestions=tuple(suggest_for(assessment.document, registry)),
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
    registry, coefficients = _profile_context(assessment.document)
    named = [(s.name, s.document) for s in payload.scenarios]
    return evaluate_scenarios(assessment.document, named, coefficients, registry)


@router.post("/{assessment_id}/finalise", response_model=Assessment)
def finalise_assessment(
    assessment_id: UUID,
    override_reason: str | None = None,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Assessment:
    """Lock inputs and create the immutable scoring run. Refuses if already finalised or not yet
    scoreable — both 409. A Frontier module or Wide power requires a Certified Lead to lead the
    assessment (§9); an admin may override that with `override_reason`, which is audited."""
    try:
        assessment = repo.get_assessment(principal, assessment_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found(exc) from exc
    if assessment.state.value == "finalised":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already finalised.")

    # Finalise against the document's operating-model profile (ADR-0025/GRS-0079); the run records
    # WHICH profile scored it via the profile's distinct coefficient_version (immutable, #6).
    registry, coefficients = _profile_context(assessment.document)
    model = active_uncertainty_model(profile_key_of(assessment.document))
    blockers = scoreability_blockers(assessment.document, registry)
    if blockers:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot finalise — not yet scoreable: " + " ".join(blockers),
        )
    # Governance gate (dual-rating + committee + certification). A NON-PRODUCTION (demo/sandbox)
    # record self-approves: the owning tester may finalise their own record and run the REAL
    # deliverable generation WITHOUT a second rater or committee (ADR-0029). The record is
    # permanently watermarked, never ratified, never client-facing — the production gate below is
    # entirely unchanged for production records, so the AI-approval non-negotiable is intact.
    gated = assessment.provenance is RecordProvenance.PRODUCTION

    # Dual-rating governance (Methodology §9): solo ratings are drafts, never deliverables.
    governance = consensus_blockers(assessment.document) if gated else []
    if governance:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot finalise — dual-rating consensus incomplete: " + " ".join(governance),
        )

    art = compute_score(
        assessment.document, coefficients, registry, model, random.Random(_LIVE_SEED)
    )
    # Rating Committee sign-off on high-stakes ratings (Methodology §8): power Established+, triad
    # above None, module Frontier. Any awaiting sign-off blocks finalisation.
    committee = (
        committee_blockers(
            required_committee_items(art.result),
            repo.list_committee_decisions(principal, assessment_id),
        )
        if gated
        else []
    )
    if committee:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot finalise — Rating Committee sign-off incomplete: " + " ".join(committee),
        )
    # Certification (Methodology §9): a Frontier module or Wide power requires a Certified Lead to
    # lead the assessment. An admin may override with a recorded reason (fail-loud, audited).
    cert_reasons = requires_certified_lead(art.result) if gated else []
    if cert_reasons:
        owner = repo.get_consultant_by_id(assessment.owner_consultant_id)
        certified = owner is not None and owner.assessor_level is AssessorLevel.CERTIFIED_LEAD
        if not certified:
            if principal.is_admin and override_reason and override_reason.strip():
                repo.record_certification_override(
                    principal,
                    assessment.owner_consultant_id,
                    reason=override_reason,
                    detail="Finalise override: " + "; ".join(cert_reasons),
                    occurred_at=datetime.now(UTC),
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Cannot finalise — a Certified Lead must lead this assessment ("
                        + "; ".join(cert_reasons)
                        + "). An admin may override with a recorded reason."
                    ),
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
