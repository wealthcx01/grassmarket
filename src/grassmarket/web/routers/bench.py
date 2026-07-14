"""Bench-time queue + performance router (GRS-0026, PRD §6).

An idle advisor's landing state: a prioritised queue of what to do next, and their own development
picture. Both are self-scoped — the queue is always the caller's; a performance summary for any id
but the caller's own is a 404 (the cross-advisor/admin view is Holy Corner scope, not this ticket).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from bcap_contracts.bench import BenchQueue, PerformanceSummary
from fastapi import APIRouter, Depends, HTTPException, status

from grassmarket.data.repository import NotFoundError, Principal, Repository
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(prefix="/bench", tags=["bench"])


@router.get("/queue", response_model=BenchQueue)
def get_queue(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> BenchQueue:
    """The caller's prioritised bench-time queue."""
    return repo.get_bench_queue(principal, now=datetime.now(UTC))


@router.get("/performance/{advisor_id}", response_model=PerformanceSummary)
def get_performance(
    advisor_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> PerformanceSummary:
    """The caller's own development picture. A foreign advisor id is a 404 (not shown to exist)."""
    try:
        return repo.get_performance_summary(principal, advisor_id, now=datetime.now(UTC))
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Performance summary not found."
        ) from exc
