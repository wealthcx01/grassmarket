"""Workbench learning resources (PRD §6) — certification and drill progress, learning content, the
spaced-repetition Power Drill cards, and the approval-gated weekly quiz, scoped per consultant."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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


# --- Power Drills: spaced-repetition cards (GRS-0024, SM-2) ------------------------------


class DrillCard(OwnedResource):
    """One advisor's spaced-repetition state for a drill TOPIC (a power / triad / module / anchor).
    The SM-2 fields (`repetitions`, `easiness`, `interval_days`) update on every review; `due_at` is
    when it next surfaces; `streak` is consecutive passes."""

    model_config = ConfigDict(extra="forbid")

    topic: str = Field(min_length=1, description="e.g. 'power:SCALE_ECONOMIES' or 'module:OEMS'.")
    repetitions: int = Field(default=0, ge=0)
    easiness: float = Field(default=2.5, ge=1.3)
    interval_days: int = Field(default=0, ge=0)
    due_at: datetime
    streak: int = Field(default=0, ge=0)
    last_reviewed_at: datetime | None = None


# --- Learning content + completion (feeds certification evidence, GRS-0023) --------------


class LearningKind(StrEnum):
    PLAYBOOK = "playbook"
    SALES_JOURNEY = "sales_journey"  # old-school / new-school journeys
    TECHNICAL_PRIMER = "technical_primer"
    EXAM_QUIZ = "exam_quiz"


class CertificationCredit(StrEnum):
    """What completing a module grants toward certification evidence (§9). Only COURSEWORK is
    self-service — it is binary and platform-verifiable ("did the module"). An EXAM score is
    objective, so it is never self-attested: the certification exam is PROCTORED and admin-recorded
    (GRS-0023). An exam-quiz here is practice content, not a certification credit (ADR-0014)."""

    NONE = "none"
    COURSEWORK = "coursework"  # completion marks the coursework credit


class LearningModule(OwnedResource):
    """A shared learning-content item (playbook module, sales journey, primer, practice exam quiz).
    Completing it may grant the coursework credit; each links back to the methodology taught."""

    model_config = ConfigDict(extra="forbid")

    kind: LearningKind
    title: str = Field(min_length=1)
    methodology_ref: str = Field(min_length=1, description="The rubric/methodology section taught.")
    certification_credit: CertificationCredit = CertificationCredit.NONE


class ContentCompletion(OwnedResource):
    """One advisor's completion of a learning module. `owner_consultant_id` is the advisor; a
    self-assessment `score` may be recorded for a practice exam quiz (their own tracking — it does
    NOT feed certification, which uses proctored scores). Completion is what feeds coursework
    evidence."""

    model_config = ConfigDict(extra="forbid")

    module_id: UUID
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    completed_at: datetime


# --- The weekly quiz: AI-generated, approval-gated (non-negotiable #8) -------------------


class QuizStatus(StrEnum):
    """AI-generated content is PROPOSED and reaches an advisor only once APPROVED (#8)."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"


class QuizQuestion(BaseModel):
    """One quiz question. The answer links back to the section it teaches (question-bank rule)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    methodology_ref: str = Field(min_length=1)


class GeneratedQuiz(OwnedResource):
    """A weekly quiz drafted by AI from Briefing content and gated: never advisor-visible until a
    human approves it (non-negotiable #8). Versioned by the drafter that produced it."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    status: QuizStatus = QuizStatus.PROPOSED
    questions: tuple[QuizQuestion, ...] = Field(min_length=1)
    drafter_version: str = Field(min_length=1)
    approved_by_consultant_id: UUID | None = None
    approved_at: datetime | None = None
