"""Render a `ClientReport` as a Bruntsfield-branded PDF (GRS-0219).

The founder's words were that the deliverable preview "has no branding". This module is the answer
to that half of the complaint: a cover, the house typefaces, page furniture, figures that survive a
printout, and a provenance footer. What the report *says* is GRS-0211's content model, which arrives
here already validated — this file never decides content, only how it looks.

The watermark rule (ADR-0029) is the one thing here that is a safety property rather than a design
one: a DRAFT_INTERNAL document is stamped on every page, because a draft escaping to a client
unmarked is the worst failure this document can have. It is drawn on the canvas beneath the content,
so no flowable can cover it and no caller can forget it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from io import BytesIO

from bcap_contracts.client_report import SECTION_TITLES as CONTRACT_SECTION_TITLES
from bcap_contracts.client_report import (
    ClientReport,
    ReportSection,
    ReportSectionKind,
    coefficient_status_sentence,
)
from bcap_contracts.deliverables import DeliverableMode
from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from grassmarket.deliverables.gate import DRAFT_WATERMARK
from grassmarket.deliverables.report_figures import ReportFigureData
from grassmarket.deliverables.report_pdf import figures as figs
from grassmarket.deliverables.report_pdf import tokens as tk

WORDMARK = "BRUNTSFIELD"
WORDMARK_SUB = "ADVISORY NETWORK"

#: Reader-facing section titles. The content model carries kinds; a client sees words.
# Re-exported from the contract, which is where the reader-facing names now live (GRS-0230). Kept
# as a module-level name so existing imports from here keep working.
SECTION_TITLES = CONTRACT_SECTION_TITLES


@dataclass(frozen=True)
class ReportMeta:
    """Everything on the cover and in the provenance footer that is not in the content model."""

    engagement_title: str
    prepared_by: str
    generated_on: date
    mode: DeliverableMode
    #: Stamped alongside the draft watermark when the underlying record is demo/sandbox data.
    non_production: bool = False
    #: Whether the coefficient set that priced this report is client-usable (GRS-0234 scope 3).
    #: Feeds the footer's plain-English provenance sentence; the identifier itself stays in the
    #: appendix's version table, where identifiers belong.
    coefficients_client_usable: bool = False


def _styles() -> dict[str, ParagraphStyle]:
    tk.register_fonts()
    body_size, body_lead = tk.BODY
    return {
        "cover_title": ParagraphStyle(
            "cover_title",
            fontName=tk.SERIF_BOLD,
            fontSize=tk.COVER_TITLE[0],
            leading=tk.COVER_TITLE[1],
            textColor=tk.INK,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            fontName=tk.SANS,
            fontSize=tk.COVER_SUBTITLE[0],
            leading=tk.COVER_SUBTITLE[1],
            textColor=tk.INK_SOFT,
        ),
        "section": ParagraphStyle(
            "section",
            fontName=tk.SERIF_BOLD,
            fontSize=tk.SECTION_TITLE[0],
            leading=tk.SECTION_TITLE[1],
            textColor=tk.INK,
            spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "body",
            fontName=tk.SERIF,
            fontSize=body_size,
            leading=body_lead,
            textColor=tk.INK,
            alignment=TA_LEFT,
            spaceAfter=tk.SPACE_PARA,
        ),
        "caption": ParagraphStyle(
            "caption",
            fontName=tk.SANS,
            fontSize=tk.CAPTION[0],
            leading=tk.CAPTION[1],
            textColor=tk.INK_MUTED,
            spaceAfter=4,
        ),
        "key": ParagraphStyle(
            "key",
            fontName=tk.MONO,
            fontSize=tk.FIGURE_KEY[0],
            leading=tk.FIGURE_KEY[1],
            textColor=tk.INK_SOFT,
        ),
    }


class _Rule(Flowable):
    """A hairline the width of the frame — the divider between narrative and appendix."""

    def __init__(self, width: float, colour: Color = tk.RULE_STRONG, thickness: float = 0.6):
        super().__init__()
        self.width = width
        self.height = thickness
        self._colour = colour
        self._thickness = thickness

    def draw(self) -> None:
        self.canv.setStrokeColor(self._colour)
        self.canv.setLineWidth(self._thickness)
        self.canv.line(0, 0, self.width, 0)


class _ReportDoc(BaseDocTemplate):
    """Page furniture: running heads, folios, the provenance footer and the watermark.

    Tracks the current section so the running head can name it — a reader who picks the document up
    mid-way should know where they are without paging back.
    """

    def __init__(
        self,
        buffer: BytesIO,
        *,
        report: ClientReport,
        meta: ReportMeta,
        section_pages: dict[int, list[str]] | None = None,
    ):
        super().__init__(
            buffer,
            pagesize=tk.PAGE_SIZE,
            leftMargin=tk.MARGIN_L,
            rightMargin=tk.MARGIN_R,
            topMargin=tk.MARGIN_T,
            bottomMargin=tk.MARGIN_B,
            title=f"{report.subject} — Platform assessment",
            author=meta.prepared_by,
            subject=meta.engagement_title,
        )
        self._report = report
        self._meta = meta
        #: page number → the section titles that BEGIN on that page, in order. Filled on the
        #: recording pass and supplied back on the rendering pass.
        self.recorded_sections: dict[int, list[str]] = {}
        self._section_pages = section_pages

        page_width, page_height = tk.PAGE_SIZE
        frame_width = page_width - tk.MARGIN_L - tk.MARGIN_R
        frame_height = page_height - tk.MARGIN_T - tk.MARGIN_B - tk.HEAD_GAP - tk.FOOT_GAP
        self.frame_width = frame_width

        cover_frame = Frame(
            tk.MARGIN_L,
            tk.MARGIN_B,
            frame_width,
            page_height - tk.MARGIN_T - tk.MARGIN_B,
            id="cover",
        )
        body_frame = Frame(
            tk.MARGIN_L, tk.MARGIN_B + tk.FOOT_GAP, frame_width, frame_height, id="body"
        )
        # Background and watermark are drawn at page START so content sits over them; the running
        # head is drawn at page END. That split is not cosmetic: `onPage` fires before the page's
        # flowables are laid out, so a head drawn there names whatever section the PREVIOUS page
        # ended in — which put "What is holding it back" above the page that says "What to do about
        # it". Drawing at page end means every section mark on the page has already been seen.
        self.addPageTemplates(
            [
                PageTemplate(
                    id="cover",
                    frames=[cover_frame],
                    onPage=self._draw_page_ground,
                    onPageEnd=self._draw_cover_furniture,
                ),
                PageTemplate(
                    id="body",
                    frames=[body_frame],
                    onPage=self._draw_page_ground,
                    onPageEnd=self._draw_body_furniture,
                ),
            ]
        )

    # -- section tracking, driven by a bookmark flowable in the story -------------------

    def afterFlowable(self, flowable: Flowable) -> None:
        section = getattr(flowable, "_section_title", None)
        if section is not None:
            self.recorded_sections.setdefault(self.page, []).append(str(section))

    def _section_for_page(self, page: int) -> str:
        """The section a reader is in at the TOP of this page.

        If a section begins on the page, that is the one — the heading is right there. Otherwise the
        page continues the last section that began on an earlier page. Naming the LAST section on
        the page instead (what `onPageEnd` alone gives) puts a title above content the reader has
        not reached: page 2 opened with "The business" under a head reading "What is holding it
        back". Naming the section at page START is what makes the head useful to someone who picks
        the document up mid-way.
        """
        if self._section_pages is None:
            return ""
        beginning_here = self._section_pages.get(page)
        if beginning_here:
            return beginning_here[0]
        earlier = [p for p in self._section_pages if p < page and self._section_pages[p]]
        if not earlier:
            return ""
        return self._section_pages[max(earlier)][-1]

    # -- furniture ---------------------------------------------------------------------

    def _draw_watermark(self, canvas: Canvas) -> None:
        """Drawn FIRST, so content sits over it and nothing can hide it (ADR-0029)."""
        marks = []
        if self._meta.mode is DeliverableMode.DRAFT_INTERNAL:
            marks.append(DRAFT_WATERMARK)
        if self._meta.non_production:
            marks.append("NON-PRODUCTION DATA")
        if not marks:
            return

        page_width, page_height = tk.PAGE_SIZE
        canvas.saveState()
        canvas.setFont(tk.SANS_BOLD, 40)
        canvas.setFillColor(tk.RULE_STRONG)
        canvas.setFillAlpha(0.30)
        canvas.translate(page_width / 2, page_height / 2)
        canvas.rotate(38)
        for index, mark in enumerate(marks):
            offset = (len(marks) - 1) * 26 / 2 - index * 52
            canvas.drawCentredString(0, offset, mark)
        canvas.restoreState()

    def _draw_page_ground(self, canvas: Canvas, _doc: BaseDocTemplate) -> None:
        """Paper and watermark, beneath everything. Runs at page start."""
        page_width, page_height = tk.PAGE_SIZE
        canvas.saveState()
        canvas.setFillColor(tk.PAPER)
        canvas.rect(0, 0, page_width, page_height, stroke=0, fill=1)
        canvas.restoreState()
        self._draw_watermark(canvas)

    def _draw_cover_furniture(self, canvas: Canvas, _doc: BaseDocTemplate) -> None:
        _, page_height = tk.PAGE_SIZE

        # The mark. A typographic wordmark rather than a bitmap: it stays crisp at any size and
        # needs no binary asset in the repo.
        canvas.saveState()
        canvas.setFillColor(tk.ACCENT)
        canvas.setFont(tk.SANS_BOLD, 15)
        canvas.drawString(tk.MARGIN_L, page_height - tk.MARGIN_T, WORDMARK)
        canvas.setFont(tk.SANS, 7.5)
        canvas.setFillColor(tk.INK_MUTED)
        canvas.drawString(tk.MARGIN_L, page_height - tk.MARGIN_T - 11, WORDMARK_SUB)
        # An accent rule under the mark — the one chromatic element on the page.
        canvas.setStrokeColor(tk.ACCENT)
        canvas.setLineWidth(1.6)
        canvas.line(
            tk.MARGIN_L,
            page_height - tk.MARGIN_T - 20,
            tk.MARGIN_L + 46,
            page_height - tk.MARGIN_T - 20,
        )
        canvas.restoreState()

        self._draw_confidentiality(canvas)

    def _draw_body_furniture(self, canvas: Canvas, doc: BaseDocTemplate) -> None:
        page_width, page_height = tk.PAGE_SIZE
        canvas.saveState()
        # Running head: the client on the left, the section on the right.
        canvas.setFont(tk.SANS, tk.RUNNING_HEAD[0])
        canvas.setFillColor(tk.INK_MUTED)
        head_y = page_height - tk.MARGIN_T + 4
        canvas.drawString(tk.MARGIN_L, head_y, self._report.subject)
        section = self._section_for_page(doc.page)
        if section:
            canvas.drawRightString(page_width - tk.MARGIN_R, head_y, section)
        canvas.setStrokeColor(tk.RULE)
        canvas.setLineWidth(0.5)
        canvas.line(tk.MARGIN_L, head_y - 4, page_width - tk.MARGIN_R, head_y - 4)

        # Folio.
        canvas.setFont(tk.MONO, tk.FOLIO[0])
        canvas.setFillColor(tk.INK_MUTED)
        canvas.drawCentredString(page_width / 2, tk.MARGIN_B, str(doc.page))
        canvas.restoreState()

        self._draw_confidentiality(canvas)

    def _draw_confidentiality(self, canvas: Canvas) -> None:
        """Provenance footer (scope item 6): who, when, and which versions produced the numbers."""
        page_width, _ = tk.PAGE_SIZE
        canvas.saveState()
        canvas.setFont(tk.SANS, 6.6)
        canvas.setFillColor(tk.INK_MUTED)
        line = (
            f"Confidential — prepared for {self._report.subject} by {self._meta.prepared_by} · "
            f"{self._meta.generated_on.isoformat()} · "
            f"methodology {self._report.methodology_version} · "
            # Plain English, not the config identifier. GRS-0219's provenance honesty is the point
            # and it stays; `coefficients v1-draft-pending-elicitation` was that fact written in a
            # vocabulary the reader does not share.
            + coefficient_status_sentence(
                version=self._report.coefficient_version,
                client_usable=self._meta.coefficients_client_usable,
            )
        )
        canvas.drawString(tk.MARGIN_L, tk.MARGIN_B - 9, line)
        canvas.restoreState()


class _SectionMark(Spacer):
    """A zero-height marker that tells the doc template which section the page is in."""

    def __init__(self, title: str):
        super().__init__(1, 0)
        self._section_title = title


def _figure(png: bytes, width: float, caption: str, styles: dict[str, ParagraphStyle]) -> list:
    """A figure with its caption, kept on one page — a chart orphaned from its caption is noise."""
    reader = ImageReader(BytesIO(png))
    native_width, native_height = reader.getSize()
    height = width * native_height / native_width
    return [
        KeepTogether(
            [
                Image(BytesIO(png), width=width, height=height),
                Spacer(1, 3),
                Paragraph(caption, styles["caption"]),
            ]
        ),
        Spacer(1, tk.SPACE_FIGURE),
    ]


def _figures_table(
    section: ReportSection, styles: dict[str, ParagraphStyle], width: float
) -> Table:
    """The section's declared figures, as a table a reader can check the prose against.

    Repeating header, because scope item 5 asks for tables that break properly — and because a
    continuation page of unlabelled numbers is unreadable.
    """
    rows: list[list] = [
        [
            Paragraph("<b>Figure</b>", styles["caption"]),
            Paragraph("<b>Value</b>", styles["caption"]),
            Paragraph("<b>Source</b>", styles["caption"]),
        ]
    ]
    for figure in section.figures:
        rows.append(
            [
                Paragraph(figure.label, styles["caption"]),
                Paragraph(figure.rendered, styles["key"]),
                Paragraph(figure.source, styles["key"]),
            ]
        )
    # Column widths are MEASURED, not guessed. The Value column carries version strings as well as
    # two-digit scores, and the Source column carries keys like `run.modules.ORCHESTRATION.q_m`; at
    # 8pt IBM Plex Mono those need 28.6% and 29.6% of the frame respectively (pdfmetrics), so each
    # gets that plus padding. Guessing produced "v1-draft-pen ding-elicita tion" — reportlab breaks
    # an over-wide token at an arbitrary character, which looks like a typo in a client document.
    table = Table(
        rows,
        colWidths=[width * 0.30, width * 0.33, width * 0.37],
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), tk.PAPER_SUNKEN),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, tk.RULE_STRONG),
                ("LINEBELOW", (0, 1), (-1, -2), 0.25, tk.RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _rendered_figures(figure_data: ReportFigureData) -> dict[str, bytes]:
    """Rasterise each figure ONCE. The document is built twice (see `render_client_report_pdf`) and
    a 300dpi radar is not something to draw twice for no reason."""
    rendered: dict[str, bytes] = {}
    # A radar needs at least three axes to be a shape rather than a line. A firm assessed on one or
    # two modules is a real case — early in an engagement it is the NORMAL case — so the radar is
    # omitted rather than drawn, and certainly rather than padded with invented axes. The module
    # breakdown below still carries every assessed module, so nothing is lost but the polygon.
    if len(figure_data.maturity.labels) >= 3:
        rendered["maturity"] = figs.maturity_radar(
            labels=list(figure_data.maturity.labels), values=list(figure_data.maturity.values)
        )
    rendered["value_buildup"] = figs.value_buildup(
        labels=list(figure_data.value_buildup.labels),
        values=list(figure_data.value_buildup.values),
    )
    if figure_data.module_breakdown.labels:
        rendered["module_breakdown"] = figs.module_breakdown(
            labels=list(figure_data.module_breakdown.labels),
            values=list(figure_data.module_breakdown.values),
        )
    return rendered


def client_report_filename(*, subject: str, generated_on: date) -> str:
    """What the client's copy is called on disk (GRS-0234 scope 1).

    An advisor forwards this file to a CFO. It arrived named `f6312cfe-4310-...pdf`, which is a
    database identifier in someone's inbox — and the cause was not this string but CORS: the browser
    could not read `Content-Disposition` because it was never exposed, so the client fell back to
    the deliverable id. Both halves are fixed; this is the half that decides what it says.

    ASCII-folded and punctuation-stripped rather than merely space-replaced: the name crosses a
    filesystem, an email client and whatever the recipient uses, and a slash or a colon in it is a
    broken attachment somewhere. The em-dashes are deliberate and safe — they are separators in the
    house style, and `Content-Disposition` carries them via RFC 5987.
    """
    cleaned = re.sub(r"[^\w\s-]", "", subject, flags=re.UNICODE).strip()
    cleaned = re.sub(r"\s+", " ", cleaned) or "Client"
    return f"Bruntsfield — Platform assessment — {cleaned} — {generated_on:%Y-%m}.pdf"


def render_client_report_pdf(
    report: ClientReport,
    *,
    meta: ReportMeta,
    figure_data: ReportFigureData,
) -> bytes:
    """The report as a branded PDF.

    The content model arrives validated (order, appendix-only maths, declared figures, approval), so
    nothing here re-checks it — this function is presentation only.

    Built in PASSES, because page furniture cannot know the future during a single pass and a
    running head that names the wrong section is worse than none:

    1. record which page each section starts on;
    2. if the report is long enough to need a contents page, insert one — which pushes every
       body page down by exactly one — and record again against that layout;
    3. render, drawing the running heads and the contents entries from the final map.

    A contents page is only produced beyond `CONTENTS_THRESHOLD_PAGES`. Below that it is furniture
    for its own sake: a reader can see the whole shape by scrolling.
    """
    rendered = _rendered_figures(figure_data)

    first = _build_document(report, meta=meta, rendered=rendered, section_pages=None)
    wants_contents = first.page_count > tk.CONTENTS_THRESHOLD_PAGES

    recording = first
    if wants_contents:
        # Re-record against the layout that HAS the contents page, so the numbers it prints are the
        # numbers the reader will turn to. Recording against the shorter layout would print a
        # contents that is wrong by exactly one page — the classic off-by-one nobody notices until
        # a client follows it.
        recording = _build_document(
            report, meta=meta, rendered=rendered, section_pages=None, contents={}
        )

    return _build_document(
        report,
        meta=meta,
        rendered=rendered,
        section_pages=recording.recorded_sections,
        contents=recording.recorded_sections if wants_contents else None,
    ).output


@dataclass(frozen=True)
class _BuildResult:
    output: bytes
    recorded_sections: dict[int, list[str]]
    page_count: int


def _contents_flowables(
    contents: dict[int, list[str]], styles: dict[str, ParagraphStyle], width: float
) -> list:
    """A contents page built from the recorded section→page map (scope item 3)."""
    rows = [
        [Paragraph(title, styles["body"]), Paragraph(str(page), styles["key"])]
        for page in sorted(contents)
        for title in contents[page]
    ]
    if not rows:
        return []
    table = Table(rows, colWidths=[width * 0.86, width * 0.14], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("LINEBELOW", (0, 0), (-1, -2), 0.25, tk.RULE),
            ]
        )
    )
    return [Paragraph("Contents", styles["section"]), Spacer(1, 6), table, PageBreak()]


def _build_document(
    report: ClientReport,
    *,
    meta: ReportMeta,
    rendered: dict[str, bytes],
    section_pages: dict[int, list[str]] | None,
    contents: dict[int, list[str]] | None = None,
) -> _BuildResult:
    styles = _styles()
    buffer = BytesIO()
    doc = _ReportDoc(buffer, report=report, meta=meta, section_pages=section_pages)
    width = doc.frame_width
    story: list = []

    # --- Cover (scope item 1) ---------------------------------------------------------
    story.append(Spacer(1, 58 * mm))
    story.append(Paragraph(report.subject, styles["cover_title"]))
    story.append(Spacer(1, 5))
    story.append(_Rule(46, tk.ACCENT, 1.6))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Platform assessment", styles["cover_sub"]))
    # GRS-0234 scope 2: the engagement title used to print here — "WeBull — delivery", an internal
    # filing key under an otherwise good cover. Dropped rather than humanised: the title above IS
    # the client and the line above IS the document, so a third line would only repeat one of them.
    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            f"{meta.generated_on.strftime('%d %B %Y')} · prepared by {meta.prepared_by}",
            styles["caption"],
        )
    )
    story.append(NextPageTemplate("body"))
    story.append(PageBreak())

    # Contents, when the report is long enough to need one. An empty dict means "reserve the page,
    # we do not know the numbers yet" — the recording pass that measures the shifted layout.
    if contents is not None:
        story.extend(_contents_flowables(contents, styles, width) or [Spacer(1, 1), PageBreak()])

    # --- Narrative body ---------------------------------------------------------------
    body_sections = [s for s in report.sections if s.kind is not ReportSectionKind.APPENDIX]
    for index, section in enumerate(body_sections):
        title = SECTION_TITLES[section.kind]
        story.append(_SectionMark(title))
        story.append(Paragraph(title, styles["section"]))
        for paragraph in section.body:
            story.append(Paragraph(paragraph, styles["body"]))

        # The figures live with the sections they belong to.
        if section.kind is ReportSectionKind.CONSTRAINT and "maturity" in rendered:
            story.extend(
                _figure(
                    rendered["maturity"],
                    width * 0.72,
                    "Module maturity across the assessed modules (0–100).",
                    styles,
                )
            )
        if section.kind is ReportSectionKind.VALUE:
            # NOTE (GRS-0234 scope 4): narrowing this to 0.72 was tried as a cheap fix for the
            # sparse page and MEASURED NOT TO HELP — the page stayed at ~300 chars plus the chart
            # across all three samples. Reverted rather than kept, because the change had no effect
            # and its comment would have claimed one. The sparse page is the VALUE section's own
            # length plus a figure, not the figure's width; a real fix is a reportlab keep-with rule
            # binding the figure to its preceding paragraph, which is not done here.
            story.extend(
                _figure(
                    rendered["value_buildup"],
                    width,
                    "How Platform Value builds up from the underlying indices.",
                    styles,
                )
            )
        if index < len(body_sections) - 1:
            story.append(Spacer(1, tk.SPACE_SECTION))

    # --- The break between the story and the maths (scope item 3) ---------------------
    story.append(PageBreak())
    appendix = report.section(ReportSectionKind.APPENDIX)
    appendix_title = SECTION_TITLES[ReportSectionKind.APPENDIX]
    story.append(_SectionMark(appendix_title))
    story.append(_Rule(width))
    story.append(Spacer(1, 6))
    story.append(Paragraph(appendix_title, styles["section"]))
    story.append(
        Paragraph(
            "Everything the narrative refers to, with the versions that produced it. "
            "The story ends here; what follows is the arithmetic behind it.",
            styles["caption"],
        )
    )
    story.append(Spacer(1, 10))
    for paragraph in appendix.body:
        story.append(Paragraph(paragraph, styles["body"]))

    if "module_breakdown" in rendered:
        story.extend(
            _figure(
                rendered["module_breakdown"],
                width,
                "Every assessed module, weakest first. Unassessed modules are omitted, not scored "
                "zero.",
                styles,
            )
        )

    if appendix.figures:
        story.append(Paragraph("Every figure quoted in this report", styles["caption"]))
        story.append(Spacer(1, 4))
        story.append(_figures_table(appendix, styles, width))

    doc.build(story)
    return _BuildResult(
        output=buffer.getvalue(),
        recorded_sections=doc.recorded_sections,
        page_count=doc.page,
    )
