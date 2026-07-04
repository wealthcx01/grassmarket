"""Contract-invariant tests for the non-CoefficientSet resources: the AI-approval gate and the
first-class Not-Assessed state (defect D9)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from bcap_contracts.assessments import SubcomponentRating
from bcap_contracts.common import EvidenceGrade, MaturityLevel, NonScoreState
from bcap_contracts.deliverables import (
    ApprovalStatus,
    Deliverable,
    DeliverableType,
)
from pydantic import ValidationError


def _now() -> datetime:
    return datetime.now(UTC)


def test_approved_deliverable_requires_human_approver() -> None:
    with pytest.raises(ValidationError):
        Deliverable(
            id=uuid.uuid4(),
            created_at=_now(),
            updated_at=_now(),
            owner_consultant_id=uuid.uuid4(),
            engagement_id=uuid.uuid4(),
            type=DeliverableType.EXECUTIVE_SUMMARY,
            title="Exec Summary",
            ai_generated=True,
            approval_status=ApprovalStatus.APPROVED,  # no approver → refused (non-negotiable #8)
        )


def test_approved_deliverable_with_approver_ok() -> None:
    d = Deliverable(
        id=uuid.uuid4(),
        created_at=_now(),
        updated_at=_now(),
        owner_consultant_id=uuid.uuid4(),
        engagement_id=uuid.uuid4(),
        type=DeliverableType.EXECUTIVE_SUMMARY,
        title="Exec Summary",
        ai_generated=True,
        approval_status=ApprovalStatus.APPROVED,
        approved_by_consultant_id=uuid.uuid4(),
    )
    assert d.approval_status is ApprovalStatus.APPROVED


def test_subcomponent_not_assessed_is_distinct_from_a_score() -> None:
    # Not Assessed carries a state, not a level — it contributes to no computation (defect D9).
    rating = SubcomponentRating(
        module_key="OEMS",
        subcomponent_key="OEMS_SOR",
        state=NonScoreState.NOT_ASSESSED,
    )
    assert rating.level is None
    assert rating.state is NonScoreState.NOT_ASSESSED


def test_subcomponent_cannot_have_both_level_and_state() -> None:
    with pytest.raises(ValidationError):
        SubcomponentRating(
            module_key="OEMS",
            subcomponent_key="OEMS_SOR",
            level=MaturityLevel.ADVANCED,
            state=NonScoreState.NOT_ASSESSED,
            evidence_grade=EvidenceGrade.E3_ARTIFACT,
        )


def test_subcomponent_must_have_level_or_state() -> None:
    with pytest.raises(ValidationError):
        SubcomponentRating(module_key="OEMS", subcomponent_key="OEMS_SOR")


def test_assessed_subcomponent_requires_evidence_grade() -> None:
    with pytest.raises(ValidationError):
        SubcomponentRating(
            module_key="OEMS",
            subcomponent_key="OEMS_SOR",
            level=MaturityLevel.ADVANCED,  # assessed but no evidence grade
        )
