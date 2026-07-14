"""FastAPI application factory.

`create_app` builds the engine + session factory from settings, bootstraps the schema
(Loop 0: `create_all`; Alembic becomes the source of truth as the schema grows), wires CORS to
the frontend origin, and mounts the routers. Tests call `create_app(settings=..., engine=...)`
with an isolated in-memory database — the same factory, no special test path.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Engine

from grassmarket import __version__
from grassmarket.config import Settings, get_settings
from grassmarket.data.database import make_engine, make_session_factory, run_migrations
from grassmarket.web.routers import (
    arena,
    assessments,
    auth,
    bench,
    calibration,
    certification,
    committee,
    deliverables,
    earnings,
    engagements,
    extraction,
    guidance,
    health,
    narratives,
    pipeline,
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
        allow_origins=[settings.frontend_origin],
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
    app.include_router(deliverables.router)
    app.include_router(narratives.router)
    app.include_router(assessments.router)
    app.include_router(committee.router)
    app.include_router(calibration.router)
    app.include_router(certification.router)
    app.include_router(workbench.router)
    app.include_router(arena.router)
    app.include_router(bench.router)
    app.include_router(earnings.router)
    app.include_router(transcripts.router)
    app.include_router(extraction.router)
    app.include_router(guidance.router)
    app.include_router(registry.router)
    return app
