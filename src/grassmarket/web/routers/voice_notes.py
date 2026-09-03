"""Voice note → pipeline proposal router (GRS-0249 scope 4).

Propose a pipeline update from one of the caller's voice notes, read it back with its per-field
confidence, then confirm or discard it. The proposal is a **gated proposal**: nothing reaches the
prospect until an advisor confirms, and what they confirm is what is applied — not what was
suggested (non-negotiable #8).

Every write goes through the same repository choke-points a typed update uses, so a confirmed
voice note is indistinguishable from typing downstream. Owner-scoped throughout; a cross-owner
reference is a 404, never a 403.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from bcap_contracts.pipeline import IllegalStageTransition
from bcap_contracts.voice_notes import PipelineField, VoiceNoteProposal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from grassmarket.config import Settings
from grassmarket.data.repository import (
    ConflictError,
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
from grassmarket.pathb.cipher import FernetTranscriptCipher, TranscriptCipher
from grassmarket.pathb.pipeline_extraction import EmptyPipelineExtractor, PipelineExtractor
from grassmarket.web.dependencies import (
    get_app_settings,
    get_current_principal,
    get_repository,
)

router = APIRouter(prefix="/voice-notes", tags=["voice-notes"])


def _cipher(settings: Settings = Depends(get_app_settings)) -> TranscriptCipher:
    return FernetTranscriptCipher(settings.transcript_encryption_key)


def _extractor() -> PipelineExtractor:
    """The pipeline extraction provider.

    The offline default proposes nothing, because real extraction is AI and a keyword-matched
    stage change would be a fabrication wearing a confidence score. The Claude extractor is wired
    here (or by overriding this dependency) at the composition root — a DI swap, never a change to
    the handler. This mirrors `routers.extraction._extractor` exactly.
    """
    return EmptyPipelineExtractor()


class ProposeRequest(BaseModel):
    prospect_id: UUID
    transcript_id: UUID


class ConfirmRequest(BaseModel):
    """The advisor's final answer, per field.

    A field that is present is applied with the value given — their correction, or the proposal's
    own suggestion where they accepted it unchanged. A field that is **absent or null is not
    applied**, whatever was proposed. There is no "accept everything" shortcut on purpose: the
    approval has to name what it approves, or it is not an approval.
    """

    fields: dict[PipelineField, str | None] = Field(default_factory=dict)


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Voice note proposal not found."
    )


@router.post("", response_model=VoiceNoteProposal, status_code=status.HTTP_201_CREATED)
def propose(
    payload: ProposeRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
    cipher: TranscriptCipher = Depends(_cipher),
    extractor: PipelineExtractor = Depends(_extractor),
) -> VoiceNoteProposal:
    try:
        return repo.propose_pipeline_update(
            principal,
            prospect_id=payload.prospect_id,
            transcript_id=payload.transcript_id,
            extractor=extractor,
            cipher=cipher,
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prospect or voice note not found."
        ) from exc


@router.get("", response_model=list[VoiceNoteProposal])
def list_proposals(
    prospect_id: UUID | None = None,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[VoiceNoteProposal]:
    return repo.list_pipeline_proposals(principal, prospect_id=prospect_id)


@router.get("/{proposal_id}", response_model=VoiceNoteProposal)
def get_proposal(
    proposal_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> VoiceNoteProposal:
    try:
        return repo.get_pipeline_proposal(principal, proposal_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found() from exc


@router.post("/{proposal_id}/confirm", response_model=VoiceNoteProposal)
def confirm(
    proposal_id: UUID,
    payload: ConfirmRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> VoiceNoteProposal:
    """Apply what the advisor confirmed. This is the gate; nothing before it wrote anything."""
    try:
        return repo.confirm_pipeline_update(
            principal, proposal_id, now=datetime.now(UTC), confirmed=payload.fields
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found() from exc
    except (ConflictError, IllegalStageTransition) as exc:
        # An unparseable date, nowhere to file the note, a proposal already answered — or a stage
        # move the lifecycle graph refuses. All of them are 409 with the reason, because the
        # advisor can act on every one of them; none is an internal failure. The graph raises its
        # own exception type rather than ConflictError, and catching only the latter turned "you
        # cannot go straight from prospect to delivered" into a 500.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{proposal_id}/discard", response_model=VoiceNoteProposal)
def discard(
    proposal_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> VoiceNoteProposal:
    """The advisor read it and said no. Recorded, not deleted."""
    try:
        return repo.discard_pipeline_update(principal, proposal_id, now=datetime.now(UTC))
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found() from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
