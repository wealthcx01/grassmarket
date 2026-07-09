"""Pipeline router — the kanban board and the (currency-free) deal-volume forecast (GRS-0011).

Both endpoints read the principal's OWN prospects through the repository (absolute scoping) and
shape them with the pure pipeline service. `now` is taken at request time and passed in, so the
service stays deterministic. No Money here — the £ forecast is GRS-0012.
"""

from __future__ import annotations

from datetime import UTC, datetime

from bcap_contracts.pipeline import PipelineBoard, PipelineForecast, load_pipeline_config
from fastapi import APIRouter, Depends

from grassmarket.data.repository import Principal, Repository
from grassmarket.pipeline import build_board, build_forecast
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/board", response_model=PipelineBoard)
def get_board(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> PipelineBoard:
    prospects = repo.list_prospects(principal)
    return build_board(prospects, load_pipeline_config(), datetime.now(UTC))


@router.get("/forecast", response_model=PipelineForecast)
def get_forecast(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> PipelineForecast:
    prospects = repo.list_prospects(principal)
    return build_forecast(prospects, load_pipeline_config(), datetime.now(UTC))
