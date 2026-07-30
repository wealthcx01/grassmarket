"""The course depth standard (GRS-0215).

The founder's complaint, twice: "The courses are so basic?! ... You have written theses as
'lessons'. Last time i checked a paragraph is not a lesson. A lesson is 20-40 slides of interactive
detail with a test before the next section."

GRS-0190 built a rich renderer and GRS-0191 wrote no content, so the product gained the capacity to
fix the complaint and none of the fix. The lesson from that is that "deep enough" cannot be a
matter of opinion held by whoever is authoring at the time. This module turns it into a check that
fails the build.

Applied to a course by `assert_meets_standard`. A course that has not been rebuilt yet is not
silently exempt — it is listed in `LEGACY_COURSES` with the ticket that will rebuild it, so the
exemption is a visible debt rather than an absence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from bcap_contracts.learning import CourseTree, SlideKind

# The founder's numbers, not invented ones.
MIN_SLIDES_PER_LESSON = 20
MAX_SLIDES_PER_LESSON = 40

# A lesson can hit 20 slides and still teach nothing if every slide is prose. At least this many
# must be something the advisor DOES: a walkthrough step, a worked example, or a checkpoint.
MIN_DOING_SLIDES_PER_LESSON = 5

# Every section ends in a test, and a one-question test is not a gate.
MIN_QUESTIONS_PER_SECTION_TEST = 5

# A slide with two sentences on it is the old failure at a smaller scale.
MIN_SLIDE_BODY_CHARS = 120

# The lesson's opening still has to say what the lesson is for.
MIN_LESSON_BODY_CHARS = 200

# At least one diagram per lesson (GRS-0225). The OpenBB rebuild passed every rule above with 196
# slides and not one drawing, which is how a course can meet a depth standard and still be a wall
# of text. Several of its ideas were spatial and written down as sentences anyway.
MIN_ASSETS_PER_LESSON = 1

# Alt text is required by the `LessonAsset` contract, but "diagram" satisfies min_length=1. A
# screen-reader user should get the content of the drawing, which takes a sentence at least.
MIN_ASSET_ALT_CHARS = 80

_DOING_KINDS = frozenset({SlideKind.WALKTHROUGH, SlideKind.EXAMPLE, SlideKind.CHECKPOINT})

# Courses that predate the standard, each with the ticket that rebuilds it. Listing them is the
# point: an exemption nobody can see is how the last rebuild quietly did not happen.
LEGACY_COURSES: dict[str, str] = {
    "product-benzinga": "GRS-0217",
    "product-brandfetch": "GRS-0217",
    "sales-egoist": "GRS-0218",
    "sales-ops-playbook": "GRS-0217",
}


@dataclass
class DepthReport:
    """What the standard found. Collects every failure rather than stopping at the first, so an
    author fixes a course in one pass instead of playing whack-a-mole with the test runner."""

    slug: str
    failures: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures

    def describe(self) -> str:
        if self.ok:
            return f"{self.slug}: meets the course depth standard."
        lines = "\n".join(f"  - {f}" for f in self.failures)
        return f"{self.slug} does not meet the course depth standard:\n{lines}"


def check_depth(slug: str, tree: CourseTree) -> DepthReport:
    """Measure one course against the standard. Never raises; `assert_meets_standard` does that."""
    report = DepthReport(slug=slug)

    if not tree.modules:
        report.failures.append("the course has no sections at all")
        return report

    for module in tree.modules:
        where = f"section {module.order + 1} ({module.title!r})"

        if not module.lessons:
            report.failures.append(f"{where} has no lessons")

        test = module.section_test
        if test is None:
            report.failures.append(
                f"{where} has no section test, so nothing stands between it and the next section"
            )
        elif len(test.questions) < MIN_QUESTIONS_PER_SECTION_TEST:
            report.failures.append(
                f"{where} test has {len(test.questions)} question(s); "
                f"{MIN_QUESTIONS_PER_SECTION_TEST} is the minimum for a gate to mean anything"
            )

        for lesson in module.lessons:
            _check_lesson(report, where, lesson)

    return report


def _check_lesson(report: DepthReport, where: str, lesson) -> None:
    label = f"{where}, lesson {lesson.title!r}"
    n = len(lesson.slides)

    if n < MIN_SLIDES_PER_LESSON:
        report.failures.append(
            f"{label} has {n} slide(s); the standard is {MIN_SLIDES_PER_LESSON}–"
            f"{MAX_SLIDES_PER_LESSON}. A paragraph is not a lesson."
        )
    elif n > MAX_SLIDES_PER_LESSON:
        report.failures.append(
            f"{label} has {n} slides, past the {MAX_SLIDES_PER_LESSON} ceiling — split it, because "
            f"a lesson nobody finishes teaches nothing either"
        )

    doing = sum(1 for s in lesson.slides if s.kind in _DOING_KINDS)
    if n and doing < MIN_DOING_SLIDES_PER_LESSON:
        report.failures.append(
            f"{label} has {doing} slide(s) the advisor does something on; "
            f"{MIN_DOING_SLIDES_PER_LESSON} is the minimum. Reading is not learning to sell."
        )

    if len((lesson.body or "").strip()) < MIN_LESSON_BODY_CHARS:
        report.failures.append(
            f"{label} opens with under {MIN_LESSON_BODY_CHARS} characters; say what the lesson is "
            f"for and what the advisor will be able to do at the end of it"
        )

    # Sources: on the lesson, or on its slides. Either satisfies "cite what you claim"; requiring
    # both would push authors toward a decorative lesson-level link.
    slide_refs = sum(len(s.references) for s in lesson.slides)
    if not lesson.references and not slide_refs:
        report.failures.append(
            f"{label} cites no source. If a claim has no source it does not go in the course."
        )

    for slide in lesson.slides:
        if len(slide.body.strip()) < MIN_SLIDE_BODY_CHARS:
            report.failures.append(
                f"{label}, slide {slide.order + 1} ({slide.title!r}) is under "
                f"{MIN_SLIDE_BODY_CHARS} characters"
            )

    # Diagrams live on slides; a lesson-level asset counts too, since GRS-0190 put them there first.
    assets = [s.asset for s in lesson.slides if s.asset] + list(lesson.assets)
    if n and len(assets) < MIN_ASSETS_PER_LESSON:
        report.failures.append(
            f"{label} has no diagram. At least {MIN_ASSETS_PER_LESSON} is the standard: if nothing "
            f"in the lesson is worth drawing, the lesson is probably explaining something spatial "
            f"in sentences. Author it in design/motion/courses/."
        )
    for asset in assets:
        if len(asset.alt.strip()) < MIN_ASSET_ALT_CHARS:
            report.failures.append(
                f"{label} has a diagram whose alt text is under {MIN_ASSET_ALT_CHARS} characters "
                f"({asset.caption!r}). Describe what the drawing shows, not that it is a drawing."
            )


def assert_meets_standard(slug: str, tree: CourseTree) -> None:
    """Raise unless the course meets the standard. The message names every failure."""
    report = check_depth(slug, tree)
    if not report.ok:
        raise AssertionError(report.describe())
