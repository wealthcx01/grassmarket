"""The Prospecting surface's shared vocabulary (GRS-0238).

Two problems in the imported registry that an advisor should never have to decode, both **measured
before they were fixed** (evidence in `docs/reviews/GRS-0238-prospecting-surface/`):

1. **The `segment` column mixes two different kinds of thing.** "Bank" and "Sell-side research" say
   what kind of *firm* it is; "Data", "Indices", "News", "Fixings", "CORAX" say what the supplier
   *supplies*. They arrived in one column because two import sources filled it from two different
   spreadsheet fields. This module gives every observed value an advisor-readable label and says
   which of the two kinds it is, so the Prospecting filter can group them honestly instead of
   presenting a supplier's content type as though it were a sector.

2. **128 institutions from the LSEG roster are named by a domain stem, not a name** — `gs`, `db`,
   `citi`, and (from clearly broken source rows) `uk`, `us`, `hk`. Their `inferred_institution`
   column holds the stem of the domain, and 124 of 129 are all-lowercase. This module decides how
   such a row is *displayed*, and the rule is the same one the rest of the codebase runs on: show
   what is actually known, never invent the rest. `gs` is not silently rendered "Goldman Sachs",
   because that is a guess, and a guess printed without a mark is a fabrication (#3).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class SegmentKind(StrEnum):
    """Which question a segment value answers."""

    FIRM_TYPE = "firm_type"
    """What kind of institution it is — comparable across sources, safe to filter a pipeline on."""

    CONTENT_TYPE = "content_type"
    """What the supplier supplies. Says nothing about the firm's size, market or suitability."""

    UNKNOWN = "unknown"
    """Observed in the data with no curated label. Shown as-is; never guessed at."""


#: Every `segment` value observed across the four committed import sources on 2026-08-19, with an
#: advisor-readable label. Counts at the time of writing are in the review folder. Deliberately a
#: closed map with an explicit fallback rather than a heuristic: a new source adding a value should
#: surface as "unlabelled", not be quietly title-cased into something that reads authoritative.
SEGMENT_LABELS: dict[str, tuple[str, SegmentKind]] = {
    # Firm types — the two sources that describe institutions.
    "Bank": ("Bank", SegmentKind.FIRM_TYPE),
    "Sell-side research": ("Sell-side research house", SegmentKind.FIRM_TYPE),
    "Exchange supplier": ("Exchange supplier", SegmentKind.FIRM_TYPE),
    # Content types — what an exchange supplier supplies, from the supplier sheet's "Content Type".
    "Data": ("Supplies: market data", SegmentKind.CONTENT_TYPE),
    "Indices": ("Supplies: indices", SegmentKind.CONTENT_TYPE),
    "Data and Indices": ("Supplies: data and indices", SegmentKind.CONTENT_TYPE),
    "News": ("Supplies: news", SegmentKind.CONTENT_TYPE),
    "Fixings": ("Supplies: fixings", SegmentKind.CONTENT_TYPE),
    "Reference Data": ("Supplies: reference data", SegmentKind.CONTENT_TYPE),
    "Fixed Income T&Cs": ("Supplies: fixed-income terms", SegmentKind.CONTENT_TYPE),
    "Fixed Income Data": ("Supplies: fixed-income data", SegmentKind.CONTENT_TYPE),
    "Funds": ("Supplies: fund data", SegmentKind.CONTENT_TYPE),
    "Ratings": ("Supplies: ratings", SegmentKind.CONTENT_TYPE),
    # Product and desk names that reached the column as though they were sectors. Labelled as what
    # they are rather than dressed up, because pretending "CORAX" is a market segment helps nobody.
    "CORAX": ("Supplies: corporate actions (CORAX)", SegmentKind.CONTENT_TYPE),
    "IDB": ("Supplies: inter-dealer broker content", SegmentKind.CONTENT_TYPE),
    "Broker content -IDB": ("Supplies: inter-dealer broker content", SegmentKind.CONTENT_TYPE),
    "Broker content - IDB": ("Supplies: inter-dealer broker content", SegmentKind.CONTENT_TYPE),
    "Eikon App": ("Supplies: Eikon app content", SegmentKind.CONTENT_TYPE),
}


def segment_label(value: str | None) -> tuple[str, SegmentKind]:
    """(label, kind) for a stored segment value.

    An unmapped value is returned verbatim under `UNKNOWN` rather than prettified. The advisor sees
    the raw string, which is ugly and correct — and the ugliness is the signal that a new import
    source arrived without anyone labelling its vocabulary.
    """
    if not value:
        return ("Unclassified", SegmentKind.UNKNOWN)
    known = SEGMENT_LABELS.get(value)
    return known if known is not None else (value, SegmentKind.UNKNOWN)


#: A name this short and this lowercase is a domain stem, not a company name. Tuned against the
#: measured data: every all-lowercase single-token name in the registry came from the LSEG roster's
#: `inferred_institution` column, which holds domain stems.
def looks_like_a_domain_stem(name: str) -> bool:
    """Whether this target's name is an import artefact rather than a firm name.

    Used to MARK the row, never to hide it: the contacts attached to these targets are real and
    useful, and suppressing them would trade a visible data-quality problem for an invisible gap.
    """
    stripped = name.strip()
    return bool(stripped) and stripped == stripped.lower() and " " not in stripped


class ProspectingTarget(BaseModel):
    """One row of the Prospecting list — a registry target plus what this advisor needs to act.

    `already_in_my_pipeline` is joined **per principal**: targets are network-shared reference data
    (ADR-0045 §2), but a prospect is one advisor's claim on part of the universe and is owner-scoped
    like everything else (#9). The flag is therefore never cached across principals.
    """

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(min_length=1)
    #: What to SHOW. The curated name when one exists, otherwise whatever the import stored.
    name: str = Field(min_length=1)
    #: What the import actually stored. Kept beside `name` so a curated row never hides its own
    #: provenance — an advisor can still see the source said `gs`.
    imported_name: str = Field(min_length=1)
    domain: str | None = None
    country: str | None = None
    segment: str | None = None
    segment_label: str
    segment_kind: SegmentKind
    source: str
    imported_on: str
    contact_count: int = Field(ge=0)
    already_in_my_pipeline: bool
    #: True when `name` is a domain stem from the import rather than a verified company name. The
    #: UI must say so beside the row; it must not substitute a guessed name.
    name_unverified: bool
    #: True when a human has curated this name (GRS-0238 / D8).
    curated: bool = False


class ProspectingPage(BaseModel):
    """A page of the registry, with the counts a filter UI needs to describe itself honestly."""

    model_config = ConfigDict(extra="forbid")

    targets: list[ProspectingTarget]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1)
