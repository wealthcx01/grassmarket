"""Company entity lookup (GRS-0100, ADR-0033).

Org-wide reference data (like the registry of powers/modules) — every consultant queries the same
canonical company list; it carries no owner's data. The lookup only PROPOSES candidates: the advisor
picks one, and the create-assessment endpoint validates the chosen id against this same registry so
a fabricated link can never be stored (fail loud, CLAUDE.md #3).
"""

from __future__ import annotations

from bcap_contracts.entities import CompanyEntity
from fastapi import APIRouter, Depends, HTTPException, Query, status

from grassmarket.data.repository import Principal
from grassmarket.entities import active_entity_registry
from grassmarket.web.dependencies import get_current_principal

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("/search", response_model=list[CompanyEntity])
def search_entities(
    q: str = Query(min_length=1, description="Company name or alias fragment."),
    limit: int = Query(default=8, ge=1, le=25),
    _principal: Principal = Depends(get_current_principal),
) -> list[CompanyEntity]:
    """Ranked candidate companies for `q` — the advisor picks one (never auto-resolved)."""
    return active_entity_registry().search(q, limit=limit)


@router.get("/{entity_id}", response_model=CompanyEntity)
def get_entity(
    entity_id: str,
    _principal: Principal = Depends(get_current_principal),
) -> CompanyEntity:
    entity = active_entity_registry().get(entity_id)
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown company entity.")
    return entity
