"""The python-docx deliverable builder (GRS-0015, PRD §5, SD3 report-stack pattern).

Renders the first sections of the Diagnostic pack from a finalised scoring run:

- **Platform Power Report** — B/P/L/V with honest uncertainty statements (ADR-0008) and the triad
  ordinals with rationale (the ordinal is what a client sees; the audit score is noted, ADR-0002).
- **Methods Appendix** — engine/methodology/coefficient/uncertainty versions, the weight
  elicitation + review dates from the provenance records, and the weight-stability summary.

The document MODE is decided by the client-usable gate (`gate.py`) before we get here: a
DRAFT_INTERNAL document is watermarked "DRAFT — not client-usable" on every page.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from io import BytesIO

from bcap_contracts.assessments import CoefficientSet
from bcap_contracts.deliverables import DeliverableMode
from docx import Document
from docx.document import Document as DocxDocument
from docx.shared import Pt, RGBColor

from grassmarket.atlas.montecarlo import UncertaintyResult
from grassmarket.atlas.results import AtlasResult
from grassmarket.deliverables.gate import DRAFT_WATERMARK
from grassmarket.deliverables.uncertainty_text import format_index_statement, to_display


@dataclass(frozen=True)
class DeliverableContext:
    """Everything the Platform Power Report needs — all derived from the finalised run, so the
    document is reproducible. No `Money` here: the Platform Power Report is score-domain only."""

    subject: str
    result: AtlasResult
    uncertainty: UncertaintyResult
    coefficients: CoefficientSet
    uncertainty_version: str
    generated_on: date


_TRIAD_ORDER = (
    ("Economic Value", "economic_value"),
    ("Perceived Value", "perceived_value"),
    ("Defence Value", "defence_value"),
)


def build_platform_power_report(context: DeliverableContext, mode: DeliverableMode) -> bytes:
    """Render the Platform Power Report + Methods Appendix to .docx bytes."""
    doc = Document()
    if mode is DeliverableMode.DRAFT_INTERNAL:
        _apply_draft_watermark(doc)

    doc.add_heading(f"Platform Power Report — {context.subject}", level=0)
    doc.add_paragraph(f"Generated {context.generated_on.isoformat()}.")

    _platform_power_section(doc, context)
    _methods_appendix(doc, context)

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def _apply_draft_watermark(doc: DocxDocument) -> None:
    """A loud DRAFT banner in the page header (every page) plus a red top line. A DRAFT_INTERNAL
    document must never be mistaken for a client pack."""
    header = doc.sections[0].header
    hp = header.paragraphs[0]
    hp.text = DRAFT_WATERMARK
    for run in hp.runs:
        run.bold = True
        run.font.color.rgb = RGBColor(0x8A, 0x20, 0x20)
    banner = doc.add_paragraph()
    run = banner.add_run(DRAFT_WATERMARK)
    run.bold = True
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0x8A, 0x20, 0x20)


def _platform_power_section(doc: DocxDocument, context: DeliverableContext) -> None:
    doc.add_heading("Platform Power", level=1)
    unc = context.uncertainty

    doc.add_paragraph(
        "Platform value V and its components, with modelled uncertainty. Where an index's inputs "
        "carried no confidence grade, uncertainty is NOT modelled and the figure is stated as a "
        "point, never a tight range (Methodology §7)."
    )
    for name, band in (
        ("V (Platform Value)", unc.v_band),
        ("B (Business)", unc.b_band),
        ("P (Powers)", unc.p_band),
        ("L (Platform/Infrastructure)", unc.l_band),
    ):
        doc.add_paragraph(format_index_statement(name, band), style="List Bullet")

    doc.add_paragraph(
        f"Overall assessment uncertainty: {unc.overall_uncertainty.value}.",
    )

    doc.add_heading("Platform Power triad", level=2)
    doc.add_paragraph(
        "The triad is reported as an ORDINAL rating — the words a client sees. The audit-only "
        "score is shown for traceability; ordinal and currency are never mixed (ADR-0002)."
    )
    triad = context.result.triad
    for label, attr in _TRIAD_ORDER:
        dim = getattr(triad, attr)
        p = doc.add_paragraph(style="List Bullet")
        p.add_run(f"{label}: {dim.rating}. ").bold = True
        p.add_run(
            f"Ordinal rating derived from the continuous inputs against the ADR-0007 triad "
            f"thresholds (audit-only score {dim.score:.3f})."
        )


def _methods_appendix(doc: DocxDocument, context: DeliverableContext) -> None:
    doc.add_heading("Methods Appendix", level=1)
    result = context.result

    doc.add_heading("Versions", level=2)
    for label, value in (
        ("Engine", result.engine_version),
        ("Methodology", result.methodology_version),
        ("Coefficient set", result.coefficient_version),
        ("Uncertainty model", context.uncertainty_version),
    ):
        doc.add_paragraph(f"{label}: {value}", style="List Bullet")

    doc.add_heading("Weight provenance", level=2)
    provenance = context.coefficients.provenance
    theta = provenance.get("theta")
    if theta is not None:
        doc.add_paragraph(
            f"Weights expert-elicited {theta.set_on.isoformat()} "
            f"({theta.method.value}), review due {theta.review_due.isoformat()}."
        )

    doc.add_heading("Weight-stability summary", level=2)
    doc.add_paragraph(
        "Recorded dispersion for each coefficient family — the spread the §7 stability interval is "
        "drawn from."
    )
    table = doc.add_table(rows=1, cols=4)
    hdr = table.rows[0].cells
    hdr[0].text = "Family"
    hdr[1].text = "Set on"
    hdr[2].text = "Dispersion"
    hdr[3].text = "Review due"
    for family in sorted(provenance):
        record = provenance[family]
        row = table.add_row().cells
        row[0].text = family
        row[1].text = record.set_on.isoformat()
        row[2].text = record.dispersion
        row[3].text = record.review_due.isoformat()

    doc.add_paragraph(
        f"Headline platform value V = {to_display(result.composite.v_index):.1f} "
        f"(display scale 0–100)."
    )
