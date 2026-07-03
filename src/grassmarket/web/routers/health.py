"""Health endpoints. `/health` is liveness (used by the Railway healthcheck) and never touches
the database. `/health/ready` is readiness and pings the DB — it fails loud if the store is
unreachable rather than reporting a hollow OK."""

from __future__ import annotations

from fastapi import APIRouter, Request
from sqlalchemy import text

from grassmarket import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict[str, str]:
    return {
        "status": "ok",
        "service": "grassmarket",
        "version": __version__,
        "env": request.app.state.settings.env,
    }


@router.get("/health/ready")
def ready(request: Request) -> dict[str, str]:
    factory = request.app.state.session_factory
    session = factory()
    try:
        session.execute(text("SELECT 1"))
    finally:
        session.close()
    return {"status": "ready"}
