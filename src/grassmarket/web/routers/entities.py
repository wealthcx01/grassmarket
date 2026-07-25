"""Company entity lookup (GRS-0100, ADR-0033) and the shared GTM contact registry (GRS-0193).

Org-wide reference data (like the registry of powers/modules) — every consultant queries the same
canonical company list; it carries no owner's data. The lookup only PROPOSES candidates: the advisor
picks one, and the create-assessment endpoint validates the chosen id against this same registry so
a fabricated link can never be stored (fail loud, CLAUDE.md #3).

The corpus behind the port is the seeded stub until a GTM import populates `registry_targets`, at
which point `active_entity_registry` returns the DB-backed adapter merged over that seed. These
routes are unchanged by that swap, which is the point of the port (ADR-0033).
"""

from __future__ import annotations

from bcap_contracts.entities import CompanyEntity, RegistryContact
from fastapi import APIRouter, Depends, HTTPException, Query, status

from grassmarket.data.repository import NotFoundError, Principal, Repository
from grassmarket.entities import active_entity_registry
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("/search", response_model=list[CompanyEntity])
def search_entities(
    q: str = Query(min_length=1, description="Company name or alias fragment."),
    limit: int = Query(default=8, ge=1, le=25),
    repo: Repository = Depends(get_repository),
    _principal: Principal = Depends(get_current_principal),
) -> list[CompanyEntity]:
    """Ranked candidate companies for `q` — the advisor picks one (never auto-resolved)."""
    return active_entity_registry(repo).search(q, limit=limit)


# Declared BEFORE `/{entity_id}` so the literal `contacts` segment is matched by this route rather
# than being swallowed as an entity id by the single-segment route below.
@router.get("/{target_id}/contacts", response_model=list[RegistryContact])
def list_registry_contacts(
    target_id: str,
    repo: Repository = Depends(get_repository),
    _principal: Principal = Depends(get_current_principal),
) -> list[RegistryContact]:
    """The known people at an imported institution (GRS-0193, ADR-0045 §2).

    Network-shared: any authenticated consultant reads the same universe, because the registry is
    reference data rather than anyone's pipeline. A consultant's own prospect contacts stay
    owner-private on the separate `/prospects/{id}/contacts` route — the two never merge.
    """
    try:
        return repo.list_registry_contacts(target_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{entity_id}", response_model=CompanyEntity)
def get_entity(
    entity_id: str,
    repo: Repository = Depends(get_repository),
    _principal: Principal = Depends(get_current_principal),
) -> CompanyEntity:
    entity = active_entity_registry(repo).get(entity_id)
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown company entity.")
    return entity
