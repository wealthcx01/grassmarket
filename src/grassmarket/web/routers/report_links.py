"""Shared client-report links (GRS-0220).

Two audiences, two very different security postures, in one file so the asymmetry stays visible:

* **Advisor routes** (`/deliverables/{id}/links`, `/report-links/{id}`) are scoped through the
  repository like everything else — you can only share, revoke and inspect your own deliverables.
* **Public routes** (`/shared/report/{token}`) carry NO principal. The token is the credential. They
  are therefore written defensively: an unknown, expired and revoked token all produce the same 404
  with the same body, so the endpoint cannot be used to discover which links exist or to learn that
  a link once existed and was withdrawn.

Read tracking is disclosed on the page itself. The event endpoint accepts only a section and a dwell
time; there is nowhere here to put an IP or a user agent even if someone wanted to.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from bcap_contracts.assessments import RecordProvenance
from bcap_contracts.client_report import ClientReport, ReportSectionKind
from bcap_contracts.deliverables import DeliverableMode
from bcap_contracts.report_links import ClientReportLink, ReportReadReport
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from grassmarket.data.repository import NotFoundError, Principal, Repository, ScopeViolationError
from grassmarket.deliverables.report_links import (
    ExpiryTooLongError,
    LinkNotUsableError,
    assert_usable,
    generate_token,
    hash_token,
    resolve_expiry,
)
from grassmarket.web.dependencies import get_current_principal, get_repository
from grassmarket.web.routers.client_report import assemble_for, assert_report_releasable

router = APIRouter(tags=["report-links"])
public_router = APIRouter(tags=["shared-report"])

#: One body for every failure on the public path. An attacker learns nothing from the difference
#: between "never existed", "expired" and "revoked", so there is no difference to read.
_OPAQUE = "This report link is not available."

#: Shown on the shared page, before any event is sent. Disclosure is the product requirement: the
#: reader is told in plain words, not in a policy nobody opens.
TRACKING_NOTICE = (
    "Bruntsfield can see which sections of this report you open and how long you spend on them. "
    "Nothing else about you is recorded."
)


def _opaque_404() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_OPAQUE)


class SharedReportPayload(BaseModel):
    """What the public page renders: the report, plus the figure series it draws.

    The SAME content model the PDF consumes (GRS-0219), so the two renditions cannot tell a client
    different things — the parity the ticket asks for is structural, not a convention.
    """

    report: ClientReport
    #: Parallel label/value lists per figure, drawn as SVG client-side rather than as images.
    figures: dict[str, dict[str, object]]
    #: Shown on the page. The reader is told, in plain words, that reads are visible to the sender.
    tracking_notice: str
    # The two marks the PDF draws, carried IN the snapshot rather than derived when the page is
    # served (GRS-0229). Stored at issue for the same reason the report is: a record reclassified
    # later must not retroactively change what an already-issued link shows a reader. Defaulted so
    # a link issued before this field existed deserialises — and defaulted to the SAFE value, which
    # for a mark is "show it": a legacy snapshot whose provenance nobody recorded is exactly the
    # case where the reader should be told the numbers may not be production.
    non_production: bool = True
    #: The deliverable was DRAFT_INTERNAL at issue — not approved for client use.
    draft: bool = True


class CreateLinkRequest(BaseModel):
    recipient_label: str = Field(min_length=1, max_length=200)
    #: Days the link should live. Omitted → the 30-day default; over the cap → 422, never clamped.
    expires_in_days: int | None = Field(default=None, ge=1)


class CreatedLinkResponse(BaseModel):
    """The ONLY time the plaintext token is returned. It is not stored and cannot be re-read."""

    link: ClientReportLink
    token: str
    #: Convenience for the advisor: the path to hand to the client.
    share_path: str


class ReadEventRequest(BaseModel):
    section: ReportSectionKind
    #: Milliseconds the section was on screen. Clamped by the contract's plausibility cap.
    dwell_ms: int = Field(ge=0, le=6 * 60 * 60 * 1000)


@router.post(
    "/deliverables/{deliverable_id}/links",
    response_model=CreatedLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_link(
    deliverable_id: UUID,
    payload: CreateLinkRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CreatedLinkResponse:
    token = generate_token()
    try:
        expires_at = resolve_expiry(
            now=datetime.now(UTC),
            requested=timedelta(days=payload.expires_in_days) if payload.expires_in_days else None,
        )
    except ExpiryTooLongError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    # Assembled HERE, not sent by the browser. The client report is a gated artefact; letting the
    # page post its own version of one would put the content model's rules on the wrong side of the
    # trust boundary. A report with unwritten sections raises the 409 that names them.
    assembled, deliverable, provenance = assemble_for(repo, principal, deliverable_id)
    # The same gate the PDF takes (GRS-0245). A share link is the MORE exposed rendition — no
    # login, anyone with the URL — so gating the download and not this one would have been the
    # wrong way round.
    assert_report_releasable(repo, principal, deliverable_id, provenance)
    snapshot = SharedReportPayload(
        report=assembled.report,
        # Serialised from the ONE figure source the PDF also renders from, including the order and
        # the per-entry notes — so the two renditions cannot disagree about what is shown or in what
        # sequence (GRS-0233 scope 3).
        figures={
            name: {
                "labels": list(series.labels),
                "values": list(series.values),
                "notes": list(series.notes),
                "ordered": series.ordered,
            }
            for name, series in (
                ("maturity", assembled.figures.maturity),
                ("value_buildup", assembled.figures.value_buildup),
                ("module_breakdown", assembled.figures.module_breakdown),
            )
        },
        tracking_notice=TRACKING_NOTICE,
        # Provenance, not mode — see the note on `assemble_for`. A sandbox record scored on an
        # activated profile resolves to mode=CLIENT, so keying the mark on mode alone showed
        # nothing on precisely the records that most need it.
        non_production=provenance is not RecordProvenance.PRODUCTION,
        draft=deliverable.mode is not DeliverableMode.CLIENT,
    )

    try:
        link = repo.create_report_link(
            principal,
            deliverable_id=deliverable_id,
            token_hash=hash_token(token),
            recipient_label=payload.recipient_label,
            report_json=snapshot.model_dump_json(),
            expires_at=expires_at,
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.") from exc

    return CreatedLinkResponse(link=link, token=token, share_path=f"/r/{token}")


@router.get("/deliverables/{deliverable_id}/links", response_model=list[ClientReportLink])
def list_links(
    deliverable_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[ClientReportLink]:
    try:
        return repo.list_report_links(principal, deliverable_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.") from exc


@router.post("/report-links/{link_id}/revoke", response_model=ClientReportLink)
def revoke_link(
    link_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> ClientReportLink:
    """Immediate. The next public request with that token gets the same 404 as an unknown one."""
    try:
        return repo.revoke_report_link(principal, link_id, at=datetime.now(UTC))
    except (NotFoundError, ScopeViolationError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.") from exc


@router.get("/report-links/{link_id}/reads", response_model=ReportReadReport)
def read_summary(
    link_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> ReportReadReport:
    """What the client actually read — the thing that changes how an advisor prepares for a call."""
    try:
        return repo.read_summary_for_link(principal, link_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.") from exc


def _resolve_public(repo: Repository, token: str) -> ClientReportLink:
    """Resolve a public token or raise the one opaque 404.

    Re-checks usability on every call. A link revoked a second ago must stop working now, not at the
    next cache expiry — which is why nothing here is cached.
    """
    link = repo.resolve_report_link_by_token_hash(hash_token(token))
    if link is None:
        raise _opaque_404()
    try:
        assert_usable(link)
    except LinkNotUsableError as exc:
        raise _opaque_404() from exc
    return link


@public_router.get("/shared/report/{token}", response_model=SharedReportPayload)
def read_shared_report(
    token: str,
    repo: Repository = Depends(get_repository),
) -> SharedReportPayload:
    """The report a client sees. No login, no session — the token is the credential.

    Serves the SNAPSHOT taken when the link was issued, not a fresh render. A client who read this
    page last week and quotes it back must be quoting something that still exists.
    """
    link = _resolve_public(repo, token)
    snapshot = repo.report_snapshot_for_link(link.id)
    repo.touch_report_link(link.id, at=datetime.now(UTC))
    return SharedReportPayload.model_validate_json(snapshot)


@public_router.post("/shared/report/{token}/events", status_code=status.HTTP_204_NO_CONTENT)
def record_read_event(
    token: str,
    payload: ReadEventRequest,
    repo: Repository = Depends(get_repository),
) -> None:
    """Record that a section was read. No principal — the token already authorised it.

    Returns 204 with no body: the reader's page has no use for the event id, and echoing anything
    back would be one more thing the public surface reveals.
    """
    link = _resolve_public(repo, token)
    now = datetime.now(UTC)
    repo.record_read_event(
        link_id=link.id,
        section=payload.section.value,
        dwell_ms=payload.dwell_ms,
        occurred_at=now,
    )
    repo.touch_report_link(link.id, at=now)
