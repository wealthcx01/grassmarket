"""Workbench learning resources (PRD §6) — certification and drill progress, scoped per
consultant. The Workbench itself is Loop 5; these contracts fix the shape now."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bcap_contracts.base import OwnedResource


class CertificationModule(StrEnum):
    BRUNTSFIELD_PLAYBOOK = "bruntsfield_playbook"
    ATLAS_METHODOLOGY = "atlas_methodology"
    WORKSHOP_DELIVERY = "workshop_delivery"


class ModuleProgressStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"


class CertificationProgress(OwnedResource):
    model_config = ConfigDict(extra="forbid")

    module: CertificationModule
    status: ModuleProgressStatus = ModuleProgressStatus.NOT_STARTED
    exam_score: float | None = Field(default=None, ge=0.0, le=1.0)


class DrillResult(OwnedResource):
    """A spaced-repetition Power Drill result (PRD §6)."""

    model_config = ConfigDict(extra="forbid")

    topic: str = Field(min_length=1)
    correct: int = Field(ge=0)
    total: int = Field(gt=0)
