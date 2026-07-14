"""Earnings statement export (GRS-0028, PRD §7) — a consultant's own earnings as a .docx, via the
report stack (python-docx). A statement of the caller's OWN lines only; the £ is always shown from
the sealed `Money` figures, never recomputed.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from io import BytesIO

from bcap_contracts.commissions import CommissionLine, EarningsSummary
from bcap_contracts.money import Money
from docx import Document


def _fmt(money: Money) -> str:
    """A £-style figure from integer minor units (two decimal places, no locale grouping)."""
    return f"{money.currency.value} {money.amount_minor / 100:,.2f}"


def build_earnings_statement(
    *,
    summary: EarningsSummary,
    lines: Sequence[CommissionLine],
    consultant_name: str,
    generated_on: date,
) -> bytes:
    """A .docx earnings statement: a header, a per-line table, and the summary totals."""
    doc = Document()
    doc.add_heading(f"Earnings statement — {consultant_name}", level=0)
    doc.add_paragraph(f"Generated {generated_on.isoformat()}. Amounts in {summary.currency.value}.")

    if lines:
        table = doc.add_table(rows=1, cols=4)
        header = table.rows[0].cells
        header[0].text = "Earned"
        header[1].text = "Kind"
        header[2].text = "Amount"
        header[3].text = "Status"
        for line in lines:
            cells = table.add_row().cells
            cells[0].text = line.earned_on.isoformat() if line.earned_on else "—"
            cells[1].text = line.kind.value.replace("_", " ")
            cells[2].text = _fmt(line.amount)
            cells[3].text = line.payment_status.value
    else:
        doc.add_paragraph("No commission lines recorded.")

    doc.add_heading("Summary", level=1)
    for label, value in (
        ("Earned year-to-date", summary.ytd_earned),
        ("Pending", summary.pending),
        ("Invoiced", summary.invoiced),
        ("Paid", summary.paid),
        ("Projected (earned, unpaid)", summary.projected_unpaid),
    ):
        doc.add_paragraph(f"{label}: {_fmt(value)}")

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
