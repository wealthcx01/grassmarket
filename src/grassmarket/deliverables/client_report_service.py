"""Assemble a deliverable's client report from what is stored (GRS-0219/0220 wiring).

GRS-0211 built the content model, GRS-0219 the PDF and GRS-0220 the shared page — and none of them
could be reached from the app, because the model takes prose as an input and nothing stored prose.
This module is that gap closed: it reads the advisor's saved words, reads the finalised run, and
hands back a validated `ClientReport` plus the figure data both renditions draw.

It fabricates nothing. A deliverable whose prose has never been written raises
`ReportNotAssembledError` rather than returning a report full of blanks, because a half-written
document that looks finished is exactly what would reach a client by accident.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from uuid import UUID

from bcap_contracts.client_report import SECTION_ORDER, ClientReport, ReportSectionKind, ReportTier

from grassmarket.deliverables.builder import DeliverableContext
from grassmarket.deliverables.client_report import SectionProse, build_client_report
from grassmarket.deliverables.report_figures import ReportFigureData, figure_data_from_context


class ReportNotAssembledError(Exception):
    """The advisor has not written this report's prose yet."""


@dataclass(frozen=True)
class AssembledReport:
    report: ClientReport
    figures: ReportFigureData


def default_prose() -> dict[str, dict]:
    """An empty draft: the six sections, in order, with their reader-facing headings and no words.

    Returned to the editor so an advisor starting a report sees the SHAPE of the argument they are
    being asked to make — business first, value last — rather than a blank page.
    """
    headings = {
        ReportSectionKind.BUSINESS: "The business",
        ReportSectionKind.ADVANTAGE: "Where the advantage sits",
        ReportSectionKind.CONSTRAINT: "What is holding it back",
        ReportSectionKind.ACTIONS: "What to do about it",
        ReportSectionKind.VALUE: "What that is worth",
        ReportSectionKind.APPENDIX: "Technical appendix",
    }
    return {
        kind.value: {"heading": headings[kind], "body": [], "tier": ReportTier.ENGAGED.value}
        for kind in SECTION_ORDER
    }


def parse_prose(sections_json: str) -> dict[ReportSectionKind, SectionProse]:
    """Turn the stored JSON into the builder's input, refusing anything incomplete.

    A section present but empty is treated as unwritten. An advisor who has typed nothing into "What
    is holding it back" has not written that section, and saying so is more useful than rendering a
    heading with silence under it.
    """
    raw = json.loads(sections_json)
    prose: dict[ReportSectionKind, SectionProse] = {}
    for kind in SECTION_ORDER:
        entry = raw.get(kind.value)
        if not entry:
            continue
        body = tuple(p.strip() for p in entry.get("body", []) if p and p.strip())
        if not body:
            continue
        prose[kind] = SectionProse(
            heading=entry.get("heading") or kind.value.title(),
            body=body,
            tier=ReportTier(entry.get("tier", ReportTier.ENGAGED.value)),
        )
    return prose


def assemble(
    context: DeliverableContext, *, scoring_run_id: UUID, sections_json: str | None
) -> AssembledReport:
    """Build the report for one deliverable, or refuse and say which sections are missing."""
    if not sections_json:
        raise ReportNotAssembledError(
            "This report has no prose yet. Write the six sections before rendering or sharing it — "
            "the narrative is written by a consultant, never generated from the score alone."
        )

    prose = parse_prose(sections_json)
    missing = [kind.value for kind in SECTION_ORDER if kind not in prose]
    if missing:
        raise ReportNotAssembledError(
            f"These sections have not been written yet: {', '.join(missing)}. "
            "A client report is only rendered once all six say something."
        )

    return AssembledReport(
        report=build_client_report(context, scoring_run_id=scoring_run_id, prose=prose),
        figures=figure_data_from_context(context),
    )
