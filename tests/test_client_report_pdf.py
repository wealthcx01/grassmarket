"""The client report as a branded PDF (GRS-0219).

The founder said the deliverable preview "has no branding". Branding is hard to assert — "looks like
something Bruntsfield would put its name on" is not a unit test. So what is tested here is the set
of properties that make that judgement possible, and the ones where being wrong is dangerous:

* the structure and prose survive the render (golden master on extracted text),
* the house fonts are actually EMBEDDED rather than silently substituted,
* a draft or non-production record is watermarked — the failure that must never ship,
* the figures stay legible without colour, asserted on the generated image rather than by eye.
"""

from __future__ import annotations

import io
import random
import re
from datetime import date
from pathlib import Path
from uuid import UUID

import pypdf
import pytest
from bcap_contracts.client_report import (
    SECTION_ORDER,
    ClientReport,
    ReportSectionKind,
    coefficient_status_sentence,
)
from bcap_contracts.deliverables import DeliverableMode
from bcap_contracts.registry import load_registry
from PIL import Image

from grassmarket.atlas import score
from grassmarket.atlas.draft_coefficients import draft_v1_coefficient_set
from grassmarket.atlas.montecarlo import draft_v1_uncertainty_model, run_monte_carlo
from grassmarket.deliverables.builder import DeliverableContext
from grassmarket.deliverables.client_report import SectionProse, build_client_report
from grassmarket.deliverables.gate import DRAFT_WATERMARK
from grassmarket.deliverables.report_figures import ReportFigureData, figure_data_from_context
from grassmarket.deliverables.report_pdf import ReportMeta, render_client_report_pdf
from grassmarket.deliverables.report_pdf import figures as figs
from grassmarket.deliverables.report_pdf import tokens as tk
from tests._atlas_inputs import meridian_inputs

_REGISTRY = load_registry()
_MODEL = draft_v1_uncertainty_model()
RUN_ID = UUID("11111111-2222-3333-4444-555555555555")
FIXTURE = Path(__file__).parent / "fixtures" / "client_report_pdf_text.txt"

# Prose fixed here rather than generated, so the golden master tests the RENDER and not a drafter.
_PROSE: dict[ReportSectionKind, tuple[str, tuple[str, ...]]] = {
    ReportSectionKind.BUSINESS: (
        "The business",
        (
            "Meridian runs a regulated brokerage and the settlement rails beneath it. It earns "
            "from "
            "trading commissions, from financing client balances, and from selling access to its "
            "own execution venue.",
        ),
    ),
    ReportSectionKind.ADVANTAGE: (
        "Where the advantage sits",
        (
            "Read through the 7 Powers, the durable position here is switching costs: client "
            "balances are slow to move and slower to re-onboard.",
        ),
    ),
    ReportSectionKind.CONSTRAINT: (
        "What is holding it back",
        ("The binding constraint is operational rather than commercial.",),
    ),
    ReportSectionKind.ACTIONS: (
        "What to do about it",
        ("Close the operational gap first; it gates everything else on this list.",),
    ),
    ReportSectionKind.VALUE: (
        "What that is worth",
        ("Acting in that order is what moves the score, and the ordering matters more than pace.",),
    ),
    ReportSectionKind.APPENDIX: (
        "Technical appendix",
        (
            "Uncertainty is modelled as a P10/P50/P90 band around the deterministic point "
            "estimate. "
            "Where inputs carried no confidence grade the band is reported as an unmodelled point.",
        ),
    ),
}


@pytest.fixture(scope="module")
def context() -> DeliverableContext:
    coefficients = draft_v1_coefficient_set(_REGISTRY)
    inputs = meridian_inputs()
    return DeliverableContext(
        subject="Deutsche Börse",
        result=score(inputs, coefficients, _REGISTRY),
        uncertainty=run_monte_carlo(
            inputs, coefficients, _REGISTRY, _MODEL, random.Random(20260730)
        ),
        coefficients=coefficients,
        uncertainty_version=_MODEL.version,
        generated_on=date(2026, 7, 30),
    )


@pytest.fixture(scope="module")
def report(context: DeliverableContext) -> ClientReport:
    prose = {
        kind: SectionProse(heading=heading, body=body) for kind, (heading, body) in _PROSE.items()
    }
    return build_client_report(context, scoring_run_id=RUN_ID, prose=prose)


