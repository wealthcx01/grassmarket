"""FastAPI application factory.

`create_app` builds the engine + session factory from settings, bootstraps the schema
(Loop 0: `create_all`; Alembic becomes the source of truth as the schema grows), wires CORS to
the frontend origin, and mounts the routers. Tests call `create_app(settings=..., engine=...)`
with an isolated in-memory database — the same factory, no special test path.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import Engine

from grassmarket import __version__
from grassmarket.config import Settings, get_settings
from grassmarket.data.database import make_engine, make_session_factory, run_migrations
from grassmarket.data.repository import (
    ConflictError,
    EngagementLinkError,
    NotFoundError,
    RepositoryError,
    ScopeViolationError,
    WorkshopStateError,
)
from grassmarket.pathb.cipher import TranscriptCipherError
from grassmarket.web.routers import (
    arena,
    assessments,
    auth,
    bench,
    calibration,
    certification,
    committee,
    compliance,
    consultants,
    deliverables,
    earnings,
    engagements,
    entities,
    extraction,
    guidance,
    health,
    narratives,
    pipeline,
    predictions,
    prospects,
    registry,
    transcripts,
    workbench,
    workshops,
)


def create_app(settings: Settings | None = None, *, engine: Engine | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine = engine or make_engine(settings.database_url)
    session_factory = make_session_factory(engine)

    # Schema is the Alembic migrations (GRS-0006 retired create_all from the app path).
    run_migrations(engine)

    app = FastAPI(
        title="Grassmarket — Bruntsfield Advisor Studio",
        version=__version__,
        summary="Advisor platform for the Bruntsfield Advisory Network (Loop 0 scaffold).",
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(prospects.router)
    app.include_router(pipeline.router)
    app.include_router(workshops.router)
    app.include_router(workshops.fees_router)
    app.include_router(engagements.router)
    app.include_router(entities.router)
    app.include_router(deliverables.router)
    app.include_router(narratives.router)
    app.include_router(assessments.router)
    app.include_router(committee.router)
    app.include_router(committee.queue_router)
    app.include_router(calibration.router)
    app.include_router(certification.router)
    app.include_router(workbench.router)
    app.include_router(arena.router)
    app.include_router(bench.router)
    app.include_router(earnings.router)
    app.include_router(transcripts.router)
    app.include_router(extraction.router)
    app.include_router(predictions.router)
    app.include_router(predictions.benchmark_router)
    app.include_router(compliance.router)
    app.include_router(guidance.router)
    app.include_router(registry.router)
    app.include_router(consultants.router)
    _register_exception_handlers(app)
    return app


# Repository errors a route forgot to translate should still map to their proper HTTP code, not a
# bare 500. Routes that catch these explicitly still win — this only fires for the ones that slip
# through (a safety net, never the primary path).
_CONFLICT_ERRORS = (ConflictError, WorkshopStateError, EngagementLinkError)


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RepositoryError)
    async def _repository_error(_: Request, exc: RepositoryError) -> JSONResponse:
        if isinstance(exc, ScopeViolationError):
            # Never confirm the existence of a resource the caller can't access.
            return JSONResponse(status_code=404, content={"detail": "Not found."})
        if isinstance(exc, NotFoundError):
            return JSONResponse(status_code=404, content={"detail": str(exc)})
        if isinstance(exc, _CONFLICT_ERRORS):
            return JSONResponse(status_code=409, content={"detail": str(exc)})
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})

    @app.exception_handler(TranscriptCipherError)
    async def _decrypt_error(_: Request, __: TranscriptCipherError) -> JSONResponse:
        # Key rotation or a corrupt ciphertext — a controlled 5xx, never an uncaught traceback, and
        # never the raw crypto detail.
        return JSONResponse(
            status_code=500,
            content={"detail": "A stored transcript could not be decrypted."},
        )
