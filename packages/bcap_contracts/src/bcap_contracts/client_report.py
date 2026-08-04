"""The client report content model (GRS-0211) — one narrative, no formatting.

The founder opened a finalised assessment, downloaded the deliverable preview, and wrote: "It is
terrible. It is so complicated, doesn't read well at all and has no branding." This module is the
replacement's spine. It defines *what the report says*, in an order borrowed from how the Acquired
podcast actually works — the business first, the score never on its own — and it deliberately
contains no formatting at all. The branded PDF (GRS-0219) and the interactive web page (GRS-0220)
both consume this same model, so the two renditions cannot drift apart in front of a client.

Four rules are enforced here rather than left to reviewers, because each of them is a way the old
preview failed:

1. **Order is fixed.** `SECTION_ORDER` is the report. A report missing a body section, or carrying
   them out of order, does not validate — so no rendition can quietly drop the part that explains
   what the numbers mean.
2. **The maths stays out of the reader's way.** `P10`/`P50`/`P90` may appear only in the technical
   appendix. The body says "our central estimate is X, and on the evidence we have it could
   reasonably be between Y and Z". The appendix keeps the exact terms.
3. **Every figure is declared.** A number in prose that the section has not declared is a build
   failure, not a proofreading problem. This is what lets a renderer surface figures and lets the
   narrative assistant (GRS-0222) be checked against the run it claims to describe.
4. **Nothing AI-drafted reaches a client unapproved** (non-negotiable #8). An AI-drafted section
   must carry its approved narrative before it can enter a client-facing report.

Scoring is untouched by any of this: the model cites a run, it never computes one.
"""

from __future__ import annotations

import re
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReportSectionKind(StrEnum):
    """The sections of a client report, in the order they are read.

    The body opens with the business and closes with what acting is worth; the appendix carries
    every number the body refers to. `SECTION_ORDER` below is normative.
    """

    BUSINESS = "business"
    """What this firm is and how it makes money, in plain prose. No score appears here."""

    ADVANTAGE = "advantage"
    """Where durable advantage sits, framed through the Powers that apply — and where it does
    not."""

    CONSTRAINT = "constraint"
    """The honest reading of what is holding the firm back."""

    ACTIONS = "actions"
    """What to do about it, with the levers ranked and priced."""

    VALUE = "value"
    """What that is worth if they act."""

    APPENDIX = "appendix"
    """Coefficients, weights, uncertainty method, coverage, the full module breakdown."""


SECTION_ORDER: tuple[ReportSectionKind, ...] = (
    ReportSectionKind.BUSINESS,
    ReportSectionKind.ADVANTAGE,
    ReportSectionKind.CONSTRAINT,
    ReportSectionKind.ACTIONS,
    ReportSectionKind.VALUE,
    ReportSectionKind.APPENDIX,
)

BODY_SECTIONS: frozenset[ReportSectionKind] = frozenset(SECTION_ORDER) - {
    ReportSectionKind.APPENDIX
}


class ReportTier(StrEnum):
    """Which audience a section is cleared for (the hook GRS-0214 will decide against).

    Declared per section so tiering is a property of the content, not of a renderer's filter.
    """

    FREE = "free"
    """Shown to a prospect before any engagement."""

    ENGAGED = "engaged"
    """Shown only under a paid engagement."""


# `P10`/`P50`/`P90` and friends. Body prose must not carry these; the appendix must be free to.
_UNCERTAINTY_TOKEN = re.compile(r"\bP(?:10|50|90)\b")

# A number-bearing token: optional currency, digits with optional thousands separators and decimal,
# optional unit suffix. Deliberately broad — over-catching costs a declaration, under-catching puts
# an undeclared claim in front of a client.
#
# The trailing guard is `(?!\w)`, NOT `(?![\w.])`. Excluding a following dot looked like it stopped
# the pattern matching "4" inside "4.2", but the leading lookbehind already does that — and it also
# skipped every number that ended a sentence ("a benchmark of 88."), which is the exact case this
# check exists to catch. A test caught it.
_NUMERIC_TOKEN = re.compile(
    r"(?<![\w.])(?:[£$€])?\d[\d,]*(?:\.\d+)?\s*(?:%|pp|bps|bn|m|k|x)?(?!\w)",
    re.IGNORECASE,
)

# Numerals that name the framework rather than measure this firm. Everything else must be declared.
_FRAMEWORK_LITERALS: tuple[str, ...] = ("7 Powers",)


