"""Build the client report content model from a finalised run (GRS-0211).

This is the seam between what the engine knows and what a client reads. It divides the work the way
the two halves genuinely divide:

* **The run owns the figures.** Every number the report may state is read from the scoring run here,
  declared with the field it came from, and rendered once — so both renditions print the same
  string and any number in the report can be traced back to the run. Scoring is not touched: this
  module reads a result, it never computes one.
* **A human (or an approved AI draft) owns the prose.** "What this firm is and how it makes money"
  is not derivable from a scoring run, and inventing it would be exactly the fabrication CLAUDE.md
  non-negotiable #3 forbids. So prose is an *input*. A section with no prose is a refusal, not a
  blank — the report cannot be half-built and still look finished.

The narrative assistant (GRS-0222) will produce that prose; the founder review gate (ADR-0041)
approves it; the renditions (GRS-0219 PDF, GRS-0220 web) consume what comes out of here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from uuid import UUID

from bcap_contracts.client_report import (
    SECTION_ORDER,
    ClientReport,
    DeclaredFigure,
    ReportSection,
    ReportSectionKind,
    ReportTier,
)

from grassmarket.atlas.results import ModuleResult
from grassmarket.deliverables.builder import DeliverableContext
from grassmarket.deliverables.uncertainty_text import to_display


class MissingReportProseError(Exception):
    """A section of the report has no prose. Fail loud rather than ship a blank section."""


@dataclass(frozen=True)
class SectionProse:
    """The words for one section. Supplied by a consultant, or by an approved AI draft."""

    heading: str
    body: tuple[str, ...]
    ai_drafted: bool = False
    narrative_id: UUID | None = None
    tier: ReportTier = ReportTier.ENGAGED
    #: Figures this prose cites that the run cannot supply on its own (client-supplied context,
    #: e.g. headcount). Declared the same way, so they are still traceable to a stated source.
    extra_figures: tuple[DeclaredFigure, ...] = field(default_factory=tuple)


def _score(value: float | None) -> str | None:
    """A score as the report prints it: 0–100, no decimals. None stays None — never a zero (D9)."""
    if value is None:
        return None
    return f"{to_display(value):.0f}"


def _pct(value: float | None) -> str | None:
    if value is None:
        return None
    return f"{value * 100:.0f}%"


def figures_available_to(context: DeliverableContext) -> dict[str, list[DeclaredFigure]]:
    """Every figure the run makes available, per section (GRS-0230 scope 3).

    The editor shows these so an advisor knows the vocabulary BEFORE the gate teaches it to them by
    refusal. Nothing new is computed — this is the same `_figures_for` the assembler uses, exposed
    rather than recalculated, so what the editor offers and what the gate accepts cannot disagree.
    """
    return {kind.value: _figures_for(kind, context) for kind in ReportSectionKind}


def _figures_for(kind: ReportSectionKind, context: DeliverableContext) -> list[DeclaredFigure]:
    """The figures a section is allowed to cite, read straight off the run.

    A figure whose source value is absent is OMITTED rather than zero-filled. If the prose then
    cites it, the content model refuses the report — which is the intended failure: an absent
    number must not silently become a stated one.
    """
    result = context.result
    figures: list[DeclaredFigure] = []

    if kind is ReportSectionKind.BUSINESS:
        # Deliberately empty. The report opens with the business, and no score appears here — that
        # ordering is the whole point of the rebuild.
        return figures

    if kind is ReportSectionKind.ADVANTAGE:
        for row in result.powers.powers:
            # `value` is the Helmer both-required score: the WEAKER of benefit and barrier. The
            # report frames advantage through it, so a power with a strong benefit and no barrier
            # cannot read as a moat.
            figures.append(
                DeclaredFigure(
                    key=f"power_{row.key.lower()}",
                    label=f"{_power_name(row.key)} (0–100)",
                    rendered=f"{to_display(row.value):.0f}",
                    source=f"run.powers.{row.key}.value",
                )
            )
        return figures

    if kind is ReportSectionKind.CONSTRAINT:
        weakest = _weakest_module(context)
        if weakest is not None:
            rendered = _score(weakest.q_m)
            if rendered is not None:
                figures.append(
                    DeclaredFigure(
                        key="bottleneck_score",
                        label=f"{weakest.name} (0–100)",
                        rendered=rendered,
                        source=f"run.modules.{weakest.key}.q_m",
                    )
                )
            coverage = _pct(weakest.coverage)
            if coverage is not None:
                figures.append(
                    DeclaredFigure(
                        key="bottleneck_coverage",
                        label=f"{weakest.name} coverage",
                        rendered=coverage,
                        source=f"run.modules.{weakest.key}.coverage",
                    )
                )
        return figures

    if kind is ReportSectionKind.ACTIONS:
        # The levers are named per module by the gate bands; pricing lands with GRS-0219's value
        # rendition. What is declared here is the score each named module starts from, so a
        # recommendation cannot quote a number the run does not hold.
        for module in result.modules:
            rendered = _score(module.q_m)
            if rendered is None:
                continue
            figures.append(
                DeclaredFigure(
                    key=f"module_{module.key.lower()}",
                    label=f"{module.name} (0–100)",
                    rendered=rendered,
                    source=f"run.modules.{module.key}.q_m",
                )
            )
        return figures

    if kind is ReportSectionKind.VALUE:
        figures.append(
            DeclaredFigure(
                key="platform_value",
                label="Platform Value (0–100)",
                rendered=f"{result.v_display_0_100:.0f}",
                source="run.v_display_0_100",
            )
        )
        # The band in plain English. P10/P90 are the engine's terms and stay in the appendix; here
        # they are the two ends of "it could reasonably be between Y and Z".
        band = _reasonable_range(context)
        if band is not None:
            low, high = band
            figures.append(
                DeclaredFigure(
                    key="value_low",
                    label="Lower end of the reasonable range",
                    rendered=low,
                    source="run.uncertainty.v_band.p10",
                )
            )
            figures.append(
                DeclaredFigure(
                    key="value_high",
                    label="Upper end of the reasonable range",
                    rendered=high,
                    source="run.uncertainty.v_band.p90",
                )
            )
        return figures

    # APPENDIX — every number the body refers to, plus the versions that produced them.
    figures.extend(
        [
            DeclaredFigure(
                key="methodology_version",
                label="Methodology version",
                rendered=result.methodology_version,
                source="run.methodology_version",
            ),
            DeclaredFigure(
                key="coefficient_version",
                label="Coefficient set version",
                rendered=result.coefficient_version,
                source="run.coefficient_version",
            ),
            DeclaredFigure(
                key="engine_version",
                label="Engine version",
                rendered=result.engine_version,
                source="run.engine_version",
            ),
            DeclaredFigure(
                key="platform_value",
                label="Platform Value (0–100)",
                rendered=f"{result.v_display_0_100:.0f}",
                source="run.v_display_0_100",
            ),
        ]
    )
    for module in result.modules:
        rendered = _score(module.q_m)
        if rendered is None:
            # Not Assessed. Omitted, never zero-filled (D9) — the appendix says so in prose.
            continue
        figures.append(
            DeclaredFigure(
                key=f"module_{module.key.lower()}",
                label=f"{module.name} (0–100)",
                rendered=rendered,
                source=f"run.modules.{module.key}.q_m",
            )
        )
    return figures


def _weakest_module(context: DeliverableContext) -> ModuleResult | None:
    """The lowest-scoring assessed module — what is holding the firm back.

    Modules with no assessed subcomponent have `q_m is None` and are skipped: an unassessed module
    is not a weak one, and treating it as zero is defect D9.
    """
    # Paired with its score so the comparison key cannot be None — the filter above already
    # guarantees that, but pairing makes it true for the type checker as well as at runtime.
    scored = [(m.q_m, m) for m in context.result.modules if m.q_m is not None]
    if not scored:
        return None
    return min(scored, key=lambda pair: pair[0])[1]


def _power_name(key: str) -> str:
    """A power's key as a reader sees it. The run carries keys, not display names."""
    return key.replace("_", " ").title()


