"""Certification-ladder router (GRS-0023, Methodology §9) — capability, enforced.

An admin (trainer/facilitator) records ladder evidence — coursework, the rubric exam, shadow
assessments, an observed lead, and a Certified Lead's sign-off — and promotes an advisor one rung at
a time; a promotion is refused unless the evidence is in. Every credit, promotion, and override is
an append-only event. An advisor may read their own record and history; an admin, anyone's.

Error mapping: an authority refusal is 403 (records are not hidden, the action is not yours); a
missing consultant is 404; a missing-evidence / state refusal is 409.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from bcap_contracts.certification import CertificationEvent, CertificationRecord
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from grassmarket.data.repository import (
    ConflictError,
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(prefix="/certification", tags=["certification"])


class ExamRequest(BaseModel):
    score: float = Field(ge=0.0, le=1.0)


class SignoffRequest(BaseModel):
    signer_consultant_id: UUID


def _forbidden(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultant not found.")


def _conflict(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


def _admin_action(fn) -> CertificationRecord:
    """Run an admin evidence/promotion action, mapping the repository errors to HTTP."""
    try:
        return fn()
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc
    except NotFoundError as exc:
        raise _not_found() from exc
    except ConflictError as exc:
        raise _conflict(exc) from exc


@router.post("/{advisor_id}/coursework", response_model=CertificationRecord)
def record_coursework(
    advisor_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CertificationRecord:
    return _admin_action(
        lambda: repo.record_coursework(principal, advisor_id, occurred_at=datetime.now(UTC))
    )


@router.post("/{advisor_id}/exam", response_model=CertificationRecord)
def record_exam(
    advisor_id: UUID,
    payload: ExamRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CertificationRecord:
    return _admin_action(
        lambda: repo.record_exam(
            principal, advisor_id, score=payload.score, occurred_at=datetime.now(UTC)
        )
    )


@router.post("/{advisor_id}/shadow", response_model=CertificationRecord)
def log_shadow(
    advisor_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CertificationRecord:
    return _admin_action(
        lambda: repo.log_shadow_assessment(principal, advisor_id, occurred_at=datetime.now(UTC))
    )


@router.post("/{advisor_id}/observed-lead", response_model=CertificationRecord)
def log_observed_lead(
    advisor_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CertificationRecord:
    return _admin_action(
        lambda: repo.log_observed_lead(principal, advisor_id, occurred_at=datetime.now(UTC))
    )


@router.post("/{advisor_id}/signoff", response_model=CertificationRecord)
def record_signoff(
    advisor_id: UUID,
    payload: SignoffRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CertificationRecord:
    return _admin_action(
        lambda: repo.record_signoff(
            principal,
            advisor_id,
            signer_id=payload.signer_consultant_id,
            occurred_at=datetime.now(UTC),
        )
    )


@router.post("/{advisor_id}/promote", response_model=CertificationRecord)
def promote(
    advisor_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CertificationRecord:
    """Advance the advisor one rung — refused (409) unless the next level's evidence is recorded."""
    return _admin_action(
        lambda: repo.promote_advisor(principal, advisor_id, occurred_at=datetime.now(UTC))
    )


@router.get("/{advisor_id}", response_model=CertificationRecord)
def get_record(
    advisor_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CertificationRecord:
    try:
        return repo.get_certification_record(principal, advisor_id)
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc
    except NotFoundError as exc:
        raise _not_found() from exc


@router.get("/{advisor_id}/events", response_model=list[CertificationEvent])
def list_events(
    advisor_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[CertificationEvent]:
    try:
        return repo.list_certification_events(principal, advisor_id)
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc
