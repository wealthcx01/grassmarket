"""Practice Arena router (GRS-0025, PRD §6) — AI-simulated discovery practice.

An admin authors shared scenarios; an advisor starts a session, conducts the role-played discovery
(the live chat is exercised manually — not in CI), then submits the transcript. Submission scores
the conversation deterministically on extraction completeness and attaches AI-drafted (labelled)
feedback (#8). Scores persist to the advisor's own history. No client data — vignettes only.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from bcap_contracts.arena import (
    ArenaModuleTarget,
    ArenaPowerTarget,
    ArenaScenario,
    ArenaSession,
    ArenaTurn,
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
from grassmarket.workbench.arena import TemplateArenaFeedbackDrafter

router = APIRouter(prefix="/arena", tags=["arena"])


class ScenarioRequest(BaseModel):
    title: str = Field(min_length=1)
    brief: str = Field(min_length=1)
    client_persona: str = Field(min_length=1)
    target_powers: list[ArenaPowerTarget] = Field(min_length=1)
    target_modules: list[ArenaModuleTarget] = []
    evidence_cues: list[str] = []


class SubmitRequest(BaseModel):
    transcript: list[ArenaTurn] = Field(min_length=1)


def _forbidden(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found.")


@router.post("/scenarios", response_model=ArenaScenario, status_code=status.HTTP_201_CREATED)
def create_scenario(
    payload: ScenarioRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> ArenaScenario:
    try:
        return repo.create_arena_scenario(
            principal,
            title=payload.title,
            brief=payload.brief,
            client_persona=payload.client_persona,
            target_powers=tuple(payload.target_powers),
            target_modules=tuple(payload.target_modules),
            evidence_cues=tuple(payload.evidence_cues),
        )
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc


@router.get("/scenarios", response_model=list[ArenaScenario])
def list_scenarios(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[ArenaScenario]:
    return repo.list_arena_scenarios(principal)


@router.get("/scenarios/{scenario_id}", response_model=ArenaScenario)
def get_scenario(
    scenario_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> ArenaScenario:
    try:
        return repo.get_arena_scenario(principal, scenario_id)
    except NotFoundError as exc:
        raise _not_found("Arena scenario") from exc


@router.post(
    "/scenarios/{scenario_id}/sessions",
    response_model=ArenaSession,
    status_code=status.HTTP_201_CREATED,
)
def start_session(
    scenario_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> ArenaSession:
    """Start a practice session against a scenario. Conduct the role-play, then submit it."""
    try:
        return repo.start_arena_session(principal, scenario_id)
    except NotFoundError as exc:
        raise _not_found("Arena scenario") from exc


@router.post("/sessions/{session_id}/submit", response_model=ArenaSession)
def submit_session(
    session_id: UUID,
    payload: SubmitRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> ArenaSession:
    """Submit the discovery transcript — scored deterministically, with AI-drafted feedback (#8)."""
    try:
        return repo.submit_arena_session(
            principal,
            session_id,
            transcript=tuple(payload.transcript),
            drafter=TemplateArenaFeedbackDrafter(),
            now=datetime.now(UTC),
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found("Arena session") from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/sessions", response_model=list[ArenaSession])
def list_sessions(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[ArenaSession]:
    """The caller's own arena history."""
    return repo.list_arena_sessions(principal)


@router.get("/sessions/{session_id}", response_model=ArenaSession)
def get_session(
    session_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> ArenaSession:
    try:
        return repo.get_arena_session(principal, session_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found("Arena session") from exc