def _normalise(token: str) -> str:
    """Compare figures on their digits and unit, not their whitespace."""
    return re.sub(r"\s+", "", token).lower()


class DeclaredFigure(BaseModel):
    """One number a section is allowed to state, and where it came from.

    `rendered` is the exact string the prose uses, so the check that follows compares like with
    like; `source` names the field on the scoring run it was read from, so a reader (or GRS-0222)
    can trace any number in the report back to the run that produced it.
    """

    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1, description="Stable identifier, unique within the section.")
    label: str = Field(min_length=1, description="What this figure is, in the reader's words.")
    rendered: str = Field(
        min_length=1,
        description="Exactly as it appears in the prose, e.g. '£1.2m' or '61'.",
    )
    source: str = Field(
        min_length=1,
        description="Where it came from on the scoring run, e.g. 'run.platform_value.point'.",
    )


#: The names a READER sees, per section. Lives here, in the contract, because three renditions need
#: them — the PDF, the public web page, and the refusal message an advisor reads when a number is
#: undeclared — and a name authored in three places drifts. That is not a hypothetical: GRS-0228 was
#: a message asserted in two places and authored in a third, red on main for nine days.
SECTION_TITLES: dict[ReportSectionKind, str] = {
    ReportSectionKind.BUSINESS: "The business",
    ReportSectionKind.ADVANTAGE: "Where the advantage sits",
    ReportSectionKind.CONSTRAINT: "What is holding it back",
    ReportSectionKind.ACTIONS: "What to do about it",
    ReportSectionKind.VALUE: "What that is worth",
    ReportSectionKind.APPENDIX: "Technical appendix",
}


#: A version CLAIM in prose: the thing named, then the value asserted for it. Matches "Methodology
#: v1.2", "methodology version 1.1", "the coefficient set v1-elicited", "engine version 1.4.0".
#: Deliberately anchored on the NAME rather than on anything version-shaped, so it cannot fire on an
#: ordinary number that happens to look like a version — a false refusal here would teach an advisor
#: to distrust the gate, which costs more than the check is worth.
_VERSION_CLAIM = re.compile(
    r"\b(methodology|coefficient(?:\s+set)?|engine|uncertainty)\b"
    r"[^.\n]{0,20}?"
    r"\bv(?:ersion)?\.?\s*([0-9][\w.\-]*)",
    re.IGNORECASE,
)


def _normalise_version(value: str) -> str:
    """Compare versions on their digits and separators, not their decoration. 'v1.2', 'V1.2' and
    '1.2' are the same claim; 'v1-elicited' and 'v1-draft' are not."""
    return value.strip().lstrip("vV").strip(". ").lower()


def version_mismatch_message(kind: ReportSectionKind, named: str, claimed: str, actual: str) -> str:
    """The refusal when prose asserts a version the run does not have (GRS-0232).

    In the product voice and beside its rule, for the same reason as `undeclared_figure_message` —
    both are read by an advisor and both are shown in two places.
    """
    return (
        f"{SECTION_TITLES[kind]} says the {named.lower()} version is {claimed}, but this "
        f"assessment ran on {actual}. A client checks the version table first, so the words and "
        f"the table have to agree. Correct the sentence, or re-run the assessment if it is "
        f"genuinely out of date."
    )


#: What a coefficient set's status MEANS, in a sentence a client can read (GRS-0234 scope 3).
#: Every page footer printed `coefficients v1-draft-pending-elicitation` — the provenance honesty is
#: right and stays, the internal config identifier is not something to put in front of a client. The
#: identifier keeps its place in the appendix's version table, where identifiers belong.
#:
#: Data rather than branching, so GRS-0150's eventual ratification changes the sentence by changing
#: which status the set carries — not by editing a renderer.
COEFFICIENT_STATUS_SENTENCES: dict[str, str] = {
    "draft": "Draft weighting — pending expert panel ratification.",
    "elicited": "Expert-elicited weighting — panel ratification pending.",
    "ratified": "Expert-elicited weighting, ratified by the Bruntsfield panel.",
}


def coefficient_status_sentence(*, version: str, client_usable: bool) -> str:
    """The footer's plain-English provenance line.

    Derived from what the set IS rather than from a status column, because there is no status
    column: `client_usable` is the flag the gate turns on when a set is fit to price a client pack,
    and the version string carries the rest. A set that is client-usable and still names itself
    draft is a contradiction worth surfacing rather than smoothing over — it resolves to the
    honest, weaker sentence.
    """
    names_draft = "draft" in version.lower()
    if names_draft or not client_usable:
        return COEFFICIENT_STATUS_SENTENCES["draft"]
    if "ratified" in version.lower():
        return COEFFICIENT_STATUS_SENTENCES["ratified"]
    return COEFFICIENT_STATUS_SENTENCES["elicited"]


