"""Calibration router (GRS-0022, Methodology §9) — inter-rater reliability as managed data.

A facilitator (admin) opens a session of shared vignettes; every active assessor submits their own
BLIND rating; on close, the per-anchor weighted kappa and Gwet's AC1 are computed and anchors below
κ 0.6 are flagged for rewrite. The blind is structural: results exist only once the session is
closed, and an assessor only ever sees their own rating — so no rater anchors on the distribution.

Error mapping: an authority refusal (non-facilitator) is 403 (calibration data is org-shared, not
hidden); a missing session is 404; a state/blind/insufficient-data refusal is 409.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from bcap_contracts.calibration import (
    CalibrationRating,
    CalibrationResult,
    CalibrationSession,
    CalibrationVignette,
    RatingEntry,
)
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from grassmarket.data.repository import (
    ConflictError,
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
from grassmarket.web.dependencies import get_current_principal, get_repository
from grassmarket.workbench.calibration import CalibrationStatsError

router = APIRouter(prefix="/calibration", tags=["calibration"])


class CreateSessionRequest(BaseModel):
    title: str = Field(min_length=1)
    vignettes: list[CalibrationVignette] = Field(min_length=1)


class SubmitRatingRequest(BaseModel):
    entries: list[RatingEntry] = Field(min_length=1)


def _forbidden(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Calibration session not found."
    )


def _conflict(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/sessions", response_model=CalibrationSession, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: CreateSessionRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CalibrationSession:
    try:
        return repo.create_calibration_session(
            principal,
            title=payload.title,
            vignettes=tuple(payload.vignettes),
            opened_at=datetime.now(UTC),
        )
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc


@router.get("/sessions", response_model=list[CalibrationSession])
def list_sessions(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[CalibrationSession]:
    return repo.list_calibration_sessions(principal)


@router.get("/sessions/{session_id}", response_model=CalibrationSession)
def get_session(
    session_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CalibrationSession:
    try:
        return repo.get_calibration_session(principal, session_id)
    except NotFoundError as exc:
        raise _not_found() from exc


@router.post("/sessions/{session_id}/ratings", response_model=CalibrationRating)
def submit_rating(
    session_id: UUID,
    payload: SubmitRatingRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CalibrationRating:
    """An assessor submits their blind rating (locked on submit). Must cover exactly the anchors."""
    try:
        return repo.submit_calibration_rating(
            principal,
            session_id,
            entries=tuple(payload.entries),
            submitted_at=datetime.now(UTC),
        )
    except NotFoundError as exc:
        raise _not_found() from exc
    except ConflictError as exc:
        raise _conflict(exc) from exc


@router.get("/sessions/{session_id}/my-rating", response_model=CalibrationRating)
def get_my_rating(
    session_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CalibrationRating:
    try:
        return repo.get_my_calibration_rating(principal, session_id)
    except NotFoundError as exc:
        raise _not_found() from exc


@router.post("/sessions/{session_id}/close", response_model=CalibrationResult)
def close_session(
    session_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CalibrationResult:
    """Close the session and compute the per-anchor agreement + flagged-anchor report. Facilitator/
    admin only; refused if already closed or fewer than two assessors submitted."""
    try:
        return repo.close_calibration_session(principal, session_id, closed_at=datetime.now(UTC))
    except NotFoundError as exc:
        raise _not_found() from exc
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc
    except (ConflictError, CalibrationStatsError) as exc:
        raise _conflict(exc) from exc


@router.get("/sessions/{session_id}/results", response_model=CalibrationResult)
def get_results(
    session_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CalibrationResult:
    """The computed result of a closed session (visible once closed). Blind while OPEN → 409."""
    try:
        return repo.get_calibration_result(principal, session_id)
    except NotFoundError as exc:
        raise _not_found() from exc
    except ConflictError as exc:
        raise _conflict(exc) from exc
