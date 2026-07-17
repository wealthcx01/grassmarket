"""Bruntsfield Academy course logic (GRS-0121, ADR-0028) — pure functions over a `CourseTree`.

The publish gate, the AI-approval sweep, and the course-completion check live here as deterministic
transforms with no persistence and no wall-clock reads (timestamps are injected). The repository
composes these; keeping them pure makes the gate rules directly testable.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from bcap_contracts.learning import CourseModule, CourseTree, Lesson, LessonAuthor


def iter_lessons(tree: CourseTree) -> tuple[Lesson, ...]:
    """Every lesson in the tree, flattened (module order preserved)."""
    return tuple(lesson for module in tree.modules for lesson in module.lessons)


def unapproved_ai_lessons(tree: CourseTree) -> tuple[str, ...]:
    """Titles of AI-authored lessons not yet approved — the publish blockers (ADR-0009)."""
    return tuple(
        lesson.title
        for lesson in iter_lessons(tree)
        if lesson.author is LessonAuthor.AI and not lesson.approved
    )


def approved_lesson_ids(tree: CourseTree) -> frozenset[UUID]:
    """The lessons a learner can complete — a course is 'complete' once all of these are done."""
    return frozenset(lesson.id for lesson in iter_lessons(tree) if lesson.approved)


def is_course_complete(tree: CourseTree, completed_lesson_ids: frozenset[UUID]) -> bool:
    """True once the learner has completed every approved lesson. An empty course is not complete
    (there is nothing to have learned)."""
    approved = approved_lesson_ids(tree)
    return bool(approved) and approved <= completed_lesson_ids


def approve_lesson_in_tree(
    tree: CourseTree, lesson_id: UUID, *, approver_id: UUID, now: datetime
) -> CourseTree:
    """Return a copy of the tree with the given lesson marked approved + its approver recorded.
    Raises KeyError if no lesson matches (fail loud — never silently no-op)."""
    found = False
    new_modules: list[CourseModule] = []
    for module in tree.modules:
        new_lessons: list[Lesson] = []
        for lesson in module.lessons:
            if lesson.id == lesson_id:
                found = True
                lesson = lesson.model_copy(
                    update={
                        "approved": True,
                        "approved_by_consultant_id": approver_id,
                        "approved_at": now,
                    }
                )
            new_lessons.append(lesson)
        new_modules.append(module.model_copy(update={"lessons": tuple(new_lessons)}))
    if not found:
        raise KeyError(lesson_id)
    return tree.model_copy(update={"modules": tuple(new_modules)})
