"""Client report content model (GRS-0211) — the four rules the old preview broke.

The founder's verdict on the deliverable preview was "It is terrible. It is so complicated, doesn't
read well at all and has no branding." Branding belongs to the renditions (GRS-0219/0220). What is
tested here is the part that made it unreadable: the report was a scorecard, the maths was in the
reader's face, and its numbers were untraceable.

Each rule is enforced by the model itself rather than by a renderer, so neither rendition can opt
out of it.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from bcap_contracts.client_report import (
    SECTION_ORDER,
    ClientReport,
    DeclaredFigure,
    ReportSection,
    ReportSectionKind,
    ReportTier,
    UnapprovedReportSectionError,
    assert_client_ready,
    undeclared_figure_message,
)
from pydantic import ValidationError

RUN_ID = uuid4()


def _section(kind: ReportSectionKind, **overrides: object) -> ReportSection:
    """A minimal valid section, so each test varies exactly one thing."""
    defaults: dict[str, object] = {
        "kind": kind,
        "heading": f"{kind.value.title()}",
        "body": ["Plain prose with no numbers in it."],
    }
    defaults.update(overrides)
    return ReportSection(**defaults)  # type: ignore[arg-type]


def _report(**overrides: object) -> ClientReport:
    defaults: dict[str, object] = {
        "subject": "Deutsche Börse",
        "scoring_run_id": RUN_ID,
        "methodology_version": "1.6",
        "coefficient_version": "v1-elicited",
        "sections": [_section(k) for k in SECTION_ORDER],
    }
    defaults.update(overrides)
    return ClientReport(**defaults)  # type: ignore[arg-type]


class TestOrderIsTheReport:
    """Rule 1. The order is what makes it a story about a business rather than a scorecard."""

    def test_the_canonical_report_validates(self) -> None:
        report = _report()
        assert [s.kind for s in report.sections] == list(SECTION_ORDER)

    def test_the_business_comes_before_the_score(self) -> None:
        # The specific complaint: the old preview led with numbers.
        assert SECTION_ORDER[0] is ReportSectionKind.BUSINESS
        assert SECTION_ORDER[-1] is ReportSectionKind.APPENDIX

    def test_a_missing_section_is_refused(self) -> None:
        sections = [_section(k) for k in SECTION_ORDER if k is not ReportSectionKind.CONSTRAINT]
        with pytest.raises(ValidationError, match="missing section"):
            _report(sections=sections)

    def test_out_of_order_sections_are_refused(self) -> None:
        sections = [_section(k) for k in SECTION_ORDER]
        sections[0], sections[1] = sections[1], sections[0]
        with pytest.raises(ValidationError, match="out of order"):
            _report(sections=sections)

    def test_a_repeated_section_is_refused(self) -> None:
        sections = [_section(k) for k in SECTION_ORDER] + [_section(ReportSectionKind.VALUE)]
        with pytest.raises(ValidationError, match="repeats section"):
            _report(sections=sections)


class TestTheMathsStaysOutOfTheWay:
    """Rule 2. 'The maths disambiguated away from the reader on both sides.'"""

    @pytest.mark.parametrize("token", ["P10", "P50", "P90"])
    def test_uncertainty_terms_are_refused_in_the_body(self, token: str) -> None:
        with pytest.raises(ValidationError, match="belong in the appendix"):
            _section(
                ReportSectionKind.VALUE,
                body=[f"The {token} outcome is the one to plan against."],
            )

    def test_the_appendix_may_use_them(self) -> None:
        section = _section(
            ReportSectionKind.APPENDIX,
            body=["Uncertainty is reported as P10/P50/P90 from the Monte Carlo run."],
        )
        assert "P10" in section.body[0]

    def test_the_plain_english_phrasing_passes(self) -> None:
        # What the body is supposed to say instead.
        section = _section(
            ReportSectionKind.VALUE,
            body=[
                "Our central estimate is £4.2m, and on the evidence we have it could reasonably "
                "be between £2.8m and £6.1m."
            ],
            figures=[
                DeclaredFigure(
                    key="central",
                    label="Central estimate",
                    rendered="£4.2m",
                    source="run.value.point",
                ),
                DeclaredFigure(
                    key="low", label="Lower bound", rendered="£2.8m", source="run.value.low"
                ),
                DeclaredFigure(
                    key="high", label="Upper bound", rendered="£6.1m", source="run.value.high"
                ),
            ],
        )
        assert len(section.figures) == 3


class TestEveryFigureIsDeclared:
    """Rule 3. An undeclared number is a build failure, not a proofreading problem."""

    def test_an_undeclared_number_is_refused(self) -> None:
        # GRS-0230 rewrote this refusal into the product voice; the RULE is unchanged, so the
        # match moved to the sentence a reader now sees rather than the old internal one.
        with pytest.raises(ValidationError, match="not among the figures"):
            _section(
                ReportSectionKind.CONSTRAINT,
                body=["Coverage reached 61% before the assessment was finalised."],
            )

    def test_a_declared_number_passes(self) -> None:
        section = _section(
            ReportSectionKind.CONSTRAINT,
            body=["Coverage reached 61% before the assessment was finalised."],
            figures=[
                DeclaredFigure(
                    key="coverage", label="Coverage", rendered="61%", source="run.coverage"
                ),
            ],
        )
        assert section.figures[0].source == "run.coverage"

    def test_the_framework_s_own_name_is_not_a_measurement(self) -> None:
        # "7 Powers" names the framework; it is not a claim about this firm, so it needs no
        # declaration. Anything else with a digit in it still does.
        section = _section(
            ReportSectionKind.ADVANTAGE,
            body=["Read through the 7 Powers, only Scale Economies applies here."],
        )
        assert section.figures == []

    def test_prose_with_no_numbers_needs_no_figures(self) -> None:
        assert _section(ReportSectionKind.BUSINESS).figures == []

    def test_a_number_the_section_did_not_declare_is_caught_even_beside_declared_ones(self) -> None:
        # The dangerous case: a section that declares SOME of its numbers looks diligent.
        with pytest.raises(ValidationError, match=r"88"):
            _section(
                ReportSectionKind.VALUE,
                body=["Value builds to £4.2m, against a benchmark of 88."],
                figures=[
                    DeclaredFigure(key="v", label="Value", rendered="£4.2m", source="run.value"),
                ],
            )

    def test_duplicate_figure_keys_are_refused(self) -> None:
        with pytest.raises(ValidationError, match="same figure key twice"):
            _section(
                ReportSectionKind.VALUE,
                body=["Plain prose."],
                figures=[
                    DeclaredFigure(key="v", label="A", rendered="1", source="run.a"),
                    DeclaredFigure(key="v", label="B", rendered="2", source="run.b"),
                ],
            )


class TestNothingUnapprovedReachesAClient:
    """Rule 4 — non-negotiable #8, as a runtime guarantee rather than a convention."""

    def test_an_ai_drafted_section_must_name_its_narrative(self) -> None:
        with pytest.raises(ValidationError, match="names no approved narrative"):
            _section(ReportSectionKind.BUSINESS, ai_drafted=True)

    def test_a_client_facing_report_refuses_an_unapproved_draft(self) -> None:
        narrative_id = uuid4()
        sections = [_section(k) for k in SECTION_ORDER]
        sections[0] = _section(
            ReportSectionKind.BUSINESS, ai_drafted=True, narrative_id=narrative_id
        )
        report = _report(sections=sections)
        with pytest.raises(UnapprovedReportSectionError, match="unapproved AI-drafted"):
            assert_client_ready(report, approved_narrative_ids=set())

    def test_an_approved_draft_passes(self) -> None:
        narrative_id = uuid4()
        sections = [_section(k) for k in SECTION_ORDER]
        sections[0] = _section(
            ReportSectionKind.BUSINESS, ai_drafted=True, narrative_id=narrative_id
        )
        report = _report(sections=sections)
        assert_client_ready(report, approved_narrative_ids={narrative_id})

    def test_human_written_prose_needs_no_approval_record(self) -> None:
        assert_client_ready(_report(), approved_narrative_ids=set())


