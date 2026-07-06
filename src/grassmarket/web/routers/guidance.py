"""Guidance router — rubric anchors for the wizard (GRS-0008/§4).

Returns the four anchors for a subcomponent, INCLUDING those whose status is `todo`: the client
shows "guidance not yet authored" for a todo anchor, never a blank. Rubric content is shared
guidance (not owned data), so this endpoint is authenticated but not owner-scoped.
"""

from __future__ import annotations

from bcap_contracts.rubric import RubricAnchor, load_rubric_library
from fastapi import APIRouter, Depends, HTTPException, status

from grassmarket.data.repository import Principal
from grassmarket.web.dependencies import get_current_principal

router = APIRouter(prefix="/guidance", tags=["guidance"])


@router.get("/subcomponents/{subcomponent_key}", response_model=list[RubricAnchor])
def subcomponent_guidance(
    subcomponent_key: str,
    _principal: Principal = Depends(get_current_principal),
) -> list[RubricAnchor]:
    anchors = load_rubric_library().for_subcomponent(subcomponent_key)
    if not anchors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No such subcomponent {subcomponent_key!r}.",
        )
    return list(anchors)