@pytest.fixture(scope="module")
def figure_data(context: DeliverableContext) -> ReportFigureData:
    return figure_data_from_context(context)


def _meta(**overrides: object) -> ReportMeta:
    defaults: dict[str, object] = {
        "engagement_title": "Q3 platform review",
        "prepared_by": "J. Gallagher",
        "generated_on": date(2026, 7, 30),
        "mode": DeliverableMode.CLIENT,
    }
    defaults.update(overrides)
    return ReportMeta(**defaults)  # type: ignore[arg-type]


def _text(pdf: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(pdf))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _normalise(text: str) -> str:
    """Extraction inserts soft line breaks at layout boundaries; the words are the contract."""
    return re.sub(r"\s+", " ", text).strip()


class TestTheDocumentItProduces:
    def test_it_renders_a_multi_page_pdf(
        self, report: ClientReport, figure_data: ReportFigureData
    ) -> None:
        pdf = render_client_report_pdf(report, meta=_meta(), figure_data=figure_data)
        assert pdf.startswith(b"%PDF-")
        reader = pypdf.PdfReader(io.BytesIO(pdf))
        assert len(reader.pages) >= 3

    def test_the_cover_carries_the_client_and_the_mark(
        self, report: ClientReport, figure_data: ReportFigureData
    ) -> None:
        pdf = render_client_report_pdf(report, meta=_meta(), figure_data=figure_data)
        cover = _normalise(pypdf.PdfReader(io.BytesIO(pdf)).pages[0].extract_text() or "")
        assert "BRUNTSFIELD" in cover
        assert "Deutsche Börse" in cover  # a real cover, not a heading on page one
        # GRS-0234 scope 2: the engagement title no longer prints on the cover. It was an internal
        # filing key ("WeBull — delivery") under an otherwise good cover, and the two lines above it
        # already say who the client is and what the document is.
        assert "Q3 platform review" not in cover
        assert "30 July 2026" in cover

    def test_every_section_reaches_the_page_in_order(
        self, report: ClientReport, figure_data: ReportFigureData
    ) -> None:
        from grassmarket.deliverables.report_pdf import SECTION_TITLES

        body = _normalise(
            _text(render_client_report_pdf(report, meta=_meta(), figure_data=figure_data))
        )
        positions = [body.index(SECTION_TITLES[kind]) for kind in SECTION_ORDER]
        assert positions == sorted(positions), (
            "sections did not render in the content model's order"
        )

    def test_the_provenance_footer_names_the_versions(
        self, report: ClientReport, figure_data: ReportFigureData
    ) -> None:
        body = _normalise(
            _text(render_client_report_pdf(report, meta=_meta(), figure_data=figure_data))
        )
        assert "Confidential" in body
        assert f"methodology {report.methodology_version}" in body
        # GRS-0234 scope 3: the footer says what the coefficient status MEANS. The identifier keeps
        # its place in the appendix's version table, where identifiers belong.
        assert (
            coefficient_status_sentence(version=report.coefficient_version, client_usable=False)
            in body
        )
        # The identifier itself is NOT banned from the document — the ticket puts it in the
        # appendix's version table, "where identifiers belong". What it must no longer do is print
        # on every page. So: it appears, and it appears once, rather than once per footer.
        assert body.count(report.coefficient_version) == 1, (
            "the config identifier should appear only in the appendix version table, "
            "not in the footer of every page"
        )

    def test_the_running_head_names_the_section_the_page_opens_in(
        self, report: ClientReport, figure_data: ReportFigureData
    ) -> None:
        # Regression: a single-pass build named the section the page ENDED in, so page two opened
        # with "The business" beneath a head reading "What is holding it back".
        pdf = render_client_report_pdf(report, meta=_meta(), figure_data=figure_data)
        reader = pypdf.PdfReader(io.BytesIO(pdf))
        first_body_page = _normalise(reader.pages[1].extract_text() or "")
        head, _, rest = first_body_page.partition("Confidential")
        assert "The business" in head, f"running head did not name the opening section: {head!r}"
        assert rest  # the footer is present too


