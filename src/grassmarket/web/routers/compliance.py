"""Compliance router (GRS-0032, PRD §2) — the append-only audit log and GDPR subject rights.

The audit log is admin-only (compliance review). GDPR export and erasure are self-or-admin: an
advisor may export or delete their own personal data; an admin may act for anyone. Erasure
anonymises the consultant and de-identifies immutable scoring runs — it never deletes them (#6).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from bcap_contracts.audit import AuditEvent, PersonalDataExport
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from grassmarket.data.repository import (
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(prefix="/compliance", tags=["compliance"])


class DeletionSummary(BaseModel):
    subject_consultant_id: UUID
    deleted_row_counts: dict[str, int]


def _forbidden(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.get("/audit", response_model=list[AuditEvent])
def audit_log(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[AuditEvent]:
    try:
        return repo.list_audit_events(principal)
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc


@router.get("/personal-data/{advisor_id}", response_model=PersonalDataExport)
def export_personal_data(
    advisor_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> PersonalDataExport:
    try:
        return repo.export_personal_data(principal, advisor_id, now=datetime.now(UTC))
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Consultant not found."
        ) from exc


@router.post("/personal-data/{advisor_id}/delete", response_model=DeletionSummary)
def delete_personal_data(
    advisor_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> DeletionSummary:
    try:
        counts = repo.delete_personal_data(principal, advisor_id, now=datetime.now(UTC))
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Consultant not found."
        ) from exc
    return DeletionSummary(subject_consultant_id=advisor_id, deleted_row_counts=counts)
