"""Building the client report from a finalised run (GRS-0211).

The model tests (`test_client_report_model.py`) prove the four rules. These prove the builder
honours them against a REAL scored run, and — the part that matters most — that it never
invents anything: prose is an input, an unmodelled band declares no range, and an unassessed
module is absent rather than zero.
"""

from __future__ import annotations

import random
from datetime import date
from uuid import uuid4

import pytest
from bcap_contracts.client_report import (
    SECTION_ORDER,
    DeclaredFigure,
    ReportSectionKind,
    ReportTier,
)
from bcap_contracts.registry import load_registry
from pydantic import ValidationError

from grassmarket.atlas import score
from grassmarket.atlas.draft_coefficients import draft_v1_coefficient_set
from grassmarket.atlas.montecarlo import draft_v1_uncertainty_model, run_monte_carlo
from grassmarket.deliverables.builder import DeliverableContext
from grassmarket.deliverables.client_report import (
    MissingReportProseError,
    SectionProse,
    build_client_report,
)
from tests._atlas_inputs import meridian_inputs

_REGISTRY = load_registry()
_MODEL = draft_v1_uncertainty_model()
RUN_ID = uuid4()


@pytest.fixture(scope="module")
def context() -> DeliverableContext:
    """The ratified Meridian golden-master run, scored deterministically and reused across tests.

    Deliberately the golden master: if the report ever starts citing numbers that are not the ones
    the engine produces for this assessment, these tests fail alongside the engine's own.
    """
    coefficients = draft_v1_coefficient_set(_REGISTRY)
    inputs = meridian_inputs()
    return DeliverableContext(
        subject="Meridian Securities",
        result=score(inputs, coefficients, _REGISTRY),
        uncertainty=run_monte_carlo(
            inputs, coefficients, _REGISTRY, _MODEL, random.Random(20260730)
        ),
        coefficients=coefficients,
        uncertainty_version=_MODEL.version,
        generated_on=date(2026, 7, 30),
    )


def _prose(**overrides: SectionProse) -> dict[ReportSectionKind, SectionProse]:
    """Human prose for every section — deliberately free of numbers, so each test adds its own."""
    base = {
        kind: SectionProse(
            heading=kind.value.title(),
            body=("Prose written by a consultant, with no numbers in it.",),
        )
        for kind in SECTION_ORDER
    }
    base.update({ReportSectionKind[k.upper()]: v for k, v in overrides.items()})
    return base


class TestItRefusesRatherThanFabricates:
    def test_a_section_without_prose_is_refused(self, context: DeliverableContext) -> None:
        prose = _prose()
        del prose[ReportSectionKind.BUSINESS]
        with pytest.raises(MissingReportProseError, match="business"):
            build_client_report(context, scoring_run_id=RUN_ID, prose=prose)

    def test_the_error_names_every_missing_section_at_once(
        self, context: DeliverableContext
    ) -> None:
        prose = _prose()
        del prose[ReportSectionKind.BUSINESS]
        del prose[ReportSectionKind.VALUE]
        with pytest.raises(MissingReportProseError) as excinfo:
            build_client_report(context, scoring_run_id=RUN_ID, prose=prose)
        assert "business" in str(excinfo.value) and "value" in str(excinfo.value)


class TestTheReportItBuilds:
    def test_it_produces_every_section_in_order(self, context: DeliverableContext) -> None:
        report = build_client_report(context, scoring_run_id=RUN_ID, prose=_prose())
        assert [s.kind for s in report.sections] == list(SECTION_ORDER)

    def test_it_is_bound_to_the_run_and_its_versions(self, context: DeliverableContext) -> None:
        report = build_client_report(context, scoring_run_id=RUN_ID, prose=_prose())
        assert report.scoring_run_id == RUN_ID
        assert report.methodology_version == context.result.methodology_version
        assert report.coefficient_version == context.result.coefficient_version

    def test_the_business_section_carries_no_figures(self, context: DeliverableContext) -> None:
        # The report opens with the business. No score appears there — that ordering is the point.
        report = build_client_report(context, scoring_run_id=RUN_ID, prose=_prose())
        assert report.section(ReportSectionKind.BUSINESS).figures == []

    def test_the_value_section_declares_the_headline_score(
        self, context: DeliverableContext
    ) -> None:
        report = build_client_report(context, scoring_run_id=RUN_ID, prose=_prose())
        value = report.section(ReportSectionKind.VALUE)
        headline = next(f for f in value.figures if f.key == "platform_value")
        assert headline.rendered == f"{context.result.v_display_0_100:.0f}"
        assert headline.source == "run.v_display_0_100"

    def test_every_declared_figure_names_where_it_came_from(
        self, context: DeliverableContext
    ) -> None:
        report = build_client_report(context, scoring_run_id=RUN_ID, prose=_prose())
        for section in report.sections:
            for figure in section.figures:
                assert figure.source.startswith("run."), (
                    f"{section.kind}/{figure.key} cites '{figure.source}', which is not a run field"
                )


