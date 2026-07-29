"""Founder review router (GRS-0188, ADR-0041) — the founder signs what goes out.

An advisor submits a document for review; the founder approves the version in front of them. The
approval names the document's hash, so any later edit stops it matching and the record returns to
the queue. That is the whole state machine, and it is arithmetic rather than a status column.

Scope refusals on an assessment are 404 (the API never reveals a record the caller cannot see).
Role refusals on the approval and the queue are 403: the caller can already see the resource, so a
404 would be a lie about why they were stopped.
"""

from __future__ import annotations

from uuid import UUID

from bcap_contracts.assessments import Assessment
from bcap_contracts.founder_review import FounderApproval, FounderReviewQueueEntry
from fastapi import APIRouter, Depends, HTTPException, status

from grassmarket.data.repository import (
    ConflictError,
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(prefix="/assessments", tags=["founder-review"])
queue_router = APIRouter(prefix="/founder-review", tags=["founder-review"])


def _not_found(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/{assessment_id}/submit-for-review", response_model=Assessment)
def submit_for_review(
    assessment_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Assessment:
    """Ask the founder to review this document. Re-submitting after an edit is the normal case,
    not an error, so this is idempotent and simply moves the request timestamp."""
    try:
        return repo.request_founder_review(principal, assessment_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found(exc) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post(
    "/{assessment_id}/founder-approval",
    response_model=FounderApproval,
    status_code=status.HTTP_201_CREATED,
)
def approve_current_version(
    assessment_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> FounderApproval:
    """The founder signs off the document as it stands. The hash is computed server-side from the
    stored document: a caller cannot name the version they are approving."""
    try:
        return repo.record_founder_approval(principal, assessment_id)
    except ScopeViolationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise _not_found(exc) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{assessment_id}/founder-approval", response_model=FounderApproval | None)
def current_approval(
    assessment_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> FounderApproval | None:
    """The approval that currently clears this document, or null. Null after an edit is the
    correct answer and the reason the advisor sees "re-edited since approval"."""
    try:
        repo.get_assessment(principal, assessment_id)  # scope check before the unscoped gate read
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found(exc) from exc
    return repo.current_founder_approval(assessment_id)


@queue_router.get("/queue", response_model=list[FounderReviewQueueEntry])
def review_queue(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[FounderReviewQueueEntry]:
    """Everything waiting on the founder, oldest request first."""
    try:
        return repo.list_founder_review_queue(principal)
    except ScopeViolationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
