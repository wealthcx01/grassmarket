"""Earnings router (GRS-0028, PRD §7).

Self-service transparency: an advisor views their own commission lines, roll-up summary, and a
downloadable statement. Recording a commission and advancing its payment status are ADMIN/finance
actions (objective money facts are never self-attested) — a non-admin gets a 403. All views are
strictly self-scoped; the cross-advisor aggregate is Holy Corner scope, not this ticket.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from io import BytesIO
from uuid import UUID

from bcap_contracts.commissions import (
    CommissionLine,
    EarningsSummary,
    PaymentStatus,
    SourcingAttribution,
)
from bcap_contracts.money import Currency, Money
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from grassmarket.data.repository import (
    ConflictError,
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
from grassmarket.earnings.statement import build_earnings_statement
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(prefix="/earnings", tags=["earnings"])

_DOCX_MEDIA = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class RecordCommissionRequest(BaseModel):
    advisor_id: UUID
    engagement_id: UUID
    base_value_minor: int = Field(ge=0, description="Engagement contract value in minor units.")
    currency: Currency = Currency.GBP
    base_value_ref: str = Field(min_length=1, description="Where the contract value comes from.")
    attribution: SourcingAttribution
    earned_on: date


class ClaimRecoveryFeeRequest(BaseModel):
    earned_on: date


class AdvancePaymentRequest(BaseModel):
    to_status: PaymentStatus


def _forbidden(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


def _conflict(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


# --- self-service views ------------------------------------------------------------------


@router.get("/commissions", response_model=list[CommissionLine])
def list_commissions(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[CommissionLine]:
    return repo.list_commission_lines(principal)


@router.get("/summary", response_model=EarningsSummary)
def get_summary(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> EarningsSummary:
    try:
        return repo.earnings_summary(principal, now=datetime.now(UTC))
    except ConflictError as exc:  # mixed-currency lines refuse to sum (not reachable today)
        raise _conflict(exc) from exc


@router.get("/statement")
def download_statement(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> StreamingResponse:
    now = datetime.now(UTC)
    try:
        summary = repo.earnings_summary(principal, now=now)
    except ConflictError as exc:
        raise _conflict(exc) from exc
    lines = repo.list_commission_lines(principal)
    docx = build_earnings_statement(
        summary=summary,
        lines=lines,
        consultant_name=repo.own_display_name(principal),
        generated_on=now.date(),
    )
    return StreamingResponse(
        BytesIO(docx),
        media_type=_DOCX_MEDIA,
        headers={"Content-Disposition": 'attachment; filename="earnings-statement.docx"'},
    )


# --- admin / finance actions -------------------------------------------------------------


@router.post("/commissions", response_model=CommissionLine, status_code=status.HTTP_201_CREATED)
def record_commission(
    payload: RecordCommissionRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CommissionLine:
    base_value = Money(
        amount_minor=payload.base_value_minor,
        currency=payload.currency,
        assumption_register_ref=payload.base_value_ref,
    )
    try:
        return repo.record_engagement_commission(
            principal,
            advisor_id=payload.advisor_id,
            engagement_id=payload.engagement_id,
            base_value=base_value,
            attribution=payload.attribution,
            earned_on=payload.earned_on,
        )
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:  # e.g. a base value in a currency the schedule doesn't price
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.post("/recovery-fees/{attribution_id}/claim", response_model=CommissionLine)
def claim_recovery_fee(
    attribution_id: UUID,
    payload: ClaimRecoveryFeeRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CommissionLine:
    try:
        return repo.claim_recovery_fee(
            principal, attribution_id=attribution_id, earned_on=payload.earned_on
        )
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise _conflict(exc) from exc


@router.post("/commissions/{line_id}/payment", response_model=CommissionLine)
def advance_payment(
    line_id: UUID,
    payload: AdvancePaymentRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CommissionLine:
    try:
        return repo.advance_commission_payment(principal, line_id, to_status=payload.to_status)
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise _conflict(exc) from exc
