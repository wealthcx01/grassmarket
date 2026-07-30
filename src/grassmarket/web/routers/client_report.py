"""The client report, reachable from the app (GRS-0219/0220 wiring).

GRS-0211 built the content model, GRS-0219 the branded PDF and GRS-0220 the shared page. All three
were unreachable: the model takes prose as an input and nothing stored prose, so nothing could
assemble a report to render or share. These routes close that.

* `GET/PUT /deliverables/{id}/report-prose` — the advisor's words.
* `GET /deliverables/{id}/client-report.pdf` — the branded PDF.
* `POST /deliverables/{id}/links` (in `report_links`) now assembles server-side, so the browser
  never has to hold a report together itself.

Every one is scoped through the repository. A report with unwritten sections refuses with a 409
naming them, rather than rendering blanks that look finished.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from io import BytesIO
from uuid import UUID

from bcap_contracts.deliverables import Deliverable, DeliverableMode
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ValidationError

from grassmarket.atlas import AssessmentInputs
from grassmarket.atlas.active import active_uncertainty_model, profile_key_of
from grassmarket.atlas.montecarlo import run_monte_carlo
from grassmarket.atlas.results import AtlasResult
from grassmarket.data.repository import (
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
from grassmarket.deliverables.builder import DeliverableContext
from grassmarket.deliverables.client_report_service import (
    AssembledReport,
    ReportNotAssembledError,
    assemble,
    default_prose,
)
from grassmarket.deliverables.report_pdf import ReportMeta, render_client_report_pdf
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(tags=["client-report"])

_PDF_MEDIA = "application/pdf"

#: The uncertainty draws a report is rendered with. Deterministic given the seed below.
_DRAWS = 2000


class ReportProseResponse(BaseModel):
    """The six sections as stored, or an empty draft if the advisor has not started."""

    sections: dict
    written: bool


class SaveReportProseRequest(BaseModel):
    sections: dict


def _first_message(exc: ValidationError) -> str:
    """The model's own explanation, without pydantic's wrapping.

    A content-model refusal is written to be read by the advisor who caused it ("section 'business'
    states ['3'] without declaring it..."), so it is worth more than a generic 422 body.
    """
    for error in exc.errors():
        message = str(error.get("msg", ""))
        # pydantic prefixes ValueError messages with "Value error, ".
        return message.removeprefix("Value error, ") or "The report's prose was refused."
    return "The report's prose was refused."


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")


def _context(
    repo: Repository, principal: Principal, deliverable_id: UUID
) -> tuple[DeliverableContext, Deliverable, UUID]:
    """The DeliverableContext for a deliverable's finalised run, plus its subject and run id.

    Rebuilt from the STORED run rather than rescored, so the report quotes the immutable finalised
    numbers (non-negotiable #6) and not a fresh computation that might differ.
    """
    try:
        deliverable = repo.get_deliverable(principal, deliverable_id)
        engagement = repo.get_engagement(principal, deliverable.engagement_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found() from exc
    if deliverable.scoring_run_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This deliverable has no finalised scoring run to report on.",
        )

    record = repo.get_scoring_run_record(principal, deliverable.scoring_run_id)
    subject = repo.get_prospect(principal, engagement.prospect_id).company_name
    document = repo.get_assessment(principal, record.assessment_id).document
    profile_key = profile_key_of(document)

    from grassmarket.atlas.active import profile_scoring_context

    registry, coefficients = profile_scoring_context(profile_key)
    inputs = AssessmentInputs.model_validate_json(record.inputs_json)
    result = AtlasResult.model_validate_json(record.result_json)
    model = active_uncertainty_model(profile_key)
    # Seeded from the run id so the same run always renders the same band — a client re-opening
    # their report must not see the range move because the dice fell differently.
    import random

    rng = random.Random(record.id.int % (2**32))
    uncertainty = run_monte_carlo(inputs, coefficients, registry, model, rng, draws=_DRAWS)

    context = DeliverableContext(
        subject=subject,
        result=result,
        uncertainty=uncertainty,
        coefficients=coefficients,
        uncertainty_version=model.version,
        generated_on=(deliverable.generated_at or datetime.now(UTC)).date(),
    )
    return context, deliverable, record.id


def assemble_for(
    repo: Repository, principal: Principal, deliverable_id: UUID
) -> tuple[AssembledReport, Deliverable]:
    """Assemble a deliverable's report, or raise the 409 that names what is unwritten."""
    context, deliverable, run_id = _context(repo, principal, deliverable_id)
    sections_json = repo.get_report_prose(principal, deliverable_id)
    try:
        assembled = assemble(context, scoring_run_id=run_id, sections_json=sections_json)
    except ReportNotAssembledError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValidationError as exc:
        # The content model rejecting the prose is NORMAL and useful — an advisor who writes "we
        # found 3 issues" without declaring the 3 has done something the model is right to catch.
        # Letting that surface as a 500 would make a working guardrail look like a broken app, so
        # the model's own sentence is passed through instead.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=_first_message(exc)
        ) from exc
    return assembled, deliverable


@router.get("/deliverables/{deliverable_id}/report-prose", response_model=ReportProseResponse)
def get_report_prose(
    deliverable_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> ReportProseResponse:
    try:
        stored = repo.get_report_prose(principal, deliverable_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found() from exc
    if stored is None:
        # An empty draft, so the advisor sees the shape of the argument rather than a blank page.
        return ReportProseResponse(sections=default_prose(), written=False)
    return ReportProseResponse(sections=json.loads(stored), written=True)


@router.put("/deliverables/{deliverable_id}/report-prose", response_model=ReportProseResponse)
def save_report_prose(
    deliverable_id: UUID,
    payload: SaveReportProseRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> ReportProseResponse:
    try:
        repo.save_report_prose(
            principal, deliverable_id, sections_json=json.dumps(payload.sections)
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found() from exc
    return ReportProseResponse(sections=payload.sections, written=True)


@router.get("/deliverables/{deliverable_id}/client-report.pdf")
def download_client_report(
    deliverable_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> StreamingResponse:
    """The branded PDF (GRS-0219).

    The watermark follows the deliverable's own mode, so an internal draft downloads stamped without
    the caller choosing to — a draft escaping unmarked is the failure that matters most (ADR-0029).
    """
    assembled, deliverable = assemble_for(repo, principal, deliverable_id)
    engagement = repo.get_engagement(principal, deliverable.engagement_id)
    consultant = repo.get_consultant_by_id(principal.consultant_id)
    prepared_by = consultant.full_name if consultant else "Bruntsfield Advisory Network"

    pdf = render_client_report_pdf(
        assembled.report,
        meta=ReportMeta(
            engagement_title=engagement.title,
            prepared_by=prepared_by,
            generated_on=(deliverable.generated_at or datetime.now(UTC)).date(),
            mode=deliverable.mode,
            non_production=deliverable.mode is not DeliverableMode.CLIENT,
        ),
        figure_data=assembled.figures,
    )
    filename = f"{assembled.report.subject.replace(' ', '-')}-platform-assessment.pdf"
    return StreamingResponse(
        BytesIO(pdf),
        media_type=_PDF_MEDIA,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
