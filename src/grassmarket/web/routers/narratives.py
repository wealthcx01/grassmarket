"""AI narrative router (GRS-0017, PRD §5). Propose AI first drafts for a deliverable's sections,
approve them with a human sign-off (seniority-gated), and list them.

'AI proposes, humans approve' is enforced here at runtime (non-negotiable #8): a proposal is only
ever a draft; approval records the approver, timestamp, final text, and an edit diff, and a
junior-tier author's narrative needs senior (Consultant-tier) approval (the PRD §5 quality gate).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from bcap_contracts.narratives import AINarrative, NarrativeSection
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from grassmarket.atlas.results import AtlasResult
from grassmarket.data.repository import (
    NotFoundError,
    Principal,
    Repository,
    RepositoryError,
    ScopeViolationError,
)
from grassmarket.deliverables.gate import SeniorApprovalError, assert_senior_approval
from grassmarket.deliverables.narrative import (
    TemplateNarrativeDrafter,
    context_from_result,
    edit_summary,
)
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(tags=["narratives"])

_DRAFTER = TemplateNarrativeDrafter()


class ProposeNarrativesRequest(BaseModel):
    # Default: draft all three sections. A subset may be requested.
    sections: list[NarrativeSection] = list(NarrativeSection)


class ApproveNarrativeRequest(BaseModel):
    # The final text a human signs off on. Omitted → approve the proposal verbatim.
    final_text: str | None = None


def _not_found(detail: str = "Not found.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _principal_tier(repo: Repository, principal: Principal):
    consultant = repo.get_consultant_by_id(principal.consultant_id)
    if consultant is None:  # a valid token whose consultant vanished — fail loud, never default
        raise _not_found("Authenticated consultant not found.")
    return consultant.tier


@router.post(
    "/deliverables/{deliverable_id}/narratives",
    response_model=list[AINarrative],
    status_code=status.HTTP_201_CREATED,
)
def propose_narratives(
    deliverable_id: UUID,
    payload: ProposeNarrativesRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[AINarrative]:
    try:
        deliverable = repo.get_deliverable(principal, deliverable_id)
        engagement = repo.get_engagement(principal, deliverable.engagement_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found("Deliverable not found.") from exc
    if deliverable.scoring_run_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Deliverable has no finalised scoring run to draft narratives from.",
        )

    record = repo.get_scoring_run_record(principal, deliverable.scoring_run_id)
    subject = repo.get_prospect(principal, engagement.prospect_id).company_name
    result = AtlasResult.model_validate_json(record.result_json)
    context = context_from_result(result, subject)
    author_tier = _principal_tier(repo, principal)

    proposed: list[AINarrative] = []
    for section in payload.sections:
        proposed.append(
            repo.create_narrative(
                principal,
                deliverable_id=deliverable_id,
                scoring_run_id=record.id,
                section=section,
                proposed_text=_DRAFTER.draft(section, context),
                drafter_version=_DRAFTER.version,
                prompt_template_version=_DRAFTER.prompt_template_version,
                author_tier=author_tier,
            )
        )
    return proposed


@router.post("/narratives/{narrative_id}/approve", response_model=AINarrative)
def approve_narrative(
    narrative_id: UUID,
    payload: ApproveNarrativeRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> AINarrative:
    try:
        narrative = repo.get_narrative(principal, narrative_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found("Narrative not found.") from exc

    # Approved text is the consultant's edit, or the proposal verbatim. An explicit empty/whitespace
    # final_text is rejected at the boundary — an approved section is never blank (§5).
    final_text = payload.final_text if payload.final_text is not None else narrative.proposed_text
    if not final_text.strip():
        raise HTTPException(
            status_code=422,  # unprocessable content (avoids the deprecated Starlette alias)
            detail="final_text must not be empty — an approved narrative section carries prose.",
        )

    approver_tier = _principal_tier(repo, principal)
    try:
        # The PRD §5 quality gate: a junior-tier author needs senior sign-off. Senior review of
        # another consultant's draft runs on the governance-visibility path (an ADMIN/committee
        # reviewer; ADR-0009) — the approver's own tier is what must be senior.
        assert_senior_approval(author_tier=narrative.author_tier, approver_tier=approver_tier)
    except SeniorApprovalError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    try:
        return repo.approve_narrative(
            principal,
            narrative_id=narrative_id,
            final_text=final_text,
            edit_summary=edit_summary(narrative.proposed_text, final_text),
            approved_at=datetime.now(UTC),
        )
    except RepositoryError as exc:  # e.g. already approved — a conflict, not a server error
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/deliverables/{deliverable_id}/narratives", response_model=list[AINarrative])
def list_narratives(
    deliverable_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[AINarrative]:
    try:
        return repo.list_narratives(principal, deliverable_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found("Deliverable not found.") from exc
