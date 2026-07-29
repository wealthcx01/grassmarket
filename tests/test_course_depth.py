"""The course depth standard has to fail on a thin course (GRS-0215).

This is the test that matters most in the Academy rebuild, and it is the one that did not exist
when GRS-0191 shipped a renderer and no content. A standard nobody can fail is not a standard, so
most of what follows is a deliberately thin fixture being refused for each specific reason.
"""

from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

import pytest
from bcap_contracts.learning import (
    CourseModule,
    CourseTree,
    Lesson,
    SectionTest,
    Slide,
    SlideKind,
    SourceRef,
    SourceRefKind,
    TestQuestion,
)

from grassmarket.workbench.content.depth import (
    MIN_DOING_SLIDES_PER_LESSON,
    MIN_QUESTIONS_PER_SECTION_TEST,
    MIN_SLIDES_PER_LESSON,
    assert_meets_standard,
    check_depth,
)

_REF = SourceRef(title="OpenBB docs", url="https://docs.openbb.co/", kind=SourceRefKind.DOCS)
_BODY = (
    "A slide body long enough to say something real rather than gesture at it, which is the "
    "whole point of the minimum: a two-sentence slide is the old failure at a smaller scale."
)
_LESSON_BODY = (
    "What this lesson is for, and what the advisor will be able to do by the end of it. Stated "
    "up front so a learner can decide whether they already know this, and so an author cannot "
    "leave the purpose implicit in a wall of slides. This opening is not the teaching; the "
    "slides are."
)


def _id(key: str):
    return uuid5(NAMESPACE_URL, f"grassmarket:test:depth:{key}")


def _slides(n: int, *, doing: int = MIN_DOING_SLIDES_PER_LESSON) -> tuple[Slide, ...]:
    out = []
    for i in range(n):
        is_doing = i < doing
        out.append(
            Slide(
                order=i,
                kind=SlideKind.WALKTHROUGH if is_doing else SlideKind.CONCEPT,
                title=f"Slide {i + 1}",
                body=_BODY,
                references=(_REF,) if i == 0 else (),
            )
        )
    return tuple(out)


def _test(n: int = MIN_QUESTIONS_PER_SECTION_TEST) -> SectionTest:
    return SectionTest(
        questions=tuple(
            TestQuestion(
                prompt=f"Question {i + 1}?",
                options=("Right", "Wrong"),
                answer_index=0,
                explanation="Why the right answer is right, which is the part that teaches.",
            )
            for i in range(n)
        )
    )


def _lesson(
    *, slides: int = MIN_SLIDES_PER_LESSON, doing: int | None = None, body: str = _LESSON_BODY
) -> Lesson:
    return Lesson(
        id=_id(f"lesson-{slides}-{doing}-{len(body)}"),
        title="A lesson",
        body=body,
        order=0,
        slides=_slides(slides, doing=MIN_DOING_SLIDES_PER_LESSON if doing is None else doing),
    )


def _course(*, lessons=None, section_test: SectionTest | None = None) -> CourseTree:
    return CourseTree(
        title="A course",
        summary="A course summary.",
        modules=(
            CourseModule(
                id=_id("module"),
                title="Section one",
                order=0,
                lessons=tuple(lessons if lessons is not None else (_lesson(),)),
                section_test=section_test if section_test is not None else _test(),
            ),
        ),
    )


def test_a_course_at_the_standard_passes() -> None:
    assert_meets_standard("product-test", _course())


def test_a_paragraph_is_not_a_lesson() -> None:
    """The founder's sentence, as an assertion."""
    report = check_depth("product-test", _course(lessons=(_lesson(slides=1, doing=1),)))
    assert not report.ok
    assert any("A paragraph is not a lesson" in f for f in report.failures)


def test_a_lesson_of_pure_prose_is_refused() -> None:
    """20 slides that are all reading is not what was asked for."""
    report = check_depth("product-test", _course(lessons=(_lesson(slides=25, doing=0),)))
    assert not report.ok
    assert any("Reading is not learning to sell" in f for f in report.failures)


def test_a_section_with_no_test_is_refused() -> None:
    tree = CourseTree(
        title="A course",
        summary="A course summary.",
        modules=(CourseModule(id=_id("m2"), title="Section one", order=0, lessons=(_lesson(),)),),
    )
    report = check_depth("product-test", tree)
    assert not report.ok
    assert any("no section test" in f for f in report.failures)


def test_a_token_section_test_is_refused() -> None:
    report = check_depth("product-test", _course(section_test=_test(n=1)))
    assert not report.ok
    assert any("minimum for a gate to mean anything" in f for f in report.failures)


def test_an_uncited_lesson_is_refused() -> None:
    lesson = Lesson(
        id=_id("uncited"),
        title="Uncited",
        body=_LESSON_BODY,
        order=0,
        slides=tuple(
            Slide(
                order=i,
                kind=SlideKind.WALKTHROUGH
                if i < MIN_DOING_SLIDES_PER_LESSON
                else SlideKind.CONCEPT,
                title=f"Slide {i + 1}",
                body=_BODY,
            )
            for i in range(MIN_SLIDES_PER_LESSON)
        ),
    )
    report = check_depth("product-test", _course(lessons=(lesson,)))
    assert not report.ok
    assert any("does not go in the course" in f for f in report.failures)


def test_a_lesson_with_no_stated_purpose_is_refused() -> None:
    report = check_depth("product-test", _course(lessons=(_lesson(body="Short."),)))
    assert not report.ok
    assert any("say what the lesson is for" in f for f in report.failures)


def test_a_bloated_lesson_is_refused_too() -> None:
    """The ceiling is as real as the floor: a lesson nobody finishes teaches nothing either."""
    report = check_depth("product-test", _course(lessons=(_lesson(slides=60),)))
    assert not report.ok
    assert any("split it" in f for f in report.failures)


def test_every_failure_is_reported_not_just_the_first() -> None:
    """An author should fix a course in one pass, not play whack-a-mole with the runner."""
    tree = CourseTree(
        title="A course",
        summary="A course summary.",
        modules=(
            CourseModule(
                id=_id("m3"),
                title="Thin section",
                order=0,
                lessons=(_lesson(slides=2, doing=0, body="Short."),),
            ),
        ),
    )
    report = check_depth("product-test", tree)
    assert len(report.failures) >= 4
    assert "Thin section" in report.describe()


def test_the_assertion_message_names_the_course_and_the_reasons() -> None:
    with pytest.raises(AssertionError) as exc:
        assert_meets_standard("product-test", _course(lessons=(_lesson(slides=3, doing=1),)))
    assert "product-test" in str(exc.value)
    assert "A paragraph is not a lesson" in str(exc.value)


# --- Contract-level guards ---------------------------------------------------------------


def test_a_checkpoint_without_a_prompt_is_refused_at_the_contract() -> None:
    """A checkpoint you cannot complete is a slide with an imperative mood."""
    with pytest.raises(ValueError, match="what the advisor has to do"):
        Slide(order=0, kind=SlideKind.CHECKPOINT, title="Do it", body=_BODY)


def test_only_a_checkpoint_carries_a_checkpoint_prompt() -> None:
    with pytest.raises(ValueError, match="Only a checkpoint slide"):
        Slide(
            order=0,
            kind=SlideKind.CONCEPT,
            title="Read this",
            body=_BODY,
            checkpoint_prompt="Do something",
        )


def test_a_test_answer_must_point_at_a_real_option() -> None:
    with pytest.raises(ValueError, match="past the end of the options"):
        TestQuestion(
            prompt="Q?", options=("a", "b"), answer_index=2, explanation="Because of the reason."
        )
