"""Deliverables router (GRS-0015, PRD §5). Generate a Platform Power Report against one of the
consultant's own engagements, list an engagement's deliverables, and download the regenerated .docx.

The client-usable gate is enforced in the service: a client-facing generation on a draft coefficient
set is refused (409). Every handler is scoped through the repository (cross-owner → 404).
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import UTC, date, datetime
from io import BytesIO
from uuid import UUID

from bcap_contracts.assessments import AssessmentDocument, AssessmentState
from bcap_contracts.committee import CommitteeDecision
from bcap_contracts.deliverables import Deliverable, DeliverableMode, DeliverableType
from bcap_contracts.narratives import AINarrative
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from grassmarket.assessments.service import c_index_of
from grassmarket.atlas import AssessmentInputs
from grassmarket.atlas.active import (
    active_uncertainty_model,
    profile_key_of,
    profile_scoring_context,
)
from grassmarket.atlas.results import AtlasResult
from grassmarket.data.repository import (
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
    StoredScoringRun,
)
from grassmarket.deliverables.gate import (
    ClientUsabilityError,
    CommitteePendingError,
    UnapprovedNarrativeError,
    assert_narratives_approved,
)
from grassmarket.deliverables.service import (
    RenderedDeliverable,
    UnsupportedDeliverableTypeError,
    render_diagnostic_document,
    title_for,
)
from grassmarket.web.dependencies import get_current_principal, get_repository

router = APIRouter(tags=["deliverables"])

_DOCX_MEDIA = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


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
) -> tuple[StoredScoringRun, str, str]:
    """The finalised scoring run + subject (client name) + operating-model profile key an
    engagement's report is built from (the profile drives the registry VIEW the run was scored
    under — GRS-0148e)."""
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
    return record, subject, profile_key_of(assessment.document)


def _render(
    record: StoredScoringRun,
    subject: str,
    *,
    profile_key: str,
    document: AssessmentDocument,
    deliverable_type: DeliverableType,
    client_facing: bool,
    generated_on: date,
    narratives: Sequence[AINarrative] = (),
    committee_decisions: Sequence[CommitteeDecision] = (),
) -> RenderedDeliverable:
    # Build the deliverable against the SAME (registry view, coefficient set) the assessment was
    # scored under (GRS-0148e). A wealth/exchange run's modules and metrics are profile-specific
    # (e.g. WEALTH_SUITABILITY), so rendering against the retail superset key-errors → a 500.
    registry, coefficients = profile_scoring_context(profile_key)
    inputs = AssessmentInputs.model_validate_json(record.inputs_json)
    result = AtlasResult.model_validate_json(record.result_json)
    # C is reported alongside V (ADR-0023 / GRS-0164). Computed from the DOCUMENT (the run's stored
    # inputs drop C), the same deterministic path the portfolio + live rail use — so it surfaces
    # even when the coefficients don't fold C into the composite (retail ⇒ result.customer None).
    return render_diagnostic_document(
        deliverable_type=deliverable_type,
        inputs=inputs,
        stored_result=result,
        coefficients=coefficients,
        registry=registry,
        model=active_uncertainty_model(profile_key),
        subject=subject,
        generated_on=generated_on,
        client_facing=client_facing,
        narratives=narratives,
        committee_decisions=committee_decisions,
        reported_c=c_index_of(document, registry),
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

    record, subject, profile_key = _resolve_run(repo, principal, engagement)
    document = repo.get_assessment(principal, record.assessment_id).document
    dtype = payload.deliverable_type
    now = datetime.now(UTC)
    try:
        committee_decisions = repo.list_committee_decisions(principal, record.assessment_id)
        rendered = _render(
            record,
            subject,
            profile_key=profile_key,
            document=document,
            deliverable_type=dtype,
            client_facing=payload.client_facing,
            generated_on=now.date(),
            committee_decisions=committee_decisions,
        )
    except (ClientUsabilityError, CommitteePendingError) as exc:
        # The controlling gates: a client-facing pack on a non-client-usable set, or one whose
        # high-stakes ratings still lack committee sign-off (§8), is refused.
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
        title=f"{title_for(dtype)} — {subject}",
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
    client_facing: bool = False,
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

    # The client pack is client-facing if the deliverable was rendered in CLIENT mode OR the caller
    # explicitly asks for a client-facing download. Either way, the GRS-0017 gate runs FIRST: an
    # unapproved AI narrative refuses the client pack (409) before anything is rendered (#8).
    client_facing = client_facing or deliverable.mode is DeliverableMode.CLIENT
    narratives = repo.list_narratives(principal, deliverable_id)
    try:
        assert_narratives_approved(narratives, client_facing=client_facing)
    except UnapprovedNarrativeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    record = repo.get_scoring_run_record(principal, deliverable.scoring_run_id)
    subject = repo.get_prospect(principal, engagement.prospect_id).company_name
    document = repo.get_assessment(principal, record.assessment_id).document
    profile_key = profile_key_of(document)
    generated_on = (deliverable.generated_at or datetime.now(UTC)).date()
    try:
        committee_decisions = repo.list_committee_decisions(principal, record.assessment_id)
        rendered = _render(
            record,
            subject,
            profile_key=profile_key,
            document=document,
            deliverable_type=deliverable.type,
            client_facing=client_facing,
            generated_on=generated_on,
            narratives=narratives,
            committee_decisions=committee_decisions,
        )
    except (ClientUsabilityError, CommitteePendingError) as exc:
        # Defense in depth — refuse on download if the set is no longer client-usable OR a
        # high-stakes rating still lacks committee sign-off (§8).
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


@router.get("/assessments/{assessment_id}/deliverable-preview")
def preview_assessment_deliverable(
    assessment_id: UUID,
    deliverable_type: DeliverableType = DeliverableType.PLATFORM_POWER_REPORT,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> StreamingResponse:
    """Render a finalised assessment's deliverable directly, without an engagement (GRS-0154).

    The whole point of the solo/sandbox path is to *see the real deliverable*, but generation was
    only reachable via a won deal's engagement — so a finalised sandbox assessment had no route to a
    document (mock-advisor: Priya/Elena/James, HIGH). This previews the INTERNAL, watermarked pack
    from the assessment's own scoring run: it is **never client-facing** (`client_facing=False`), so
    it renders even for a draft wealth/exchange profile — the client-pack gate is untouched. Nothing
    is persisted (a preview, not a stored deliverable). Owner-scoped and fail-loud."""
    try:
        assessment = repo.get_assessment(principal, assessment_id)
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found("Assessment not found.") from exc
    if assessment.state != AssessmentState.FINALISED or assessment.scoring_run_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Finalise the assessment before previewing its deliverable.",
        )
    record = repo.get_scoring_run_record(principal, assessment.scoring_run_id)
    profile_key = profile_key_of(assessment.document)
    now = datetime.now(UTC)
    try:
        committee_decisions = repo.list_committee_decisions(principal, record.assessment_id)
        rendered = _render(
            record,
            assessment.subject,
            profile_key=profile_key,
            document=assessment.document,
            deliverable_type=deliverable_type,
            client_facing=False,  # a preview is internal + watermarked, never client-facing
            generated_on=now.date(),
            committee_decisions=committee_decisions,
        )
    except (ClientUsabilityError, CommitteePendingError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except UnsupportedDeliverableTypeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    filename = f"preview-{deliverable_type.value}-{assessment_id}.docx"
    return StreamingResponse(
        BytesIO(rendered.docx_bytes),
        media_type=_DOCX_MEDIA,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
