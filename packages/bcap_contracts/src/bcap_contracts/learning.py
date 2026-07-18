"""Workbench learning resources (PRD §6) — certification and drill progress, learning content, the
spaced-repetition Power Drill cards, and the approval-gated weekly quiz, scoped per consultant."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    # Real retrieval content (GRS-0139) — the question the advisor tries to recall, and the model
    # answer they reveal before self-grading. Empty on a legacy topic-only card.
    prompt: str = Field(default="", description="The recall question (front of the card).")
    answer: str = Field(default="", description="The model answer (back of the card).")
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


# --- Bruntsfield Academy: the Course → Module → Lesson content model (GRS-0121) ----------
#
# The foundation the whole Academy program (Sales Egoist, the product courses, the ops playbook)
# is authored *into*. A course's editable body is a `CourseTree`; publishing snapshots it into an
# immutable, append-only `CourseVersion` (versions are retained, and re-publishing needs no deploy).
# AI-authored lessons are approval-gated (ADR-0009): an AI lesson cannot appear in a published
# version until a human approves it.


class LessonAuthor(StrEnum):
    """Who wrote a lesson. AI-authored content is approval-gated before it can be published (#8)."""

    HUMAN = "human"
    AI = "ai"


class Lesson(BaseModel):
    """One teaching unit inside a module: a markdown body, an optional video, and links to the
    spaced-repetition drill topics it reinforces. An AI-authored lesson (`author == AI`) is not
    ``approved`` until a human signs off — the approver is then recorded (ADR-0009)."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    title: str = Field(min_length=1)
    body: str = Field(min_length=1, description="Lesson content, markdown.")
    order: int = Field(ge=0)
    author: LessonAuthor = LessonAuthor.HUMAN
    video_ref: str | None = None
    drill_topics: tuple[str, ...] = Field(
        default=(), description="Existing DrillCard topics this lesson reinforces (e.g. 'power:…')."
    )
    measurement: str | None = Field(
        default=None,
        description="How the advisor measures they have applied this lesson (GRS-0122).",
    )
    check_question: str | None = Field(
        default=None,
        description="A retrieval-practice question the advisor answers to complete the lesson "
        "(GRS-0139). None → the reader derives a recall prompt from `measurement`.",
    )
    check_answer: str | None = Field(
        default=None,
        description="The model answer revealed after the advisor attempts the check (GRS-0139). "
        "None → the reader falls back to `measurement` as the answer key.",
    )
    approved: bool = True
    approved_by_consultant_id: UUID | None = None
    approved_at: datetime | None = None

    @model_validator(mode="after")
    def _approval_provenance(self) -> Lesson:
        # An approved lesson that was AI-authored must record WHO approved it (ADR-0009). A human-
        # authored lesson is inherently approved (a human wrote it) and needs no approver.
        if (
            self.author is LessonAuthor.AI
            and self.approved
            and self.approved_by_consultant_id is None
        ):
            raise ValueError("An approved AI-authored lesson must record its approver (ADR-0009).")
        if self.approved_by_consultant_id is not None and not self.approved:
            raise ValueError("A lesson with an approver must be marked approved.")
        return self


class CourseModule(BaseModel):
    """An ordered group of lessons within a course."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    title: str = Field(min_length=1)
    order: int = Field(ge=0)
    lessons: tuple[Lesson, ...] = ()


class CourseTree(BaseModel):
    """The editable body of a course — metadata plus its nested modules/lessons. This is what an
    admin edits in the CMS; publishing snapshots it into an immutable `CourseVersion`."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    certification_credit: CertificationCredit = CertificationCredit.NONE
    mandatory_first: bool = Field(
        default=False,
        description="A new advisor's learning path opens on this course (GRS-0122). At most one "
        "course should carry the flag; the catalog surfaces it first.",
    )
    modules: tuple[CourseModule, ...] = ()


class Course(BaseModel):
    """A catalog course: a stable slug, its current editable draft, and how many versions have been
    published (``latest_version`` is 0 until first publish). Learners see the latest published
    version; admins author against the draft."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    slug: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9-]*$")
    draft: CourseTree
    latest_version: int = Field(default=0, ge=0)
    created_at: datetime
    updated_at: datetime


class CourseVersion(BaseModel):
    """An immutable, published snapshot of a course tree (append-only; retained forever)."""

    model_config = ConfigDict(extra="forbid")

    course_id: UUID
    slug: str = Field(min_length=1)
    version: int = Field(ge=1)
    tree: CourseTree
    published_by_consultant_id: UUID
    published_at: datetime


class LessonCompletion(OwnedResource):
    """One advisor's completion of a single lesson (GRS-0121). Completing every approved lesson of a
    COURSEWORK-credit course grants the coursework credit via the existing certification path."""

    model_config = ConfigDict(extra="forbid")

    course_id: UUID
    lesson_id: UUID
    completed_at: datetime
