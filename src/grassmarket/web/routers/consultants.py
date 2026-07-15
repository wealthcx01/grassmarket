"""Consultants router — a minimal colleague lookup for rater assignment (GRS-0062).

Dual rating (§9) needs the lead to name a co-rater by their consultant id, which no human knows.
This resolves a colleague by their EXACT email to the id + name — enough to assign them, and no
more. It is an exact-match lookup (never a listing or prefix search), so it does not enable
directory enumeration; any authenticated consultant may resolve a colleague they know the email of.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr

from grassmarket.data.repository import Principal, Repository
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(prefix="/consultants", tags=["consultants"])


class RaterCandidate(BaseModel):
    """The minimum needed to assign a colleague as a rater — never a password hash or other PII."""

    id: UUID
    full_name: str
    email: EmailStr
    is_active: bool


@router.get("/by-email", response_model=RaterCandidate)
def lookup_by_email(
    email: EmailStr = Query(..., description="The colleague's exact email address."),
    _principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> RaterCandidate:
    stored = repo.get_consultant_by_email(email)
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No consultant with that email. Check the address, or ask them to sign in once.",
        )
    return RaterCandidate(
        id=stored.id, full_name=stored.full_name, email=stored.email, is_active=stored.is_active
    )
