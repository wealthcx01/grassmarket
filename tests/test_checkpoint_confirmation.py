"""Confirming a checkpoint (GRS-0239 scope 3).

CHECKPOINT slides rendered "Do this now:" and then did nothing — no control, no state, no record —
while the content contract promised "the advisor produces something and confirms they did". Ticking
through a lesson meant scrolling past its checkpoints.

Three things are worth holding down: only a real checkpoint can be confirmed (or a client could
invent progress the content never offered), confirming twice is a no-op rather than an error, and
the denominator comes from the published content so "0 of 3" is distinguishable from "no
checkpoints here".
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from bcap_contracts.learning import (
    CourseModule,
    CourseTree,
    Lesson,
    LessonAuthor,
    Slide,
    SlideKind,
)

from grassmarket.data.repository import ConflictError, NotFoundError, Repository

NOW = datetime(2026, 8, 21, tzinfo=UTC)
SLUG = "checkpoint-course"


def _slide(order: int, kind: SlideKind) -> Slide:
    # A CHECKPOINT slide must carry a prompt — the contract refuses one without it, which is the
    # rule that makes "the advisor produces something" enforceable rather than aspirational.
    prompt = "Open the wizard and rate one module." if kind is SlideKind.CHECKPOINT else None
    return Slide(
        order=order, kind=kind, title=f"Slide {order}", body="Body.", checkpoint_prompt=prompt
    )


@pytest.fixture
def lesson_id(repo: Repository, admin, alice):
    """A published course with one lesson: two checkpoints (orders 1 and 3) among four slides."""
    lid = uuid4()
    tree = CourseTree(
        title="Checkpoints",
        summary="A course with checkpoints in it, for testing the confirmation path.",
        modules=(
            CourseModule(
                id=uuid4(),
                title="Only module",
                order=0,
                lessons=(
                    Lesson(
                        id=lid,
                        title="Only lesson",
                        body="By the end of this lesson you can confirm a checkpoint.",
                        order=0,
                        author=LessonAuthor.HUMAN,
                        slides=(
                            _slide(0, SlideKind.CONCEPT),
                            _slide(1, SlideKind.CHECKPOINT),
                            _slide(2, SlideKind.EXAMPLE),
                            _slide(3, SlideKind.CHECKPOINT),
                        ),
                    ),
                ),
            ),
        ),
    )
    repo.upsert_published_course(admin.principal, SLUG, tree, now=NOW)
    return lid


class TestConfirming:
    def test_a_checkpoint_can_be_confirmed(self, repo: Repository, alice, lesson_id) -> None:
        repo.confirm_checkpoint(alice.principal, SLUG, lesson_id, 1, now=NOW)
        assert repo.checkpoint_progress(alice.principal, SLUG, lesson_id) == (1, 2)

    def test_confirming_twice_is_a_no_op(self, repo: Repository, alice, lesson_id) -> None:
        """Re-ticking a self-reported checkpoint is not a mistake worth an error.

        Deliberately the opposite of `complete_lesson`, which raises on a duplicate: completing a
        lesson twice IS a mistake, and conflating the two would teach advisors to ignore the error.
        """
        repo.confirm_checkpoint(alice.principal, SLUG, lesson_id, 1, now=NOW)
        repo.confirm_checkpoint(alice.principal, SLUG, lesson_id, 1, now=NOW)
        assert repo.checkpoint_progress(alice.principal, SLUG, lesson_id) == (1, 2)

    def test_a_non_checkpoint_slide_is_refused(self, repo: Repository, alice, lesson_id) -> None:
        """Otherwise a client could invent progress the content model never offered."""
        with pytest.raises(ConflictError):
            repo.confirm_checkpoint(alice.principal, SLUG, lesson_id, 0, now=NOW)

    def test_a_slide_that_does_not_exist_is_refused(
        self, repo: Repository, alice, lesson_id
    ) -> None:
        with pytest.raises(NotFoundError):
            repo.confirm_checkpoint(alice.principal, SLUG, lesson_id, 99, now=NOW)

    def test_a_lesson_that_does_not_exist_is_refused(self, repo: Repository, alice) -> None:
        with pytest.raises(NotFoundError):
            repo.confirm_checkpoint(alice.principal, SLUG, uuid4(), 1, now=NOW)


class TestProgress:
    def test_the_denominator_comes_from_the_content(
        self, repo: Repository, alice, lesson_id
    ) -> None:
        """0 of 2 is a different statement from "no checkpoints here", and must read differently."""
        assert repo.checkpoint_progress(alice.principal, SLUG, lesson_id) == (0, 2)

    def test_both_checkpoints_confirm_independently(
        self, repo: Repository, alice, lesson_id
    ) -> None:
        repo.confirm_checkpoint(alice.principal, SLUG, lesson_id, 1, now=NOW)
        assert repo.checkpoint_progress(alice.principal, SLUG, lesson_id) == (1, 2)
        repo.confirm_checkpoint(alice.principal, SLUG, lesson_id, 3, now=NOW)
        assert repo.checkpoint_progress(alice.principal, SLUG, lesson_id) == (2, 2)

    def test_progress_is_per_advisor(self, repo: Repository, alice, bob, lesson_id) -> None:
        """The one property that would be a scoping leak if wrong (#9)."""
        repo.confirm_checkpoint(alice.principal, SLUG, lesson_id, 1, now=NOW)
        assert repo.checkpoint_progress(alice.principal, SLUG, lesson_id) == (1, 2)
        assert repo.checkpoint_progress(bob.principal, SLUG, lesson_id) == (0, 2)

    def test_a_stale_confirmation_cannot_inflate_the_count(
        self, repo: Repository, alice, lesson_id
    ) -> None:
        """The re-ordering limitation, bounded.

        A confirmation is keyed on slide POSITION, so re-authoring a lesson can leave one pointing
        at a position that is no longer a checkpoint. It must not then count: the confirmed set is
        intersected with the CURRENT checkpoint positions, so progress can never exceed its own
        denominator — which is the part that would actually mislead someone.
        """
        from grassmarket.data.models import CheckpointConfirmationORM

        repo.confirm_checkpoint(alice.principal, SLUG, lesson_id, 1, now=NOW)
        # A leftover confirmation on slide 2, which is an EXAMPLE, not a checkpoint.
        repo._session.add(
            CheckpointConfirmationORM(
                owner_consultant_id=alice.principal.consultant_id,
                course_id=repo._get_course_row(SLUG).id,
                lesson_id=lesson_id,
                slide_order=2,
                confirmed_at=NOW,
            )
        )
        repo._session.flush()
        confirmed, total = repo.checkpoint_progress(alice.principal, SLUG, lesson_id)
        assert (confirmed, total) == (1, 2)
        assert confirmed <= total


def test_a_lesson_with_no_checkpoints_reports_zero_of_zero(repo: Repository, admin, alice) -> None:
    """Not (0, 1) or a crash — a lesson without checkpoints simply has none to do."""
    lid = uuid4()
    tree = CourseTree(
        title="No checkpoints",
        summary="A course whose lesson has no checkpoint slides at all.",
        modules=(
            CourseModule(
                id=uuid4(),
                title="M",
                order=0,
                lessons=(
                    Lesson(
                        id=lid,
                        title="L",
                        body="By the end of this lesson you can do nothing in particular.",
                        order=0,
                        author=LessonAuthor.HUMAN,
                        slides=(_slide(0, SlideKind.CONCEPT),),
                    ),
                ),
            ),
        ),
    )
    repo.upsert_published_course(admin.principal, "no-checkpoints", tree, now=NOW)
    assert repo.checkpoint_progress(alice.principal, "no-checkpoints", lid) == (0, 0)
