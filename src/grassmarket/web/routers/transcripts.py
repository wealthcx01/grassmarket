"""Path B meeting-transcript ingestion router (GRS-0029, PRD §3.3).

Ingest a pasted transcript or an uploaded audio/video file (base64 in JSON — no multipart dep),
transcribe behind a swappable adapter, and store scoped + encrypted at rest. NO AI extraction here
(that is GRS-0030). Every read is the caller's own (an admin may read any); a cross-owner read is a
404. Size + type limits and a malware-scan hook run before anything is stored.
"""

from __future__ import annotations

import base64
import binascii
from datetime import date
from uuid import UUID

from bcap_contracts.meetings import MediaKind, MeetingTranscript
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from grassmarket.config import Settings
from grassmarket.data.repository import (
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
from grassmarket.pathb.cipher import FernetTranscriptCipher, TranscriptCipher
from grassmarket.pathb.scanning import AllowAllScanner, MediaScanner, MediaThreatError
from grassmarket.pathb.transcription import EchoTranscriber, Transcriber, TranscriptionError
from grassmarket.web.dependencies import (
    get_app_settings,
    get_current_principal,
    get_repository,
)

router = APIRouter(prefix="/transcripts", tags=["path-b"])

# Only audio/video may be uploaded as media (a pasted transcript uses the /text endpoint).
_ALLOWED_MEDIA_KINDS = {MediaKind.AUDIO, MediaKind.VIDEO}


def _cipher(settings: Settings = Depends(get_app_settings)) -> TranscriptCipher:
    return FernetTranscriptCipher(settings.transcript_encryption_key)


def _transcriber() -> Transcriber:
    """The transcription provider. The offline echo transcriber is the default; the real Whisper
    adapter is wired here (or by overriding this dependency) at the composition root — a config/DI
    swap, never a change to the route handler."""
    return EchoTranscriber()


def _scanner() -> MediaScanner:
    """The media scanner. The permissive default; a real AV scanner swaps in by overriding this."""
    return AllowAllScanner()


class PasteTranscriptRequest(BaseModel):
    text: str = Field(min_length=1)
    source_filename: str = Field(min_length=1)
    engagement_id: UUID | None = None
    retention_until: date | None = None


class UploadMediaRequest(BaseModel):
    media_base64: str = Field(min_length=1, description="The media file, base64-encoded.")
    source_filename: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    source_kind: MediaKind
    engagement_id: UUID | None = None
    retention_until: date | None = None


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found.")


@router.post("/text", response_model=MeetingTranscript, status_code=status.HTTP_201_CREATED)
def ingest_text(
    payload: PasteTranscriptRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
    cipher: TranscriptCipher = Depends(_cipher),
) -> MeetingTranscript:
    try:
        return repo.ingest_pasted_transcript(
            principal,
            text=payload.text,
            source_filename=payload.source_filename,
            cipher=cipher,
            engagement_id=payload.engagement_id,
            retention_until=payload.retention_until,
        )
    except (NotFoundError, ScopeViolationError) as exc:
        # A cross-owner / missing engagement link is refused, never revealed.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Engagement not found."
        ) from exc


@router.post("/media", response_model=MeetingTranscript, status_code=status.HTTP_201_CREATED)
def ingest_media(
    payload: UploadMediaRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
    settings: Settings = Depends(get_app_settings),
    cipher: TranscriptCipher = Depends(_cipher),
    transcriber: Transcriber = Depends(_transcriber),
    scanner: MediaScanner = Depends(_scanner),
) -> MeetingTranscript:
    if payload.source_kind not in _ALLOWED_MEDIA_KINDS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="source_kind must be 'audio' or 'video' for a media upload.",
        )
    # Reject on the encoded length BEFORE decoding, so an oversized body is never buffered/decoded
    # into memory (base64 inflates ~4/3, so the raw limit maps to this encoded ceiling).
    if len(payload.media_base64) > (settings.max_upload_bytes * 4) // 3 + 8:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Media exceeds the {settings.max_upload_bytes}-byte upload limit.",
        )
    try:
        media = base64.b64decode(payload.media_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=422, detail="media_base64 is not valid base64.") from exc
    if len(media) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Media exceeds the {settings.max_upload_bytes}-byte upload limit.",
        )
    try:
        return repo.ingest_media(
            principal,
            media=media,
            source_filename=payload.source_filename,
            content_type=payload.content_type,
            source_kind=payload.source_kind,
            transcriber=transcriber,
            scanner=scanner,
            cipher=cipher,
            engagement_id=payload.engagement_id,
            retention_until=payload.retention_until,
        )
    except (NotFoundError, ScopeViolationError) as exc:
        # A cross-owner / missing engagement link is refused, never revealed.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Engagement not found."
        ) from exc
    except MediaThreatError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except TranscriptionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.get("", response_model=list[MeetingTranscript])
def list_transcripts(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
    cipher: TranscriptCipher = Depends(_cipher),
) -> list[MeetingTranscript]:
    return repo.list_transcripts(principal, cipher=cipher)


@router.get("/{transcript_id}", response_model=MeetingTranscript)
def get_transcript(
    transcript_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
    cipher: TranscriptCipher = Depends(_cipher),
) -> MeetingTranscript:
    try:
        return repo.get_transcript(principal, transcript_id, cipher=cipher)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found() from exc