class TestTheContentsPage:
    """Scope item 3. It was DECLARED as a token and never built — `CONTENTS_THRESHOLD_PAGES` sat in
    tokens.py looking like an implementation while the renderer ignored it, and the ticket claimed
    all six scope items were done. These tests are what makes the claim true."""

    def test_a_short_report_gets_no_contents_page(
        self, report: ClientReport, figure_data: ReportFigureData
    ) -> None:
        # Below the threshold a contents page is furniture for its own sake.
        pdf = render_client_report_pdf(report, meta=_meta(), figure_data=figure_data)
        reader = pypdf.PdfReader(io.BytesIO(pdf))
        assert len(reader.pages) <= tk.CONTENTS_THRESHOLD_PAGES
        assert "Contents" not in _normalise(_text(pdf))

    def _long_report(self, report: ClientReport) -> ClientReport:
        """The same report with enough prose to cross the threshold."""
        filler = ["A paragraph of a consultant's assessment prose, carrying no figures."] * 22
        return report.model_copy(
            update={
                "sections": [
                    s.model_copy(update={"body": [*s.body, *filler]}) for s in report.sections
                ]
            }
        )

    def test_a_long_report_gets_a_contents_page(
        self, report: ClientReport, figure_data: ReportFigureData
    ) -> None:
        pdf = render_client_report_pdf(
            self._long_report(report), meta=_meta(), figure_data=figure_data
        )
        reader = pypdf.PdfReader(io.BytesIO(pdf))
        assert len(reader.pages) > tk.CONTENTS_THRESHOLD_PAGES
        contents_page = _normalise(reader.pages[1].extract_text() or "")
        assert contents_page.startswith("Contents") or "Contents" in contents_page
        # It lists the sections a reader would look for.
        for title in ("The business", "What that is worth", "Technical appendix"):
            assert title in contents_page, f"contents omits {title!r}"

    def test_the_contents_page_numbers_point_at_the_right_pages(
        self, report: ClientReport, figure_data: ReportFigureData
    ) -> None:
        """The off-by-one nobody notices until a client follows it.

        Inserting the contents page pushes every body page down by one, so the numbers have to be
        recorded against the layout that HAS the contents page, not the one that does not.
        """
        pdf = render_client_report_pdf(
            self._long_report(report), meta=_meta(), figure_data=figure_data
        )
        reader = pypdf.PdfReader(io.BytesIO(pdf))
        contents = _normalise(reader.pages[1].extract_text() or "")

        match = re.search(r"Technical appendix\s+(\d+)", contents)
        assert match, f"could not read the appendix's page number from: {contents[:200]}"
        claimed = int(match.group(1))

        actual = next(
            i + 1
            for i, page in enumerate(reader.pages)
            if "Technical appendix" in _normalise(page.extract_text() or "")
            and i > 1  # skip the contents page's own mention
        )
        assert claimed == actual, (
            f"contents says the appendix is on page {claimed}; it is on page {actual}"
        )


class TestGoldenMaster:
    def test_the_extracted_text_matches_the_committed_fixture(
        self, report: ClientReport, figure_data: ReportFigureData
    ) -> None:
        """A prose or structure regression shows up as a diff in review, not before a client."""
        produced = _normalise(
            _text(render_client_report_pdf(report, meta=_meta(), figure_data=figure_data))
        )
        if not FIXTURE.exists():  # pragma: no cover - first run writes the master
            FIXTURE.parent.mkdir(parents=True, exist_ok=True)
            FIXTURE.write_text(produced, encoding="utf-8")
            pytest.fail(f"wrote a new golden master to {FIXTURE}; inspect it and re-run")
        assert produced == FIXTURE.read_text(encoding="utf-8")


class TestTheWatermarkCannotBeForgotten:
    """The worst failure this document can have is a draft escaping unmarked (ADR-0029)."""

    def test_a_draft_is_watermarked_on_every_page(
        self, report: ClientReport, figure_data: ReportFigureData
    ) -> None:
        pdf = render_client_report_pdf(
            report, meta=_meta(mode=DeliverableMode.DRAFT_INTERNAL), figure_data=figure_data
        )
        reader = pypdf.PdfReader(io.BytesIO(pdf))
        for index, page in enumerate(reader.pages):
            assert DRAFT_WATERMARK in _normalise(page.extract_text() or ""), (
                f"page {index + 1} of a draft carries no watermark"
            )

    def test_a_non_production_record_is_marked_too(
        self, report: ClientReport, figure_data: ReportFigureData
    ) -> None:
        pdf = render_client_report_pdf(
            report, meta=_meta(non_production=True), figure_data=figure_data
        )
        assert "NON-PRODUCTION DATA" in _normalise(_text(pdf))

    def test_a_clean_client_document_carries_no_mark(
        self, report: ClientReport, figure_data: ReportFigureData
    ) -> None:
        body = _normalise(
            _text(render_client_report_pdf(report, meta=_meta(), figure_data=figure_data))
        )
        assert DRAFT_WATERMARK not in body
        assert "NON-PRODUCTION" not in body


