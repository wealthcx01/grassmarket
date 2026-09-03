"""Path B meeting-transcript ingestion router (GRS-0029, PRD §3.3).

Ingest a pasted transcript or an uploaded audio/video file (base64 in JSON — no multipart dep),
transcribe behind a swappable adapter, and store scoped + encrypted at rest. NO AI extraction here
(that is GRS-0030). Every read is the caller's own (an admin may read any); a cross-owner read is a
404. Size + type limits and a malware-scan hook run before anything is stored.
"""

from __future__ import annotations

import base64
import binascii
from datetime import date, datetime
from uuid import UUID

from bcap_contracts.meetings import (
    FOUNDER_APPROVED_CONSENT_WORDING,
    MediaKind,
    MeetingTranscript,
    RecordingKind,
)
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from grassmarket.config import Settings
from grassmarket.data.repository import (
    ConsentRequiredError,
    DocumentError,
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
from grassmarket.pathb.cipher import FernetTranscriptCipher, TranscriptCipher
from grassmarket.pathb.scanning import (
    MediaScanner,
    MediaThreatError,
    ScannerNotConfiguredError,
    build_scanner,
)
from grassmarket.pathb.transcription import (
    Transcriber,
    TranscriberNotConfiguredError,
    TranscriptionError,
    build_transcriber,
)
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


def _transcriber(settings: Settings = Depends(get_app_settings)) -> Transcriber:
    """The configured transcription provider (GRS-0251).

    Resolved from config on every request rather than hardcoded, and a misconfiguration is a 503
    the operator can read — never a quiet downgrade to the offline test double, which is the bug
    this dependency used to be."""
    try:
        return build_transcriber(settings)
    except TranscriberNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


def _scanner(settings: Settings = Depends(get_app_settings)) -> MediaScanner:
    """The configured media scanner (GRS-0251). Same contract as `_transcriber`: configured, or a
    readable 503. Never a no-op standing in for a scan."""
    try:
        return build_scanner(settings)
    except ScannerNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


class PasteTranscriptRequest(BaseModel):
    text: str = Field(min_length=1)
    source_filename: str = Field(min_length=1)
    # Any of the three parents, or none — a workshop is recorded while the client is still a
    # prospect, before an engagement exists (GRS-0254 build 2).
    prospect_id: UUID | None = None
    workshop_id: UUID | None = None
    engagement_id: UUID | None = None
    retention_until: date | None = None


class UploadMediaRequest(BaseModel):
    media_base64: str = Field(min_length=1, description="The media file, base64-encoded.")
    source_filename: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    source_kind: MediaKind
    prospect_id: UUID | None = None
    workshop_id: UUID | None = None
    engagement_id: UUID | None = None
    retention_until: date | None = None
    recording_kind: RecordingKind = Field(
        default=RecordingKind.NOT_RECORDED,
        description="Who was in the room. A recorded session must carry consent; nothing else may.",
    )
    consent_confirmed_at: datetime | None = Field(
        default=None, description="When the advisor confirmed the client agreed."
    )
    consent_wording: str | None = Field(
        default=None,
        description="The exact text shown to the client. Must be the founder-approved wording.",
    )
    keep_recording: bool = Field(
        default=False,
        description="Store the audio alongside the transcript (needs a parent to file it under).",
    )


class ConsentLine(BaseModel):
    """What the recorder must show before a session may be recorded.

    Served rather than hardcoded in the frontend so there is exactly one copy of the wording in the
    system. A client that shows its own text will have the upload refused, which is the point.
    """

    wording: str = Field(description="The exact text to read to the client, shown verbatim.")


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found.")


@router.get("/consent-line", response_model=ConsentLine)
def get_consent_line() -> ConsentLine:
    """The founder-approved consent wording (GRS-0255).

    Unauthenticated-safe in content — it is a script an advisor reads aloud, not client data — but
    it sits behind the same router so a client fetches it the same way it fetches everything else.
    """
    return ConsentLine(wording=FOUNDER_APPROVED_CONSENT_WORDING)


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
            prospect_id=payload.prospect_id,
            workshop_id=payload.workshop_id,
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
            prospect_id=payload.prospect_id,
            workshop_id=payload.workshop_id,
            engagement_id=payload.engagement_id,
            retention_until=payload.retention_until,
            recording_kind=payload.recording_kind,
            consent_confirmed_at=payload.consent_confirmed_at,
            consent_wording=payload.consent_wording,
            keep_recording=payload.keep_recording,
            max_bytes=settings.max_upload_bytes,
        )
    except (NotFoundError, ScopeViolationError) as exc:
        # A cross-owner / missing parent link is refused, never revealed.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prospect, workshop or engagement not found.",
        ) from exc
    except ConsentRequiredError as exc:
        # 422, not 403: the request is well-formed and the caller is allowed here — what is wrong
        # is the recording it describes. Nothing was stored.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except DocumentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
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
