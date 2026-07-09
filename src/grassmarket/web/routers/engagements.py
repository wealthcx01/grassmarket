"""Engagements router (GRS-0013, PRD §4). Every handler is scoped through the repository; a
cross-owner access — an engagement, or a prospect/assessment being linked that isn't the
principal's — is a 404 (never revealing existence). A link that's structurally invalid (prospect
not contracted, assessment not finalised) is a 409.

Score-and-money-free: engagement detail carries no currency and no index.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from bcap_contracts.engagements import CommsChannel, CommsLogEntry, DeliverableSlot, Engagement
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from grassmarket.data.repository import (
    EngagementLinkError,
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(prefix="/engagements", tags=["pipeline"])

_NOT_FOUND = "Engagement not found."


class CreateEngagementRequest(BaseModel):
    prospect_id: UUID
    title: str = Field(min_length=1)
    started_on: date | None = None
    assessment_ids: tuple[UUID, ...] = ()
    deliverables: tuple[DeliverableSlot, ...] = ()


class CommsEntryRequest(BaseModel):
    channel: CommsChannel
    body: str = Field(min_length=1)


@router.post("", response_model=Engagement, status_code=status.HTTP_201_CREATED)
def create_engagement(
    payload: CreateEngagementRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Engagement:
    try:
        return repo.create_engagement(
            principal,
            prospect_id=payload.prospect_id,
            title=payload.title,
            started_on=payload.started_on,
            assessment_ids=payload.assessment_ids,
            deliverables=payload.deliverables,
        )
    except (NotFoundError, ScopeViolationError) as exc:
        # A cross-owner (or missing) prospect/assessment — 404, no existence leak.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.") from exc
    except EngagementLinkError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("", response_model=list[Engagement])
def list_engagements(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[Engagement]:
    return repo.list_engagements(principal)


@router.get("/{engagement_id}", response_model=Engagement)
def get_engagement(
    engagement_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Engagement:
    try:
        return repo.get_engagement(principal, engagement_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND) from exc


@router.post(
    "/{engagement_id}/comms", response_model=CommsLogEntry, status_code=status.HTTP_201_CREATED
)
def append_comms_entry(
    engagement_id: UUID,
    payload: CommsEntryRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CommsLogEntry:
    try:
        return repo.append_comms_entry(
            principal, engagement_id, channel=payload.channel, body=payload.body
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND) from exc
