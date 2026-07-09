"""Workshops + recovery-fee router (GRS-0012, PRD §4). Every handler is scoped through the
repository; a cross-owner access is a 404 (never revealing existence). A workshop-state or
attribution-window refusal is a 409 — the resource is yours, the operation just isn't valid.

Money never appears in a handler signature here: the endpoints speak dates and ids; the £ fee is
computed and persisted inside the repository as `Money` (ADR-0002).
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from bcap_contracts.engagements import Workshop
from bcap_contracts.fees import RecoveryFeeAttribution
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from grassmarket.data.repository import (
    AttributionWindowExpired,
    ConflictError,
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
    WorkshopStateError,
)
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(prefix="/workshops", tags=["pipeline"])
fees_router = APIRouter(prefix="/recovery-fees", tags=["pipeline"])

_NOT_FOUND = "Workshop not found."


class CreateWorkshopRequest(BaseModel):
    prospect_id: UUID
    scheduled_for: date | None = None
    pre_workshop_brief: str | None = None


class DeliverWorkshopRequest(BaseModel):
    delivered_on: date
    workshop_output: str | None = None


class RecoveryFeeRequest(BaseModel):
    contracted_on: date


@router.post("", response_model=Workshop, status_code=status.HTTP_201_CREATED)
def create_workshop(
    payload: CreateWorkshopRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Workshop:
    try:
        return repo.create_workshop(
            principal,
            prospect_id=payload.prospect_id,
            scheduled_for=payload.scheduled_for,
            pre_workshop_brief=payload.pre_workshop_brief,
        )
    except (NotFoundError, ScopeViolationError) as exc:
        # The linked prospect isn't the principal's (or doesn't exist) — 404, no existence leak.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prospect not found."
        ) from exc


@router.get("", response_model=list[Workshop])
def list_workshops(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[Workshop]:
    return repo.list_workshops(principal)


@router.get("/{workshop_id}", response_model=Workshop)
def get_workshop(
    workshop_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Workshop:
    try:
        return repo.get_workshop(principal, workshop_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND) from exc


@router.post("/{workshop_id}/deliver", response_model=Workshop)
def deliver_workshop(
    workshop_id: UUID,
    payload: DeliverWorkshopRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Workshop:
    try:
        return repo.deliver_workshop(
            principal,
            workshop_id,
            delivered_on=payload.delivered_on,
            workshop_output=payload.workshop_output,
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND) from exc
    except WorkshopStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post(
    "/{workshop_id}/recovery-fee",
    response_model=RecoveryFeeAttribution,
    status_code=status.HTTP_201_CREATED,
)
def attribute_recovery_fee(
    workshop_id: UUID,
    payload: RecoveryFeeRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> RecoveryFeeAttribution:
    try:
        return repo.record_recovery_fee_attribution(
            principal, workshop_id, contracted_on=payload.contracted_on
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND) from exc
    except (WorkshopStateError, AttributionWindowExpired, ConflictError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@fees_router.get("", response_model=list[RecoveryFeeAttribution])
def list_recovery_fees(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[RecoveryFeeAttribution]:
    return repo.list_recovery_fee_attributions(principal)
