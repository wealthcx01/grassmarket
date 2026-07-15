"""Prediction register + benchmark router (GRS-0031, Methodology v1.2 §11).

Register lever-level predictions against a finalised scoring run, surface due follow-ups, record a
realised value (which scores the prediction — a hit/miss and a Brier score), and ingest a finalised
score into the ANONYMISED benchmark population. Predictions are owner-scoped; the benchmark is
de-identified and org-wide.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from bcap_contracts.money import Currency, Money
from bcap_contracts.predictions import BenchmarkRow, BenchmarkSector, Prediction
from bcap_contracts.value import LeverValuation
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from grassmarket.data.repository import (
    MAX_PAGE_LIMIT,
    ConflictError,
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
from grassmarket.predictions.logic import predictions_from_levers
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(prefix="/predictions", tags=["validation"])
benchmark_router = APIRouter(prefix="/benchmark", tags=["validation"])


class RegisterRequest(BaseModel):
    scoring_run_id: UUID
    levers: list[LeverValuation] = Field(min_length=1)
    horizon_months: int = Field(gt=0)
    probability: float = Field(ge=0.0, le=1.0)
    follow_up_due: date


class RealiseRequest(BaseModel):
    realised_delta_minor: int
    currency: Currency = Currency.GBP
    realised_ref: str = Field(min_length=1)


class IngestBenchmarkRequest(BaseModel):
    scoring_run_id: UUID
    sector: BenchmarkSector | None = None


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found.")


@router.post("", response_model=list[Prediction], status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[Prediction]:
    try:
        return repo.register_predictions(
            principal,
            scoring_run_id=payload.scoring_run_id,
            specs=predictions_from_levers(payload.levers),
            horizon_months=payload.horizon_months,
            probability=payload.probability,
            follow_up_due=payload.follow_up_due,
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found("Scoring run") from exc


@router.get("", response_model=list[Prediction])
def list_predictions(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[Prediction]:
    return repo.list_predictions(principal)


@router.get("/follow-ups/due", response_model=list[Prediction])
def due_follow_ups(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[Prediction]:
    return repo.list_due_follow_ups(principal, now=datetime.now(UTC))


@router.post("/{prediction_id}/realise", response_model=Prediction)
def realise(
    prediction_id: UUID,
    payload: RealiseRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Prediction:
    realised = Money(
        amount_minor=payload.realised_delta_minor,
        currency=payload.currency,
        assumption_register_ref=payload.realised_ref,
    )
    try:
        return repo.record_realised_value(
            principal, prediction_id, realised_delta=realised, now=datetime.now(UTC)
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found("Prediction") from exc
    except (ConflictError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@benchmark_router.post("/ingest", response_model=BenchmarkRow, status_code=status.HTTP_201_CREATED)
def ingest(
    payload: IngestBenchmarkRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> BenchmarkRow:
    try:
        return repo.ingest_benchmark(
            principal, payload.scoring_run_id, sector=payload.sector, now=datetime.now(UTC)
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found("Scoring run") from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@benchmark_router.get("", response_model=list[BenchmarkRow])
def list_benchmark(
    _principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
    limit: int = Query(default=100, ge=1, le=MAX_PAGE_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> list[BenchmarkRow]:
    return repo.list_benchmark_rows(limit=limit, offset=offset)
