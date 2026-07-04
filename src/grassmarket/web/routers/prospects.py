"""Prospects router — a scoped pipeline resource that demonstrates absolute data scoping over
HTTP. Every handler passes the authenticated principal to the repository, which is the only
place the owner check happens.

At the HTTP boundary a `ScopeViolationError` is mapped to 404 (not 403): the API does not reveal
that a resource it won't show you exists at all.
"""

from __future__ import annotations

from uuid import UUID

from bcap_contracts.entities import PipelineStage, Prospect
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from grassmarket.data.repository import (
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(prefix="/prospects", tags=["pipeline"])


class CreateProspectRequest(BaseModel):
    company_name: str = Field(min_length=1)
    sector: str | None = None
    primary_contact_name: str | None = None
    primary_contact_email: str | None = None
    notes: str | None = None


class UpdateStageRequest(BaseModel):
    stage: PipelineStage


@router.post("", response_model=Prospect, status_code=status.HTTP_201_CREATED)
def create_prospect(
    payload: CreateProspectRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Prospect:
    return repo.create_prospect(
        principal,
        company_name=payload.company_name,
        sector=payload.sector,
        primary_contact_name=payload.primary_contact_name,
        primary_contact_email=payload.primary_contact_email,
        notes=payload.notes,
    )


@router.get("", response_model=list[Prospect])
def list_prospects(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[Prospect]:
    return repo.list_prospects(principal)


@router.get("/{prospect_id}", response_model=Prospect)
def get_prospect(
    prospect_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Prospect:
    try:
        return repo.get_prospect(principal, prospect_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prospect not found."
        ) from exc


@router.patch("/{prospect_id}/stage", response_model=Prospect)
def update_stage(
    prospect_id: UUID,
    payload: UpdateStageRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Prospect:
    try:
        return repo.update_prospect_stage(principal, prospect_id, payload.stage)
    except (NotFoundError, ScopeViolationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prospect not found."
        ) from exc