def undeclared_figure_message(kind: ReportSectionKind, numbers: list[str]) -> str:
    """The sentence an advisor reads when their prose states a number the run does not declare.

    In the product voice, and in ONE place, because both the API and the editor show it. What it
    replaced named the section by its internal key and the rule by its class name
    (`section 'value' states ['£3.4m'] ... must be a DeclaredFigure`) — the exact leak GRS-0163
    existed to stop.

    It says three things, in this order: what is wrong, why the rule exists, and what to do. The
    middle one matters most: an advisor who understands that a client will trace the number stops
    experiencing the gate as an obstacle.
    """
    quoted = ", ".join(sorted(set(numbers)))
    plural = "those numbers are" if len(set(numbers)) > 1 else "that number is"
    return (
        f"{SECTION_TITLES[kind]} mentions {quoted}, but {plural} not among the figures this "
        f"assessment produced. Every number in a client report has to trace back to the scoring "
        f"run, so the client can check it. Use one of the figures listed beside this section, or "
        f"take the number out of the sentence."
    )


class ReportSection(BaseModel):
    """One section of the report: prose, the figures that prose is allowed to cite, and its gate."""

    model_config = ConfigDict(extra="forbid")

    kind: ReportSectionKind
    heading: str = Field(min_length=1)
    body: list[str] = Field(
        min_length=1,
        description="Paragraphs of plain prose. No markup — the renditions own presentation.",
    )
    figures: list[DeclaredFigure] = Field(default_factory=list)
    tier: ReportTier = ReportTier.ENGAGED
    ai_drafted: bool = Field(
        default=False,
        description="Whether the prose began as an AI draft. If so it needs an approved narrative.",
    )
    narrative_id: UUID | None = Field(
        default=None,
        description="The approved AINarrative this prose came from. Required when ai_drafted.",
    )

    @model_validator(mode="after")
    def _figures_have_unique_keys(self) -> ReportSection:
        keys = [f.key for f in self.figures]
        duplicates = sorted({k for k in keys if keys.count(k) > 1})
        if duplicates:
            raise ValueError(
                f"section '{self.kind}' declares the same figure key twice: {', '.join(duplicates)}"
            )
        return self

    @model_validator(mode="after")
    def _uncertainty_terms_stay_in_the_appendix(self) -> ReportSection:
        """Rule 2. The founder asked for the maths moved out of the reader's way."""
        if self.kind is ReportSectionKind.APPENDIX:
            return self
        for paragraph in self.body:
            found = _UNCERTAINTY_TOKEN.findall(paragraph)
            if found:
                raise ValueError(
                    f"section '{self.kind}' uses {sorted(set(found))} in the body. P10/P50/P90 "
                    "belong in the appendix; say 'our central estimate is X, and it could "
                    "reasonably be between Y and Z' instead."
                )
        return self

    @model_validator(mode="after")
    def _every_number_in_prose_is_declared(self) -> ReportSection:
        """Rule 3. An undeclared number is a build failure, not a proofreading problem."""
        declared = {_normalise(f.rendered) for f in self.figures}
        undeclared: list[str] = []
        for paragraph in self.body:
            scannable = paragraph
            for literal in _FRAMEWORK_LITERALS:
                scannable = scannable.replace(literal, "")
            for match in _NUMERIC_TOKEN.findall(scannable):
                token = _normalise(match)
                # A declared figure may be quoted whole ('£1.2m') or the prose may restate its
                # bare number; either way the token must be traceable to a declaration.
                if token in declared or any(token in d or d in token for d in declared):
                    continue
                undeclared.append(match.strip())
        if undeclared:
            raise ValueError(undeclared_figure_message(self.kind, undeclared))
        return self

    @model_validator(mode="after")
    def _ai_drafts_carry_their_approval(self) -> ReportSection:
        """Rule 4, structural half. The client-facing half is asserted in `assert_client_ready`."""
        if self.ai_drafted and self.narrative_id is None:
            raise ValueError(
                f"section '{self.kind}' is AI-drafted but names no approved narrative "
                "(non-negotiable #8: AI proposes, humans approve)."
            )
        return self