def _reasonable_range(context: DeliverableContext) -> tuple[str, str] | None:
    """The two ends of "it could reasonably be between Y and Z" — or None.

    None when the band is NOT modelled. That is the ADR-0008 honesty rule: an unmodelled band has
    P10 = P50 = P90, and printing it as a range would tell a client we have a tight estimate when
    what we actually have is a point. No range is declared, so prose that tries to state one is
    refused by the content model rather than quietly rendered.

    The range is clamped to contain the headline score, so a downward-skewed draw never puts the
    firm's own score outside its stated range.
    """
    band = context.uncertainty.v_band
    if not band.modelled:
        return None
    point = context.result.v_display_0_100
    low = min(to_display(band.p10), point)
    high = max(to_display(band.p90), point)
    return f"{low:.0f}", f"{high:.0f}"


def build_client_report(
    context: DeliverableContext,
    *,
    scoring_run_id: UUID,
    prose: Mapping[ReportSectionKind, SectionProse],
) -> ClientReport:
    """Assemble the report: structure and figures from here, words from `prose`.

    Refuses loudly if any section has no prose. The content model then applies its own four rules —
    order, appendix-only maths, declared figures, approval — so a report that returns from this
    function is one both renditions can print.
    """
    missing = [k.value for k in SECTION_ORDER if k not in prose]
    if missing:
        raise MissingReportProseError(
            f"no prose supplied for section(s): {', '.join(missing)}. "
            "Every section of a client report is written or approved by a human — a blank section "
            "is a refusal, not an empty page."
        )

    sections: list[ReportSection] = []
    for kind in SECTION_ORDER:
        words = prose[kind]
        sections.append(
            ReportSection(
                kind=kind,
                heading=words.heading,
                body=list(words.body),
                figures=[*_figures_for(kind, context), *words.extra_figures],
                tier=words.tier,
                ai_drafted=words.ai_drafted,
                narrative_id=words.narrative_id,
            )
        )

    return ClientReport(
        subject=context.subject,
        scoring_run_id=scoring_run_id,
        methodology_version=context.result.methodology_version,
        coefficient_version=context.result.coefficient_version,
        sections=sections,
    )
