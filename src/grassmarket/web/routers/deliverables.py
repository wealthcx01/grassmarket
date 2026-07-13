"""Deliverables router (GRS-0015, PRD §5). Generate a Platform Power Report against one of the
consultant's own engagements, list an engagement's deliverables, and download the regenerated .docx.

The client-usable gate is enforced in the service: a client-facing generation on a draft coefficient
set is refused (409). Every handler is scoped through the repository (cross-owner → 404).
"""

from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime
from io import BytesIO
from uuid import UUID

from bcap_contracts.assessments import AssessmentState
from bcap_contracts.deliverables import Deliverable, DeliverableMode, DeliverableType
from bcap_contracts.registry import load_registry
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from grassmarket.atlas import AssessmentInputs
from grassmarket.atlas.draft_coefficients import draft_v1_coefficient_set
from grassmarket.atlas.montecarlo import draft_v1_uncertainty_model
from grassmarket.atlas.results import AtlasResult
from grassmarket.data.repository import (
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
    StoredScoringRun,
)
from grassmarket.deliverables.gate import ClientUsabilityError
from grassmarket.deliverables.service import (
    RenderedDeliverable,
    UnsupportedDeliverableTypeError,
    render_diagnostic_document,
)
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(tags=["deliverables"])

_DOCX_MEDIA = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

_TITLES = {
    DeliverableType.EXECUTIVE_SUMMARY: "Executive Summary",
    DeliverableType.PLATFORM_POWER_REPORT: "Platform Power Report",
    DeliverableType.INFRASTRUCTURE_HEATMAP: "Infrastructure Heatmap",
    DeliverableType.TECHNICAL_APPENDIX: "Technical Appendix",
    DeliverableType.WORKSHOP_OUTPUT: "Workshop Output",
}


class GenerateDeliverableRequest(BaseModel):
    # A draft coefficient set refuses client_facing=True (the gate). Default False → watermarked
    # internal document, which is always permitted.
    client_facing: bool = False
    # Which single-run Diagnostic-pack document to generate (GRS-0018). The roadmap + score
    # evolution have their own generation paths and are refused here (422).
    deliverable_type: DeliverableType = DeliverableType.PLATFORM_POWER_REPORT


def _not_found(detail: str = "Not found.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _resolve_run(
    repo: Repository, principal: Principal, engagement
) -> tuple[StoredScoringRun, str]:
    """The finalised scoring run + subject (client name) an engagement's report is built from."""
    if not engagement.assessment_ids:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Engagement has no linked assessment; finalise an assessment first.",
        )
    assessment = repo.get_assessment(principal, engagement.assessment_ids[0])
    if assessment.state != AssessmentState.FINALISED or assessment.scoring_run_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The linked assessment is not finalised; a report needs a finalised run.",
        )
    record = repo.get_scoring_run_record(principal, assessment.scoring_run_id)
    subject = repo.get_prospect(principal, engagement.prospect_id).company_name
    return record, subject


def _render(
    record: StoredScoringRun,
    subject: str,
    *,
    deliverable_type: DeliverableType,
    client_facing: bool,
    generated_on: date,
) -> RenderedDeliverable:
    registry = load_registry()
    inputs = AssessmentInputs.model_validate_json(record.inputs_json)
    result = AtlasResult.model_validate_json(record.result_json)
    return render_diagnostic_document(
        deliverable_type=deliverable_type,
        inputs=inputs,
        stored_result=result,
        coefficients=draft_v1_coefficient_set(registry),
        registry=registry,
        model=draft_v1_uncertainty_model(),
        subject=subject,
        generated_on=generated_on,
        client_facing=client_facing,
    )


@router.post(
    "/engagements/{engagement_id}/deliverables",
    response_model=Deliverable,
    status_code=status.HTTP_201_CREATED,
)
def generate_deliverable(
    engagement_id: UUID,
    payload: GenerateDeliverableRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Deliverable:
    try:
        engagement = repo.get_engagement(principal, engagement_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found("Engagement not found.") from exc

    record, subject = _resolve_run(repo, principal, engagement)
    dtype = payload.deliverable_type
    now = datetime.now(UTC)
    try:
        rendered = _render(
            record,
            subject,
            deliverable_type=dtype,
            client_facing=payload.client_facing,
            generated_on=now.date(),
        )
    except ClientUsabilityError as exc:
        # The controlling gate: a client-facing pack on a non-client-usable set is refused.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except UnsupportedDeliverableTypeError as exc:
        # A type with its own render path (roadmap / score evolution) is not generable here.
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    digest = hashlib.sha256(
        "|".join(
            [
                str(engagement_id),
                dtype.value,
                str(record.id),
                record.coefficient_version,
                rendered.mode.value,
            ]
        ).encode("utf-8")
    ).hexdigest()
    return repo.create_deliverable(
        principal,
        engagement_id=engagement_id,
        deliverable_type=dtype,
        title=f"{_TITLES[dtype]} — {subject}",
        mode=rendered.mode,
        scoring_run_id=record.id,
        coefficient_version=record.coefficient_version,
        content_hash=digest,
        generated_at=now,
    )


@router.get("/engagements/{engagement_id}/deliverables", response_model=list[Deliverable])
def list_deliverables(
    engagement_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[Deliverable]:
    try:
        return repo.list_deliverables(principal, engagement_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found("Engagement not found.") from exc


@router.get("/deliverables/{deliverable_id}/download")
def download_deliverable(
    deliverable_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> StreamingResponse:
    try:
        deliverable = repo.get_deliverable(principal, deliverable_id)
        engagement = repo.get_engagement(principal, deliverable.engagement_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found("Deliverable not found.") from exc
    if deliverable.scoring_run_id is None:
        raise _not_found("Deliverable has no scoring run to render from.")

    record = repo.get_scoring_run_record(principal, deliverable.scoring_run_id)
    subject = repo.get_prospect(principal, engagement.prospect_id).company_name
    generated_on = (deliverable.generated_at or datetime.now(UTC)).date()
    client_facing = deliverable.mode is DeliverableMode.CLIENT
    try:
        rendered = _render(
            record,
            subject,
            deliverable_type=deliverable.type,
            client_facing=client_facing,
            generated_on=generated_on,
        )
    except ClientUsabilityError as exc:
        # Defense in depth — if the set is no longer client-usable, refuse on download too.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except UnsupportedDeliverableTypeError as exc:
        # A stored deliverable whose type has its own render path (roadmap / evolution) — consistent
        # with generate's 422, never a 500. Unreachable today (generate refuses those types).
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    filename = f"{deliverable.type.value}-{deliverable.id}.docx"
    return StreamingResponse(
        BytesIO(rendered.docx_bytes),
        media_type=_DOCX_MEDIA,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