class ClientReport(BaseModel):
    """The whole report, rendition-agnostic.

    It is bound to the scoring run it interprets and to the versions that produced that run, so a
    report is always attributable — the same discipline scoring runs themselves carry.
    """

    model_config = ConfigDict(extra="forbid")

    subject: str = Field(min_length=1, description="The firm this report is about.")
    scoring_run_id: UUID
    methodology_version: str = Field(min_length=1)
    coefficient_version: str = Field(min_length=1)
    sections: list[ReportSection]

    @model_validator(mode="after")
    def _sections_are_complete_and_in_order(self) -> ClientReport:
        """Rule 1. The order IS the report — it is what makes it read as a story about a business
        rather than as a scorecard, which is the complaint this ticket exists to answer."""
        kinds = [s.kind for s in self.sections]
        duplicates = sorted({k for k in kinds if kinds.count(k) > 1})
        if duplicates:
            raise ValueError(f"report repeats section(s): {', '.join(duplicates)}")
        missing = [k for k in SECTION_ORDER if k not in kinds]
        if missing:
            raise ValueError(f"report is missing section(s): {', '.join(missing)}")
        if tuple(kinds) != SECTION_ORDER:
            raise ValueError(
                "report sections are out of order. Expected "
                f"{' → '.join(SECTION_ORDER)}, got {' → '.join(kinds)}."
            )
        return self

    @model_validator(mode="after")
    def _no_section_contradicts_the_run(self) -> ClientReport:
        """Rule 5 (GRS-0232). A version stated in prose must match the run — in EVERY section.

        The declared-figure gate (rule 3) exempts the appendix, which is right for percentile prose
        and wrong for this: it meant the one section holding the audit trail was the one section
        where a wrong number survived into a client artefact. "Methodology v1.2" shipped a
        centimetre above a table reading "Methodology version 1.1", and nothing caught it.

        Checked here rather than on `ReportSection` because a section does not know the run's
        versions — only the assembled report does. That also means no rendition can opt out: both
        the PDF and the web page are built from a validated `ClientReport` (GRS-0211's construction
        rule).
        """
        truth = {
            "methodology": self.methodology_version,
            "coefficient": self.coefficient_version,
            "coefficient set": self.coefficient_version,
        }
        # The engine and uncertainty versions are not fields on the report, but the appendix
        # declares them as figures — so where one exists, its declared value is the truth.
        for section in self.sections:
            for figure in section.figures:
                if figure.key in ("engine_version", "uncertainty_version"):
                    truth[figure.key.split("_")[0]] = figure.rendered

        for section in self.sections:
            for paragraph in section.body:
                for named, claimed in _VERSION_CLAIM.findall(paragraph):
                    actual = truth.get(named.strip().lower())
                    if actual is None:
                        # Nothing to check it against. Refusing here would block prose about a
                        # version this report does not carry, which is not this rule's business.
                        continue
                    if _normalise_version(claimed) != _normalise_version(actual):
                        raise ValueError(
                            version_mismatch_message(section.kind, named, claimed, actual)
                        )
        return self

    def section(self, kind: ReportSectionKind) -> ReportSection:
        """The one section of this kind. Validation guarantees exactly one exists."""
        for candidate in self.sections:
            if candidate.kind is kind:
                return candidate
        raise KeyError(kind)  # unreachable while _sections_are_complete_and_in_order holds

    def for_tier(self, tier: ReportTier) -> list[ReportSection]:
        """The sections a given audience may see. FREE content is visible to everyone."""
        if tier is ReportTier.ENGAGED:
            return list(self.sections)
        return [s for s in self.sections if s.tier is ReportTier.FREE]


class UnapprovedReportSectionError(Exception):
    """An AI-drafted section without a recorded approval tried to reach a client."""


def assert_client_ready(report: ClientReport, *, approved_narrative_ids: set[UUID]) -> None:
    """Refuse a client-facing report containing AI prose nobody approved.

    Fails loud and names the sections (CLAUDE.md non-negotiable #3 and #8). The caller supplies the
    approved set because approval lives in the repository layer, not in the content model.
    """
    offenders = [
        str(s.kind)
        for s in report.sections
        if s.ai_drafted and (s.narrative_id is None or s.narrative_id not in approved_narrative_ids)
    ]
    if offenders:
        raise UnapprovedReportSectionError(
            f"report for '{report.subject}' carries unapproved AI-drafted section(s): "
            f"{', '.join(offenders)}. Nothing AI-generated reaches a client without sign-off."
        )
