"""Registry router — the module/subcomponent/metric/power structure the wizard renders its forms
from (GRS-0010). Read-only shared content (one source of truth, the ADR-0001 registry),
authenticated but not owner-scoped."""

from __future__ import annotations

from bcap_contracts.registry import Registry, load_registry
from fastapi import APIRouter, Depends

from grassmarket.data.repository import Principal
from grassmarket.web.dependencies import get_current_principal

router = APIRouter(prefix="/registry", tags=["registry"])


@router.get("", response_model=Registry)
def get_registry(_principal: Principal = Depends(get_current_principal)) -> Registry:
    return load_registry()
