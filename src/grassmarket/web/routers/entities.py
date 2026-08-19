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

from datetime import UTC, datetime

from bcap_contracts.entities import CompanyEntity, RegistryContact
from bcap_contracts.influencer import InfluencerMap
from bcap_contracts.prospecting import ProspectingPage, SegmentKind, segment_label
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from grassmarket.data.repository import NotFoundError, Principal, Repository
from grassmarket.entities import active_entity_registry
from grassmarket.gtm import LsegRosterSource, RowError, generate_influencer_map
from grassmarket.web.dependencies import (
    get_current_principal,
    get_lseg_roster_source,
    get_repository,
)

router = APIRouter(prefix="/entities", tags=["entities"])


class InfluencerMapRequest(BaseModel):
    """The ticker sample to pull the roster against. Required and explicit: there is no default
    basket, because which tickers a contributor covers is a per-run judgement (GRS-0194 §1)."""

    model_config = ConfigDict(extra="forbid")

    sample_rics: tuple[str, ...] = Field(min_length=1, max_length=60)


@router.get("/search", response_model=list[CompanyEntity])
def search_entities(
    q: str = Query(min_length=1, description="Company name or alias fragment."),
    limit: int = Query(default=8, ge=1, le=25),
    repo: Repository = Depends(get_repository),
    _principal: Principal = Depends(get_current_principal),
) -> list[CompanyEntity]:
    """Ranked candidate companies for `q` — the advisor picks one (never auto-resolved)."""
    return active_entity_registry(repo).search(q, limit=limit)


class RegistryFacets(BaseModel):
    """What the Prospecting filters can offer, derived from the data rather than from a constant."""

    model_config = ConfigDict(extra="forbid")

    segments: list[SegmentFacet]
    countries: list[Facet]


class Facet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str
    count: int = Field(ge=0)


class SegmentFacet(Facet):
    """A segment option, carrying the label and the KIND so the UI can group honestly.

    The kind matters because the stored column mixes firm types with supplier content types
    (GRS-0238). Presenting "Supplies: indices" in the same flat list as "Bank" would tell an advisor
    they are alternatives of one kind, which they are not.
    """

    model_config = ConfigDict(extra="forbid")

    label: str
    kind: SegmentKind


# Declared BEFORE `/{entity_id}` so these literal segments are matched by their own routes rather
# than being swallowed as an entity id by the single-segment route below.
@router.get("", response_model=ProspectingPage)
def list_registry_targets(
    segment: str | None = Query(default=None),
    country: str | None = Query(default=None),
    q: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> ProspectingPage:
    """Browse the imported universe (GRS-0238) — the founder's "I can't see prospective clients".

    Network-shared read, exactly like `/entities/search`: the registry is reference data, so there
    is no owner filter on the targets. The one owner-scoped field is `already_in_my_pipeline`,
    computed against this principal in the repository layer.
    """
    return repo.list_registry_targets(
        principal, segment=segment, country=country, q=q, offset=offset, limit=limit
    )


@router.get("/facets", response_model=RegistryFacets)
def registry_facets(
    repo: Repository = Depends(get_repository),
    _principal: Principal = Depends(get_current_principal),
) -> RegistryFacets:
    """The filter options that actually exist in the data, with counts."""
    return RegistryFacets(
        segments=[
            SegmentFacet(
                value=value,
                count=count,
                label=segment_label(value)[0],
                kind=segment_label(value)[1],
            )
            for value, count in repo.registry_segments()
        ],
        countries=[Facet(value=value, count=count) for value, count in repo.registry_countries()],
    )


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


@router.post("/{target_id}/influencer-map", response_model=InfluencerMap)
def generate_influencer_map_for_target(
    target_id: str,
    payload: InfluencerMapRequest,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    source: LsegRosterSource = Depends(get_lseg_roster_source),
) -> InfluencerMap:
    """Generate the influencer map for an imported institution (GRS-0194).

    Admin-only and never scheduled: every run is an operator action against a live vendor
    connector, so it is triggered deliberately and one advisor cannot start a mass pull.
    """
    if not principal.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Generating an influencer map runs a live vendor pull and is admin-only.",
        )
    target = repo.get_registry_target(target_id)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registry target '{target_id}' not found.",
        )
    try:
        return generate_influencer_map(
            target,
            repo.list_registry_contacts(target_id),
            source,
            sample_rics=payload.sample_rics,
            generated_on=datetime.now(UTC).date(),
        )
    except RowError as exc:
        # A refused pull is a 422, not a 500: the request named a target or a sample the method
        # cannot produce an honest map from, and the reason is worth showing.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


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
