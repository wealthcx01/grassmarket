"""The Sales Egoist course, rebuilt from committed source (GRS-0218).

The acceptance the ticket sets is a human one — "the founder reads the course and recognises the
material they gave us, developed rather than compressed" — so these tests cover the part a machine
can check: that the course meets the depth standard, that every lesson cites the committed source
rather than a paraphrase, and that the specific claims from the curriculum which make the course
*this* course rather than a generic sales course are actually present.

That last group is the important one. The failure being corrected was a course that summarised the
source into something true, bland and interchangeable; a depth standard alone would have passed it,
because 177 slides of generic sales advice is still 177 slides.
"""

from __future__ import annotations

import pytest
from bcap_contracts.learning import SlideKind

from grassmarket.workbench.content.depth import (
    LEGACY_COURSES,
    MAX_SLIDES_PER_LESSON,
    MIN_SLIDES_PER_LESSON,
    assert_meets_standard,
)
from grassmarket.workbench.content.sales_egoist import SALES_EGOIST_SLUG, sales_egoist_course
from grassmarket.workbench.content.sales_egoist_slides import (
    CURRICULUM,
    DECK_01,
    DECK_02,
    SECTIONS_AUTHORED,
    SECTIONS_PLANNED,
    rebuilt_sections,
)

COURSE = sales_egoist_course()
ALL_SLIDES = [s for m in COURSE.modules for lesson in m.lessons for s in lesson.slides]
ALL_TEXT = " ".join(f"{s.title} {s.body}" for s in ALL_SLIDES).lower()


class TestTheDepthStandard:
    def test_the_course_meets_the_standard(self) -> None:
        assert_meets_standard(SALES_EGOIST_SLUG, COURSE)

    def test_eight_sections_each_with_one_lesson_and_a_test(self) -> None:
        assert len(COURSE.modules) == 8
        for module in COURSE.modules:
            assert len(module.lessons) == 1, f"{module.title} is not a single lesson"
            assert module.section_test is not None, f"{module.title} has no section test"

    @pytest.mark.parametrize("module", COURSE.modules, ids=lambda m: m.title[:30])
    def test_every_lesson_is_a_deck(self, module) -> None:  # noqa: ANN001 - pytest param
        count = len(module.lessons[0].slides)
        assert MIN_SLIDES_PER_LESSON <= count <= MAX_SLIDES_PER_LESSON

    def test_nothing_is_still_planned(self) -> None:
        assert SECTIONS_PLANNED == ()
        assert len(SECTIONS_AUTHORED) == len(rebuilt_sections()) == 8

    def test_the_course_has_left_the_legacy_register(self) -> None:
        """GRS-0218 was the last entry. The register stays; the debt does not."""
        assert SALES_EGOIST_SLUG not in LEGACY_COURSES


class TestSourceAttribution:
    """The ticket's second test: every lesson cites committed material, so the "generic summary"
    failure is caught by the build rather than by the founder."""

    def test_every_lesson_cites_the_committed_source(self) -> None:
        for module in COURSE.modules:
            refs = module.lessons[0].references
            assert refs, f"{module.title} cites nothing"
            assert any(r.url.endswith((".docx", ".pptx")) for r in refs), (
                f"{module.title} cites no committed source file"
            )

    def test_every_citation_points_at_the_repository(self) -> None:
        """Not at a summary, a blog post, or a vendor page. The material is in `data/reference/`
        and the link resolves to the exact committed artefact each lesson was written from."""
        for ref in (CURRICULUM, DECK_01, DECK_02):
            assert "/data/reference/sales-egoist/" in ref.url

    def test_the_decks_are_cited_where_their_content_is_used(self) -> None:
        """Lesson 01 and 02 of the authored decks cover convictions I and II, so their slides are
        where the deck citations belong. A citation on a section the deck says nothing about would
        be decoration."""
        by_key = {m.id: m for m in COURSE.modules}
        deck_sections = [
            m
            for m in by_key.values()
            if any(r in (DECK_01, DECK_02) for r in m.lessons[0].references)
        ]
        titles = " ".join(m.title for m in deck_sections)
        assert "Convictions I and II" in titles