class TestProseIsCheckedAgainstTheRun:
    def test_prose_may_quote_a_figure_the_run_supplied(self, context: DeliverableContext) -> None:
        score = f"{context.result.v_display_0_100:.0f}"
        report = build_client_report(
            context,
            scoring_run_id=RUN_ID,
            prose=_prose(
                value=SectionProse(
                    heading="What acting is worth",
                    body=(f"Platform Value stands at {score} today.",),
                )
            ),
        )
        assert score in report.section(ReportSectionKind.VALUE).body[0]

    def test_prose_quoting_a_number_the_run_never_produced_is_refused(
        self, context: DeliverableContext
    ) -> None:
        # The failure this whole mechanism exists for: a plausible number nobody can trace.
        # GRS-0230 rewrote the refusal into the product voice. The RULE is unchanged; the
        # match moved to the sentence an advisor now reads.
        with pytest.raises(ValidationError, match="not among the figures"):
            build_client_report(
                context,
                scoring_run_id=RUN_ID,
                prose=_prose(
                    value=SectionProse(
                        heading="What acting is worth",
                        body=("Acting on this is worth £4,200,000 over three years.",),
                    )
                ),
            )

    def test_client_supplied_context_can_be_declared_explicitly(
        self, context: DeliverableContext
    ) -> None:
        # Not every number in a report comes off the run — but it still has to be declared.
        report = build_client_report(
            context,
            scoring_run_id=RUN_ID,
            prose=_prose(
                business=SectionProse(
                    heading="The business",
                    body=("Meridian runs 240 people across three desks.",),
                    extra_figures=(
                        DeclaredFigure(
                            key="headcount",
                            label="Headcount",
                            rendered="240",
                            source="client.headcount (supplied at kickoff)",
                        ),
                    ),
                )
            ),
        )
        assert report.section(ReportSectionKind.BUSINESS).figures[0].key == "headcount"

    def test_the_body_may_not_talk_in_percentiles(self, context: DeliverableContext) -> None:
        with pytest.raises(ValidationError, match="belong in the appendix"):
            build_client_report(
                context,
                scoring_run_id=RUN_ID,
                prose=_prose(
                    value=SectionProse(
                        heading="What acting is worth",
                        body=("The P50 case is the one to plan against.",),
                    )
                ),
            )


class TestAbsenceIsNeverAZero:
    def test_an_unassessed_module_is_absent_from_the_appendix_not_zero(
        self, context: DeliverableContext
    ) -> None:
        report = build_client_report(context, scoring_run_id=RUN_ID, prose=_prose())
        appendix = report.section(ReportSectionKind.APPENDIX)
        declared_module_keys = {f.key for f in appendix.figures if f.key.startswith("module_")}
        unassessed = [m.key.lower() for m in context.result.modules if m.q_m is None]
        for key in unassessed:
            assert f"module_{key}" not in declared_module_keys, (
                f"module {key} has no assessed subcomponent but was declared anyway (defect D9)"
            )

    def test_an_unmodelled_band_declares_no_range(self, context: DeliverableContext) -> None:
        # ADR-0008: an unmodelled band is a point. Declaring a range would tell a client we have a
        # tight estimate when we have a single number.
        report = build_client_report(context, scoring_run_id=RUN_ID, prose=_prose())
        value = report.section(ReportSectionKind.VALUE)
        has_range = any(f.key == "value_low" for f in value.figures)
        assert has_range == context.uncertainty.v_band.modelled

    def test_a_declared_range_always_contains_the_headline_score(
        self, context: DeliverableContext
    ) -> None:
        report = build_client_report(context, scoring_run_id=RUN_ID, prose=_prose())
        value = report.section(ReportSectionKind.VALUE)
        figures = {f.key: f.rendered for f in value.figures}
        if "value_low" not in figures:
            pytest.skip("this run's V band is not modelled, so no range is declared")
        point = float(figures["platform_value"])
        assert float(figures["value_low"]) <= point <= float(figures["value_high"])


class TestTiering:
    def test_a_section_can_be_published_to_the_free_tier(self, context: DeliverableContext) -> None:
        report = build_client_report(
            context,
            scoring_run_id=RUN_ID,
            prose=_prose(
                business=SectionProse(
                    heading="The business",
                    body=("Prose with no numbers.",),
                    tier=ReportTier.FREE,
                )
            ),
        )
        assert [s.kind for s in report.for_tier(ReportTier.FREE)] == [ReportSectionKind.BUSINESS]