class TestTheHouseTypographyIsReallyThere:
    def test_the_fonts_are_embedded_not_substituted(
        self, report: ClientReport, figure_data: ReportFigureData
    ) -> None:
        # reportlab substitutes Helvetica silently when a face is missing, which would lose the
        # house typography without failing anything. Assert the real faces are in the file.
        pdf = render_client_report_pdf(report, meta=_meta(), figure_data=figure_data)
        blob = pdf.decode("latin-1")
        for family in ("SourceSerif4", "Inter", "IBMPlexMono"):
            assert family in blob, f"{family} was not embedded in the PDF"

    def test_a_missing_face_refuses_rather_than_substitutes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(tk, "_FONT_DIR", Path("/nonexistent/fonts"))
        monkeypatch.setattr(tk.pdfmetrics, "getRegisteredFontNames", lambda: [])
        with pytest.raises(tk.MissingReportFontError, match="vendor_report_fonts"):
            tk.register_fonts()

    def test_non_ascii_client_names_survive(
        self, report: ClientReport, figure_data: ReportFigureData
    ) -> None:
        # The vendored faces are full Unicode, not the ASCII subset used for motion work — a
        # missing glyph renders blank and silently, so the ö is asserted rather than assumed.
        cover = _normalise(
            pypdf.PdfReader(
                io.BytesIO(render_client_report_pdf(report, meta=_meta(), figure_data=figure_data))
            )
            .pages[0]
            .extract_text()
            or ""
        )
        assert "Börse" in cover


class TestFiguresSurviveAPrintout:
    """Scope item 4: "a chart that only works in colour is a chart that fails in a boardroom
    printout" — asserted on the generated image, not by eye."""

    def test_the_palette_separates_in_luminance(self) -> None:
        palette = figs.GREYSCALE_PALETTE
        luminances = [figs.relative_luminance(colour) for colour in palette]
        for i in range(len(luminances) - 1):
            gap = abs(luminances[i] - luminances[i + 1])
            assert gap >= figs.MIN_LUMINANCE_SEPARATION, (
                f"{palette[i]} and {palette[i + 1]} are {gap:.3f} apart in luminance — "
                "two adjacent fills a printer would render as the same grey"
            )

    def test_every_series_also_carries_a_hatch(self) -> None:
        # Luminance alone fails a photocopier that flattens greys; hatch is the second channel.
        assert len(figs.HATCHES) >= len(figs.GREYSCALE_PALETTE)
        assert len({h for h in figs.HATCHES}) == len(figs.HATCHES)

    def test_the_rendered_buildup_keeps_distinct_greys(self, figure_data: ReportFigureData) -> None:
        png = figs.value_buildup(
            labels=list(figure_data.value_buildup.labels),
            values=list(figure_data.value_buildup.values),
        )
        grey = Image.open(io.BytesIO(png)).convert("L")
        histogram = grey.histogram()
        # Ink levels that occupy a meaningful area — bar fills, not antialiasing fringe.
        ink_levels = [
            level for level, count in enumerate(histogram) if count > 4000 and level < 235
        ]
        assert len(ink_levels) >= 3, (
            f"only {len(ink_levels)} distinct ink levels in greyscale — the bars have collapsed"
        )

    def test_the_figures_render_at_print_resolution(self, figure_data: ReportFigureData) -> None:
        assert figs.PRINT_DPI >= 300
        png = figs.module_breakdown(
            labels=list(figure_data.module_breakdown.labels),
            values=list(figure_data.module_breakdown.values),
        )
        width, _ = Image.open(io.BytesIO(png)).size
        assert width > 1500, "figure is not at print resolution"

    def test_an_unassessed_module_is_never_plotted_as_zero(
        self, context: DeliverableContext, figure_data: ReportFigureData
    ) -> None:
        assessed = {m.name for m in context.result.modules if m.q_m is not None}
        assert set(figure_data.maturity.labels) == assessed
        assert all(value > 0 for value in figure_data.maturity.values)
