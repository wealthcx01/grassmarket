"""Rating Committee router (GRS-0021, Methodology §8) — peer sign-off on high-stakes ratings.

The queue for an assessment lists its high-stakes items (power Established+, triad above None, a
module rated Frontier), from the live score, each paired with the committee's current call.
committee member (never the assessment owner — peer challenge) records approve / reject decisions
with rationale and dissent. Those decisions gate finalisation (assessments router) and client packs
(deliverables). Scope-refusals are 404; state/authority refusals are 409.
"""

from __future__ import annotations

import random
from uuid import UUID

from bcap_contracts.committee import (
    CommitteeDecision,
    CommitteeDecisionStatus,
    CommitteeItemType,
    CommitteeQueueEntry,
)
from bcap_contracts.registry import load_registry
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from grassmarket.assessments import compute_score, scoreability_blockers
from grassmarket.atlas.active import active_coefficient_set, active_uncertainty_model
from grassmarket.atlas.committee import required_committee_items
from grassmarket.data.repository import (
    ConflictError,
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(prefix="/assessments", tags=["committee"])

# Same fixed seed as the live-score / finalise paths so the derived high-stakes set is stable.
_SEED = 20260706


class CommitteeDecisionRequest(BaseModel):
    # Mirror the CommitteeDecision contract's constraints so bad input is a 422 at the boundary,
    # never a 500 when the repository maps the row back to the (min_length-checked) contract.
    item_type: CommitteeItemType
    item_key: str = Field(min_length=1)
    rating: str = Field(min_length=1)
    status: CommitteeDecisionStatus
    rationale: str = Field(min_length=1)
    dissent_note: str | None = None


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")


@router.get("/{assessment_id}/committee", response_model=list[CommitteeQueueEntry])
def committee_queue(
    assessment_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[CommitteeQueueEntry]:
    """The high-stakes items on this assessment that need committee sign-off, each with its current
    decision (or none = pending). Empty while the document is not yet scoreable — no ratings exist
    to review. Visible to the owner, a committee member, or an admin."""
    try:
        assessment = repo.get_assessment_for_committee(principal, assessment_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found() from exc

    registry = load_registry()
    if scoreability_blockers(assessment.document, registry):
        return []
    art = compute_score(
        assessment.document,
        active_coefficient_set(registry),
        registry,
        active_uncertainty_model(),
        random.Random(_SEED),
    )
    items = required_committee_items(art.result)
    decisions = {
        (d.item_type, d.item_key): d
        for d in repo.list_committee_decisions(principal, assessment_id)
    }
    return [
        CommitteeQueueEntry(item=item, decision=decisions.get((item.item_type, item.item_key)))
        for item in items
    ]


@router.post("/{assessment_id}/committee/decide", response_model=CommitteeDecision)
def decide_committee_item(
    assessment_id: UUID,
    payload: CommitteeDecisionRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CommitteeDecision:
    """Record the committee's call on one high-stakes item. Committee member or admin only, and
    never on their own assessment (peer challenge). Rationale required; dissent optional (§8)."""
    try:
        return repo.decide_committee_item(
            principal,
            assessment_id,
            item_type=payload.item_type,
            item_key=payload.item_key,
            rating=payload.rating,
            status=payload.status,
            rationale=payload.rationale,
            dissent_note=payload.dissent_note,
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found() from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
