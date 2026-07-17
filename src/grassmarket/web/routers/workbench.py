"""Workbench router (GRS-0024, PRD §6) — Power Drills, learning content, and the weekly quiz.

Drills are per-advisor spaced-repetition cards (SM-2): create a card, see what's due, answer with a
recall grade and it reschedules. Learning modules are shared content whose completion feeds
certification evidence (GRS-0023). The weekly quiz is AI-drafted and gated — an advisor only ever
sees an APPROVED quiz (non-negotiable #8).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from bcap_contracts.learning import (
    CertificationCredit,
    ContentCompletion,
    Course,
    CourseTree,
    CourseVersion,
    DrillCard,
    GeneratedQuiz,
    LearningKind,
    LearningModule,
    LessonCompletion,
)
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from grassmarket.data.repository import (
    ConflictError,
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
from grassmarket.web.dependencies import get_current_principal, get_repository
from grassmarket.workbench.drills import DrillGradeError
from grassmarket.workbench.quiz import TemplateQuizDrafter

router = APIRouter(prefix="/workbench", tags=["workbench"])


class DrillCardRequest(BaseModel):
    topic: str = Field(min_length=1)


class AnswerRequest(BaseModel):
    grade: int = Field(ge=0, le=5)


class LearningModuleRequest(BaseModel):
    kind: LearningKind
    title: str = Field(min_length=1)
    methodology_ref: str = Field(min_length=1)
    certification_credit: CertificationCredit = CertificationCredit.NONE


class CompleteRequest(BaseModel):
    score: float | None = Field(default=None, ge=0.0, le=1.0)


class ProposeQuizRequest(BaseModel):
    title: str = Field(min_length=1)
    topics: list[str] = Field(min_length=1)


class CreateCourseRequest(BaseModel):
    slug: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9-]*$")
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    certification_credit: CertificationCredit = CertificationCredit.NONE


def _forbidden(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found.")


def _conflict(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


# --- Power Drills -----------------------------------------------------------------------


@router.post("/drills/cards", response_model=DrillCard, status_code=status.HTTP_201_CREATED)
def create_drill_card(
    payload: DrillCardRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> DrillCard:
    try:
        return repo.create_drill_card(principal, topic=payload.topic, now=datetime.now(UTC))
    except ConflictError as exc:
        raise _conflict(exc) from exc


@router.get("/drills/cards", response_model=list[DrillCard])
def list_drill_cards(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[DrillCard]:
    return repo.list_drill_cards(principal)


@router.get("/drills/cards/due", response_model=list[DrillCard])
def list_due_drill_cards(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[DrillCard]:
    return repo.list_due_drill_cards(principal, now=datetime.now(UTC))


@router.post("/drills/cards/{card_id}/answer", response_model=DrillCard)
def answer_drill_card(
    card_id: UUID,
    payload: AnswerRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> DrillCard:
    """Grade your recall (0–5) — the card reschedules itself by SM-2."""
    try:
        return repo.answer_drill_card(
            principal, card_id, grade=payload.grade, now=datetime.now(UTC)
        )
    except (NotFoundError, ScopeViolationError) as exc:
        raise _not_found("Drill card") from exc
    except DrillGradeError as exc:  # defence-in-depth; the request model already bounds grade 0..5
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# --- Learning content -------------------------------------------------------------------


@router.post(
    "/learning/modules", response_model=LearningModule, status_code=status.HTTP_201_CREATED
)
def create_learning_module(
    payload: LearningModuleRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> LearningModule:
    try:
        return repo.create_learning_module(
            principal,
            kind=payload.kind,
            title=payload.title,
            methodology_ref=payload.methodology_ref,
            certification_credit=payload.certification_credit,
        )
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc


@router.get("/learning/modules", response_model=list[LearningModule])
def list_learning_modules(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[LearningModule]:
    return repo.list_learning_modules(principal)


@router.post("/learning/modules/{module_id}/complete", response_model=ContentCompletion)
def complete_learning_module(
    module_id: UUID,
    payload: CompleteRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> ContentCompletion:
    """Complete a module — an exam quiz records your score, and completion feeds certification
    evidence (coursework / exam) for the human-gated promotion (GRS-0023)."""
    try:
        return repo.complete_learning_module(
            principal, module_id, score=payload.score, now=datetime.now(UTC)
        )
    except NotFoundError as exc:
        raise _not_found("Learning module") from exc
    except ConflictError as exc:
        raise _conflict(exc) from exc


# --- The weekly quiz (AI-drafted, approval-gated) ---------------------------------------


@router.post("/quizzes", response_model=GeneratedQuiz, status_code=status.HTTP_201_CREATED)
def propose_quiz(
    payload: ProposeQuizRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> GeneratedQuiz:
    """AI-draft a weekly quiz from the given topics — stored as a PROPOSAL, never advisor-visible
    until an admin approves it (#8)."""
    drafter = TemplateQuizDrafter()
    try:
        return repo.propose_quiz(
            principal,
            title=payload.title,
            questions=drafter.draft(payload.topics),
            drafter_version=drafter.version,
        )
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc


@router.post("/quizzes/{quiz_id}/approve", response_model=GeneratedQuiz)
def approve_quiz(
    quiz_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> GeneratedQuiz:
    return _decide_quiz(repo, principal, quiz_id, approve=True)


@router.post("/quizzes/{quiz_id}/reject", response_model=GeneratedQuiz)
def reject_quiz(
    quiz_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> GeneratedQuiz:
    return _decide_quiz(repo, principal, quiz_id, approve=False)


def _decide_quiz(
    repo: Repository, principal: Principal, quiz_id: UUID, *, approve: bool
) -> GeneratedQuiz:
    try:
        return repo.decide_quiz(principal, quiz_id, approve=approve, now=datetime.now(UTC))
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc
    except NotFoundError as exc:
        raise _not_found("Quiz") from exc
    except ConflictError as exc:
        raise _conflict(exc) from exc


@router.get("/quizzes", response_model=list[GeneratedQuiz])
def list_quizzes(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[GeneratedQuiz]:
    """An advisor sees only APPROVED quizzes; an admin sees every one, whatever its status (#8)."""
    return repo.list_quizzes(principal)


@router.get("/quizzes/{quiz_id}", response_model=GeneratedQuiz)
def get_quiz(
    quiz_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> GeneratedQuiz:
    try:
        return repo.get_quiz(principal, quiz_id)
    except NotFoundError as exc:
        raise _not_found("Quiz") from exc


# --- Bruntsfield Academy courses (CMS, GRS-0121) ----------------------------------------
# Authoring (create/edit/approve/publish) is admin-gated in the repository → a ScopeViolationError
# maps to 403. Reading the published catalog is org-wide. AI-authored lessons are approval-gated:
# publishing refuses while any remain unapproved (409).


@router.post("/courses", response_model=Course, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CreateCourseRequest,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Course:
    try:
        return repo.create_course(
            principal,
            slug=payload.slug,
            title=payload.title,
            summary=payload.summary,
            certification_credit=payload.certification_credit,
        )
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc
    except ConflictError as exc:
        raise _conflict(exc) from exc


@router.get("/courses", response_model=list[Course])
def list_courses(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[Course]:
    """Every course DRAFT (admin authoring view)."""
    try:
        return repo.list_courses(principal)
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc


@router.get("/courses/published", response_model=list[CourseVersion])
def list_published_courses(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[CourseVersion]:
    """The learner-facing catalog: the latest published version of every course (org-wide)."""
    return repo.list_published_courses(principal)


@router.get("/courses/{slug}", response_model=Course)
def get_course(
    slug: str,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Course:
    """The editable draft (admin authoring view)."""
    try:
        return repo.get_course(principal, slug)
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc
    except NotFoundError as exc:
        raise _not_found("Course") from exc


@router.put("/courses/{slug}/draft", response_model=Course)
def save_course_draft(
    slug: str,
    tree: CourseTree,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Course:
    """Replace the editable draft tree (admin). Does not publish."""
    try:
        return repo.save_course_draft(principal, slug, tree)
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc
    except NotFoundError as exc:
        raise _not_found("Course") from exc


@router.post("/courses/{slug}/lessons/{lesson_id}/approve", response_model=Course)
def approve_course_lesson(
    slug: str,
    lesson_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Course:
    """Approve one AI-authored lesson so it can be published (ADR-0009)."""
    try:
        return repo.approve_course_lesson(principal, slug, lesson_id, now=datetime.now(UTC))
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc
    except NotFoundError as exc:
        raise _not_found("Lesson") from exc


@router.post("/courses/{slug}/publish", response_model=CourseVersion)
def publish_course(
    slug: str,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CourseVersion:
    """Snapshot the draft into a new immutable version. Refuses (409) while any AI lesson is
    unapproved (ADR-0009)."""
    try:
        return repo.publish_course(principal, slug, now=datetime.now(UTC))
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc
    except NotFoundError as exc:
        raise _not_found("Course") from exc
    except ConflictError as exc:
        raise _conflict(exc) from exc


@router.get("/courses/{slug}/published", response_model=CourseVersion)
def get_published_course(
    slug: str,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> CourseVersion:
    """The latest published version of one course (org-wide)."""
    try:
        return repo.get_published_course(principal, slug)
    except NotFoundError as exc:
        raise _not_found("Published course") from exc


@router.get("/courses/{slug}/versions", response_model=list[CourseVersion])
def list_course_versions(
    slug: str,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> list[CourseVersion]:
    """Every retained published version of a course (admin)."""
    try:
        return repo.list_course_versions(principal, slug)
    except ScopeViolationError as exc:
        raise _forbidden(exc) from exc
    except NotFoundError as exc:
        raise _not_found("Course") from exc


@router.post("/courses/{slug}/lessons/{lesson_id}/complete", response_model=LessonCompletion)
def complete_lesson(
    slug: str,
    lesson_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> LessonCompletion:
    """Complete one lesson of the latest published course. Completing every lesson of a
    coursework-credit course grants the coursework credit via the existing certification path."""
    try:
        return repo.complete_lesson(principal, slug, lesson_id, now=datetime.now(UTC))
    except NotFoundError as exc:
        raise _not_found("Lesson") from exc
    except ConflictError as exc:
        raise _conflict(exc) from exc
