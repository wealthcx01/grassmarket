"""Uploaded documents (GRS-0247).

Until this router existed the product had no general upload path: the only inbound route was Path
B's media ingest, which keeps a transcript and discards the file. An advisor with a client's board
pack had nowhere to put it, which is why the founder's own files move by `scp`.

Base64 in JSON, matching the media ingest rather than introducing multipart for one endpoint. Size
is checked BEFORE decoding, so an oversized body is never buffered into memory — the same guard
`ingest_media` uses. Every parent id is checked against the caller, so a cross-owner reference is a
404 and never a stored document pointing at someone else's client.
"""

from __future__ import annotations

import base64
import binascii
from uuid import UUID

from bcap_contracts.documents import Document, UploadDocumentRequest
from fastapi import APIRouter, Depends, HTTPException, Response, status

from grassmarket.config import Settings
from grassmarket.data.repository import (
    DocumentError,
    DocumentTooLargeError,
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
from grassmarket.web.dependencies import (
    get_app_settings,
    get_current_principal,
    get_repository,
)

router = APIRouter(prefix="/documents", tags=["documents"])


def _cipher(settings: Settings = Depends(get_app_settings)) -> TranscriptCipher:
    return FernetTranscriptCipher(settings.transcript_encryption_key)


def _scanner(settings: Settings = Depends(get_app_settings)) -> MediaScanner:
    """The configured scanner, or a readable 503 — never a no-op standing in for a scan."""
    try:
        return build_scanner(settings)
    except ScannerNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


@router.post("", response_model=Document, status_code=status.HTTP_201_CREATED)
def upload_document(
    payload: UploadDocumentRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
    settings: Settings = Depends(get_app_settings),
    cipher: TranscriptCipher = Depends(_cipher),
    scanner: MediaScanner = Depends(_scanner),
) -> Document:
    # Reject on the ENCODED length before decoding, so an oversized body is never expanded into
    # memory (base64 inflates ~4/3, so the raw limit maps to this encoded ceiling).
    if len(payload.content_base64) > (settings.max_upload_bytes * 4) // 3 + 8:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"{payload.filename} exceeds the {settings.max_upload_bytes}-byte limit.",
        )
    try:
        content = base64.b64decode(payload.content_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="content_base64 is not valid base64.",
        ) from exc
    try:
        return repo.store_document(
            principal,
            content=content,
            filename=payload.filename,
            content_type=payload.content_type,
            cipher=cipher,
            scanner=scanner,
            prospect_id=payload.prospect_id,
            workshop_id=payload.workshop_id,
            engagement_id=payload.engagement_id,
            retention_until=payload.retention_until,
            max_bytes=settings.max_upload_bytes,
        )
    except DocumentTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)
        ) from exc
    except MediaThreatError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except DocumentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except (NotFoundError, ScopeViolationError) as exc:
        # A cross-owner or missing parent is refused, never revealed.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Parent record not found."
        ) from exc


@router.get("", response_model=list[Document])
def list_documents(
    prospect_id: UUID | None = None,
    workshop_id: UUID | None = None,
    engagement_id: UUID | None = None,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[Document]:
    return repo.list_documents(
        principal,
        prospect_id=prospect_id,
        workshop_id=workshop_id,
        engagement_id=engagement_id,
    )


@router.get("/{document_id}", response_model=Document)
def get_document(
    document_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Document:
    try:
        return repo.get_document(principal, document_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
        ) from exc


@router.get("/{document_id}/content")
def download_document(
    document_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
    cipher: TranscriptCipher = Depends(_cipher),
) -> Response:
    """The file itself. The stored hash is verified before anything is returned."""
    try:
        content, document = repo.read_document_content(principal, document_id, cipher=cipher)
    except (NotFoundError, ScopeViolationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
        ) from exc
    except DocumentError as exc:
        # A hash mismatch is corruption or tampering. Failing loud beats handing back bytes the
        # advisor would reasonably assume are their file.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    return Response(
        content=content,
        media_type=document.content_type,
        headers={"Content-Disposition": f'attachment; filename="{document.filename}"'},
    )


@router.post("/{document_id}/engagement/{engagement_id}", response_model=Document)
def attach_to_engagement(
    document_id: UUID,
    engagement_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Document:
    """Re-parent a document onto an engagement once one exists (Backend Requests R2).

    The original prospect or workshop link is kept — a document collected during pitching did
    belong to that prospect.
    """
    try:
        return repo.attach_document_to_engagement(principal, document_id, engagement_id)
    except DocumentError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (NotFoundError, ScopeViolationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
        ) from exc
