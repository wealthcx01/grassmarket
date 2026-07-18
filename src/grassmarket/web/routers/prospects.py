"""Prospects router — a scoped pipeline resource that demonstrates absolute data scoping over
HTTP. Every handler passes the authenticated principal to the repository, which is the only
place the owner check happens.

At the HTTP boundary a `ScopeViolationError` is mapped to 404 (not 403): the API does not reveal
that a resource it won't show you exists at all.
"""

from __future__ import annotations

from uuid import UUID

from bcap_contracts.entities import Contact, PipelineStage, Prospect
from bcap_contracts.pipeline import IllegalStageTransition, StageHistoryEntry
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

router = APIRouter(prefix="/prospects", tags=["pipeline"])


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prospect not found.")


class CreateProspectRequest(BaseModel):
    company_name: str = Field(min_length=1)
    sector: str | None = None
    website: str | None = None
    primary_contact_name: str | None = None
    primary_contact_email: str | None = None
    notes: str | None = None


class UpdateProspectRequest(BaseModel):
    """Patch a prospect's editable fields — only the fields sent (non-null) are changed."""

    company_name: str | None = None
    sector: str | None = None
    website: str | None = None
    primary_contact_name: str | None = None
    primary_contact_email: str | None = None
    notes: str | None = None


class UpdateStageRequest(BaseModel):
    stage: PipelineStage


class CreateContactRequest(BaseModel):
    name: str = Field(min_length=1)
    email: str | None = None
    phone: str | None = None
    title: str | None = None
    is_primary: bool = False


class UpdateContactRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    title: str | None = None
    is_primary: bool | None = None


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
        website=payload.website,
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


@router.get("/{prospect_id}/history", response_model=list[StageHistoryEntry])
def prospect_stage_history(
    prospect_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[StageHistoryEntry]:
    """The prospect's stage timeline, oldest first (GRS-0111). Owner-scoped — an unowned or unknown
    prospect is 404, never a leak that it exists."""
    try:
        return list(repo.list_stage_history(principal, prospect_id))
    except (NotFoundError, ScopeViolationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prospect not found."
        ) from exc


@router.patch("/{prospect_id}", response_model=Prospect)
def update_prospect(
    prospect_id: UUID,
    payload: UpdateProspectRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Prospect:
    """Edit a prospect's fields (company, sector, website, primary contact, notes). Stage moves use
    the dedicated `/stage` choke-point, not this."""
    try:
        return repo.update_prospect(
            principal,
            prospect_id,
            company_name=payload.company_name,
            sector=payload.sector,
            website=payload.website,
            primary_contact_name=payload.primary_contact_name,
            primary_contact_email=payload.primary_contact_email,
            notes=payload.notes,
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found() from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


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
        raise _not_found() from exc
    except IllegalStageTransition as exc:
        # A legitimate, owned prospect but an illegal move — 409, with the reason.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


# --- Contacts (first-class, owner-scoped, GRS-0111) -------------------------------------
@router.get("/{prospect_id}/contacts", response_model=list[Contact])
def list_contacts(
    prospect_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[Contact]:
    try:
        return repo.list_contacts(principal, prospect_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found() from exc


@router.post("/{prospect_id}/contacts", response_model=Contact, status_code=status.HTTP_201_CREATED)
def create_contact(
    prospect_id: UUID,
    payload: CreateContactRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Contact:
    try:
        return repo.create_contact(
            principal,
            prospect_id,
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            title=payload.title,
            is_primary=payload.is_primary,
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found() from exc


@router.patch("/{prospect_id}/contacts/{contact_id}", response_model=Contact)
def update_contact(
    prospect_id: UUID,
    contact_id: UUID,
    payload: UpdateContactRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Contact:
    try:
        return repo.update_contact(
            principal,
            contact_id,
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            title=payload.title,
            is_primary=payload.is_primary,
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found."
        ) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{prospect_id}/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    prospect_id: UUID,
    contact_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> None:
    try:
        repo.delete_contact(principal, contact_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found."
        ) from exc
