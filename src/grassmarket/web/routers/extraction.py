"""Path B extraction → review router (GRS-0030, PRD §3.3).

Propose an extraction from one of the caller's transcripts (a gated proposal — nothing reaches the
assessment until confirmed, #8), inspect its per-field provenance, then confirm it (optionally with
corrections). Confirmation applies the document through the SAME Path A save path, so confirmed data
is indistinguishable from manual entry — the byte-identical-scoring guarantee. Owner-scoped.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from bcap_contracts.assessments import AssessmentDocument
from bcap_contracts.extraction import Extraction, FieldProvenance
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from grassmarket.config import Settings
from grassmarket.data.repository import (
    ConflictError,
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
from grassmarket.pathb.cipher import FernetTranscriptCipher, TranscriptCipher
from grassmarket.pathb.extraction import EmptyExtractor, Extractor
from grassmarket.web.dependencies import (
    get_app_settings,
    get_current_principal,
    get_repository,
)

router = APIRouter(prefix="/extractions", tags=["path-b"])


def _cipher(settings: Settings = Depends(get_app_settings)) -> TranscriptCipher:
    return FernetTranscriptCipher(settings.transcript_encryption_key)


def _extractor() -> Extractor:
    """The extraction provider. The offline default proposes an empty document (real extraction is
    AI); the Claude extractor is wired here (or by overriding this dependency) at the composition
    root — a config/DI swap, never a change to the route handler."""
    return EmptyExtractor()


class ProposeRequest(BaseModel):
    assessment_id: UUID
    transcript_id: UUID


class ConfirmRequest(BaseModel):
    corrected_document: AssessmentDocument | None = None


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found.")


@router.post("", response_model=Extraction, status_code=status.HTTP_201_CREATED)
def propose_extraction(
    payload: ProposeRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
    cipher: TranscriptCipher = Depends(_cipher),
    extractor: Extractor = Depends(_extractor),
) -> Extraction:
    try:
        return repo.propose_extraction(
            principal,
            assessment_id=payload.assessment_id,
            transcript_id=payload.transcript_id,
            extractor=extractor,
            cipher=cipher,
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found("Assessment or transcript") from exc


@router.get("/{extraction_id}", response_model=Extraction)
def get_extraction(
    extraction_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Extraction:
    try:
        return repo.get_extraction(principal, extraction_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found("Extraction") from exc


@router.get("/{extraction_id}/provenance", response_model=list[FieldProvenance])
def list_provenance(
    extraction_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[FieldProvenance]:
    try:
        return repo.list_field_provenance(principal, extraction_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found("Extraction") from exc


@router.post("/{extraction_id}/confirm", response_model=Extraction)
def confirm_extraction(
    extraction_id: UUID,
    payload: ConfirmRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Extraction:
    try:
        return repo.confirm_extraction(
            principal,
            extraction_id,
            now=datetime.now(UTC),
            corrected_document=payload.corrected_document,
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found("Extraction") from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