class TestTiering:
    """The GRS-0214 hook: tiering is a property of the content, not a renderer's filter."""

    def test_free_tier_sees_only_free_sections(self) -> None:
        sections = [_section(k) for k in SECTION_ORDER]
        sections[0] = _section(ReportSectionKind.BUSINESS, tier=ReportTier.FREE)
        report = _report(sections=sections)
        assert [s.kind for s in report.for_tier(ReportTier.FREE)] == [ReportSectionKind.BUSINESS]
        assert len(report.for_tier(ReportTier.ENGAGED)) == len(SECTION_ORDER)

    def test_sections_are_engaged_by_default(self) -> None:
        # Defaulting to the paid tier means a new section cannot leak by omission.
        assert _section(ReportSectionKind.VALUE).tier is ReportTier.ENGAGED


class TestTheUndeclaredFigureMessage:
    """GRS-0230 scope 2. The refusal an advisor reads when a number is not in the run.

    What it replaced named the section by its internal key and the rule by its class name —
    `section 'value' states ['£3.4m'] ... must be a DeclaredFigure` — which is precisely the leak
    GRS-0163 existed to stop. It lives in ONE place because both the API and the editor show it, and
    a message authored in two places drifts (GRS-0228, red on main for nine days).
    """

    def test_it_names_the_section_a_reader_sees(self) -> None:
        message = undeclared_figure_message(ReportSectionKind.VALUE, ["£3.4m"])
        assert "What that is worth" in message
        assert "'value'" not in message

    def test_it_leaks_no_internal_vocabulary(self) -> None:
        message = undeclared_figure_message(ReportSectionKind.CONSTRAINT, ["12"])
        for leak in ("DeclaredFigure", "ReportSection", "[", "]", "kind="):
            assert leak not in message, f"the refusal leaks {leak!r} at an advisor"

    def test_it_says_what_to_do(self) -> None:
        # A refusal that only refuses is the dead end the ticket is about.
        message = undeclared_figure_message(ReportSectionKind.VALUE, ["£3.4m"])
        assert "Use one of the figures" in message
        assert "take the number out" in message

    def test_it_reads_naturally_for_one_number_and_for_several(self) -> None:
        one = undeclared_figure_message(ReportSectionKind.VALUE, ["£3.4m"])
        many = undeclared_figure_message(ReportSectionKind.VALUE, ["£3.4m", "12%"])
        assert "that number is not" in one
        assert "those numbers are not" in many

    def test_the_validator_uses_it(self) -> None:
        """The message and the gate cannot drift apart, because there is only one of it."""
        with pytest.raises(ValidationError) as exc:
            ReportSection(
                kind=ReportSectionKind.VALUE,
                heading="What that is worth",
                body=["The lever is worth £3.4m."],
                figures=(),
            )
        assert "What that is worth" in str(exc.value)
        assert "DeclaredFigure" not in str(exc.value)
