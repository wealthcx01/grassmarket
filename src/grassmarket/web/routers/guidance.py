"""Guidance router — rubric anchors for the wizard (GRS-0008/§4).

Returns the four anchors for a subcomponent, INCLUDING those whose status is `todo`: the client
shows "guidance not yet authored" for a todo anchor, never a blank. Rubric content is shared
guidance (not owned data), so this endpoint is authenticated but not owner-scoped.
"""

from __future__ import annotations

import functools

from bcap_contracts.registry import load_profiles, load_registry
from bcap_contracts.rubric import RubricAnchor, load_rubric_library
from fastapi import APIRouter, Depends, HTTPException, status

from grassmarket.data.repository import Principal
from grassmarket.web.dependencies import get_current_principal

router = APIRouter(prefix="/guidance", tags=["guidance"])


@functools.lru_cache(maxsize=1)
def _all_known_subcomponent_keys() -> frozenset[str]:
    """Every subcomponent key that exists in ANY operating-model view — the retail superset plus
    each profile's own subcomponent additions (e.g. the wealth custody/suitability set). Used to
    tell a real-but-unauthored subcomponent (graceful empty) from a genuinely unknown key (404)."""
    keys = set(load_registry().all_subcomponent_keys())
    for profile in load_profiles().values():
        keys.update(a.key for a in profile.subcomponent_additions)
    return frozenset(keys)


@router.get("/subcomponents/{subcomponent_key}", response_model=list[RubricAnchor])
def subcomponent_guidance(
    subcomponent_key: str,
    _principal: Principal = Depends(get_current_principal),
) -> list[RubricAnchor]:
    anchors = load_rubric_library().for_subcomponent(subcomponent_key)
    if anchors:
        return list(anchors)
    # A real subcomponent whose rubric isn't authored yet (e.g. the draft wealth infra set) returns
    # an EMPTY list — the wizard shows "guidance not yet authored", never a raw error. Only a
    # genuinely unknown key is a 404.
    if subcomponent_key in _all_known_subcomponent_keys():
        return []
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No such subcomponent {subcomponent_key!r}.",
    )
