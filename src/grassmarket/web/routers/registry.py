"""Registry router — the module/subcomponent/metric/power structure the wizard renders its forms
from (GRS-0010). Read-only shared content (one source of truth, the ADR-0001 registry),
authenticated but not owner-scoped. A `profile` selects the operating-model VIEW (ADR-0025/GRS-0079)
— retail (default) is the full superset; exchange reshapes the module set."""

from __future__ import annotations

from bcap_contracts.registry import (
    RETAIL_PROFILE_KEY,
    Registry,
    UnknownKeyError,
    load_profile,
    load_profiles,
    load_registry,
)
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from grassmarket.data.repository import Principal
from grassmarket.web.dependencies import get_current_principal

router = APIRouter(prefix="/registry", tags=["registry"])


class ProfileSummary(BaseModel):
    """One selectable operating-model profile (ADR-0025) — key + display name for the wizard."""

    key: str
    name: str


@router.get("/profiles", response_model=list[ProfileSummary])
def list_profiles(_principal: Principal = Depends(get_current_principal)) -> list[ProfileSummary]:
    """The operating-model profiles a wizard may select (retail first). Only profiles with real
    content are offered — a profile with no content can't be selected (fail-loud upstream)."""
    profiles = load_profiles()
    ordered = [RETAIL_PROFILE_KEY, *(k for k in profiles if k != RETAIL_PROFILE_KEY)]
    return [ProfileSummary(key=k, name=profiles[k].name) for k in ordered]


@router.get("", response_model=Registry)
def get_registry(
    profile: str = RETAIL_PROFILE_KEY,
    _principal: Principal = Depends(get_current_principal),
) -> Registry:
    """The registry the wizard renders. `profile=retail` (default) is the full superset —
    byte-identical to before; a non-retail profile returns its filtered view. An unknown profile
    fails loud (ADR-0001)."""
    registry = load_registry()
    try:
        return registry.for_profile(load_profile(profile))
    except UnknownKeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