class TestTheMaterialIsDevelopedNotCompressed:
    """The claims that make this the Sales Egoist course rather than a sales course. Each is in the
    committed curriculum and each is specific enough that a generic summary would have dropped it —
    which is exactly what happened the first time."""

    @pytest.mark.parametrize(
        "phrase",
        [
            "self-authorship",  # the meaning of "egoist", section 1
            "placeholder",  # the doctrine's central figure
            "three to five years",  # the cost of a competitor's win
            "11 october 2027",  # the settlement deadline
            "december 2026",  # the T+0 confirmations milestone
            "august 2026",  # EU AI Act obligations
            "swift institute",  # the source of the 80% cross-border estimate
            "fidelity gap",  # conviction II's failure mode
            "signature play",  # conviction III's five fields
            "blue sheet",  # conviction V's operating system
            "pre-emptive close",  # conviction VIII's reward
            "bruntsfield maxim",  # the closing
        ],
    )
    def test_a_load_bearing_claim_survived(self, phrase: str) -> None:
        assert phrase in ALL_TEXT, f"the course no longer contains {phrase!r}"

    def test_the_armoury_is_named_not_gestured_at(self) -> None:
        """Sixteen methodologies, by name. A course that says "use a sales methodology" has
        compressed the armoury back out of existence."""
        for name in (
            "spin",
            "solution selling",
            "gap selling",
            "challenger",
            "provocation",
            "command of the message",
            "mutual action plan",
            "meddic",
            "sandler",
            "miller heiman",
            "target account",
            "timing layer",
        ):
            assert name in ALL_TEXT, f"the armoury no longer names {name!r}"

    def test_the_capital_markets_units_are_present(self) -> None:
        """A business case in the buyer's own units is conviction III's 'insight' variable. These
        four are the vocabulary the curriculum names."""
        for unit in ("basis points", "funding drag", "csdr", "exception management"):
            assert unit in ALL_TEXT

    def test_the_doctrine_keeps_its_own_vocabulary(self) -> None:
        """A deliberate decision, recorded in the module docstring: this is internal training in
        the founder's voice. GRS-0148 finding 4 asks whether the naming survives on CLIENT-adjacent
        surfaces, which is founder decision D5b and not this course's call."""
        assert "zero-sum" in ALL_TEXT
        assert "weapon" in ALL_TEXT

    def test_the_assessment_is_placed_in_the_campaign(self) -> None:
        """Ticket scope item 3: how the framing maps onto an ATLAS engagement. Section 8 has to do
        this concretely — the three jobs — rather than gesture at 'synergies'."""
        final = COURSE.modules[-1]
        text = " ".join(f"{s.title} {s.body}" for s in final.lessons[0].slides).lower()
        assert "platform power assessment" in text
        assert "committee" in text
        assert "mutual action plan" in text


class TestThePracticeIsReal:
    def test_every_section_ends_in_a_test_that_teaches(self) -> None:
        """A test that only says 'wrong' teaches nothing, and this gate exists to teach rather than
        to filter — so every question carries an explanation with substance in it."""
        for module in COURSE.modules:
            for question in module.section_test.questions:
                assert len(question.explanation) > 80, (
                    f"{module.title}: {question.prompt[:40]!r} has a thin explanation"
                )

    def test_wrong_options_are_plausible(self) -> None:
        """Every question offers four options, and none is given away by its shape.

        The property tested is length symmetry rather than an absolute floor. Some questions are
        legitimately answered by a date or a job title — "11 October 2027", "The CRO" — and there a
        20-character minimum would be measuring the wrong thing. What actually gives an answer away
        is one option being conspicuously longer or shorter than its siblings, which is the tell a
        learner uses to pass by elimination without knowing the material.
        """
        for module in COURSE.modules:
            for question in module.section_test.questions:
                assert len(question.options) == 4
                lengths = [len(o) for o in question.options]
                assert min(lengths) >= 7
                assert min(lengths) / max(lengths) >= 0.25, (
                    f"{module.title}: {question.prompt[:40]!r} has an option whose length "
                    f"gives it away ({lengths})"
                )

    def test_the_checkpoints_produce_artefacts(self) -> None:
        """The measurement on each lesson names something the advisor HOLDS afterwards. This is the
        difference between a course you have read and a course you have done."""
        for module in COURSE.modules:
            lesson = module.lessons[0]
            assert lesson.measurement
            checkpoints = [s for s in lesson.slides if s.kind is SlideKind.CHECKPOINT]
            assert checkpoints, f"{module.title} asks the advisor to produce nothing"
            for slide in checkpoints:
                assert slide.checkpoint_prompt

    def test_the_campaign_section_ends_with_a_diarised_action(self) -> None:
        """The doctrine reduces to 'stop waiting', so the last checkpoint of the last section is a
        date in a calendar rather than a reflection."""
        last = COURSE.modules[-1].lessons[0].slides[-1]
        assert last.kind is SlideKind.CHECKPOINT
        assert "diarise" in (last.checkpoint_prompt or "").lower()


class TestTheCourseIsStillTheFrontDoor:
    def test_it_stays_mandatory_first(self) -> None:
        """GRS-0239 scope 5 proposed moving `mandatory_first` off this course because 'Start here'
        pointed at the worst content we had. GRS-0218 fixes the cause instead, so the flag stays."""
        assert COURSE.mandatory_first is True

    def test_it_still_carries_no_certification_credit_by_itself(self) -> None:
        assert COURSE.certification_credit.value == "none"
