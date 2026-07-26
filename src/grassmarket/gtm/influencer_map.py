"""Generate an influencer map for a GTM target (GRS-0194, ADR-0045).

The LSEG connector returns cells as a flat `(ric, field, value)` list in analyst order, with no
row identity of its own. Rows are reconstructed by grouping per `(ric, field)` and zipping
index-wise, which only holds while every field returns the same number of cells for a RIC; an
unequal count means the analyst order has desynchronised, and zipping it anyway would attach one
analyst's email to another's name. That case fails loud rather than padding (GRS-0200 method
fact 1).

The pull itself sits behind the `LsegRosterSource` port so tests drive the whole generator from
fixture cells and CI never makes a live call.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

from bcap_contracts.entities import RegistryContact, RegistryTarget
from bcap_contracts.influencer import (
    InfluencerMap,
    InfluencerMapProvenance,
    InfluencerOwner,
    InfluencerRank,
)

from grassmarket.gtm.ingest import RowError, decode_lseg_rating, null_if_unset

# The roster fields, in the order the reconstructed rows key them. Verified against the live
# catalogue on 2026-07-23 (GRS-0200); there is no contributor-NAME field, which is why the
# institution comes from the curated map rather than from the pull.
ROSTER_FIELDS: tuple[str, ...] = (
    "TR.AnalystName",
    "TR.AnalystEmail",
    "TR.AnalystPhone",
    "TR.AnalystJobRole",
    "TR.AnalystCtbID",
    "TR.AnalystCreateDate",
    "TR.OverallAnalystEstimateRating",
    "TR.OverallAnalystRecommendationRatingT24M",
)

_FIELD_KEYS: dict[str, str] = {
    "TR.AnalystName": "analyst_name",
    "TR.AnalystEmail": "email",
    "TR.AnalystPhone": "phone",
    "TR.AnalystJobRole": "job_role",
    "TR.AnalystCtbID": "ctb_id",
    "TR.AnalystCreateDate": "create_date",
    "TR.OverallAnalystEstimateRating": "est_rating",
    "TR.OverallAnalystRecommendationRatingT24M": "rec_rating_24m",
}

# The source token GRS-0193 stamps on LSEG-derived contacts. Owner rows are everything else on the
# target, which is precisely the human-researched layer.
_LSEG_SOURCE = "lseg-roster"


@dataclass(frozen=True)
class LsegCell:
    """One cell as the connector returns it: no row identity of its own, only a position
    within its (ric, field) group."""

    ric: str
    field: str
    value: str | None


class LsegRosterSource(Protocol):
    """The port the generator pulls through — never the connector itself.

    Implementations batch at the connector's own 3-15 RICs with its inter-batch sleep, and one RIC
    failing never aborts the run (GRS-0200 method fact 5). No implementation ships in this ticket:
    every run is operator-triggered, so the live client is wired at the operator's console.
    """

    def fetch_cells(self, rics: Sequence[str], fields: Sequence[str]) -> list[LsegCell]: ...

    @property
    def connector(self) -> str: ...


def reconstruct_rows(cells: Iterable[LsegCell]) -> list[dict[str, str | None]]:
    """Rebuild analyst rows from the flat cell list, grouping per (ric, field) and zipping.

    Fails loud when a RIC's fields return different cell counts: the index-wise zip is the ONLY
    thing tying a name to an email, so a desynchronised response must abort rather than produce
    plausible, wrong people.
    """
    by_ric: dict[str, dict[str, list[str | None]]] = defaultdict(lambda: defaultdict(list))
    for cell in cells:
        by_ric[cell.ric][cell.field].append(cell.value)

    rows: list[dict[str, str | None]] = []
    for ric in sorted(by_ric):
        fields = by_ric[ric]
        counts = {field: len(values) for field, values in fields.items()}
        if len(set(counts.values())) > 1:
            raise RowError(
                f"RIC {ric} returned uneven field counts {counts}; the analyst order cannot be "
                f"reconstructed, so the pull is refused rather than mis-zipped."
            )
        length = next(iter(counts.values()), 0)
        for index in range(length):
            row: dict[str, str | None] = {"ric": ric}
            for field, values in fields.items():
                row[_FIELD_KEYS.get(field, field)] = null_if_unset(values[index])
            rows.append(row)
    return rows


def _parse_tenure(value: str | None) -> date | None:
    text = null_if_unset(value)
    if text is None:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError as exc:
            raise RowError(f"Unrecognised analyst create date {text!r}.") from exc


def rank_analysts(rows: Sequence[dict[str, str | None]], *, ctb_id: int) -> list[InfluencerRank]:
    """Filter the reconstructed rows to one contributor and rank its analysts.

    Ranking order, most to least significant:

    1. **Coverage breadth in the sample.** The analyst returned against the most sampled tickers
       has the widest franchise footprint, which is the strongest available proxy for seniority.
    2. **The estimate rating**, then the 24-month recommendation rating. Both are 0-100 signals
       where a higher value is the stronger analyst. *This direction is an assumption about the
       StarMine-style scale and is flagged for founder review; it changes the order within a
       coverage tier, never across tiers.*
    3. **Tenure**, earliest first: a longer-standing analyst is better placed to route a
       conversation upward.
    4. **Name**, so the output is deterministic and two runs of the same pull are comparable.

    A missing rating sorts last within its tier rather than as a zero, because an unrated analyst
    is not a badly-rated one.
    """
    grouped: dict[str, dict[str, object]] = {}
    for row in rows:
        raw_ctb = null_if_unset(row.get("ctb_id"))
        if raw_ctb is None or int(float(raw_ctb)) != ctb_id:
            continue
        name = null_if_unset(row.get("analyst_name"))
        if name is None:
            continue  # an anonymous contributor slot: no person to rank
        entry = grouped.setdefault(
            name,
            {
                "email": null_if_unset(row.get("email")),
                "phone": null_if_unset(row.get("phone")),
                "job_role": null_if_unset(row.get("job_role")),
                "est": decode_lseg_rating(row.get("est_rating")),
                "rec": decode_lseg_rating(row.get("rec_rating_24m")),
                "tenure": _parse_tenure(row.get("create_date")),
                "rics": set(),
            },
        )
        ric = null_if_unset(row.get("ric"))
        if ric is not None:
            rics = entry["rics"]
            assert isinstance(rics, set)
            rics.add(ric)

    def sort_key(item: tuple[str, dict[str, object]]) -> tuple[object, ...]:
        name, entry = item
        rics = entry["rics"]
        assert isinstance(rics, set)
        est = entry["est"]
        rec = entry["rec"]
        tenure = entry["tenure"]
        return (
            -len(rics),
            # `None` sorts after every rating rather than below every rating.
            (0, -int(est)) if isinstance(est, int) else (1, 0),
            (0, -int(rec)) if isinstance(rec, int) else (1, 0),
            (0, tenure.toordinal()) if isinstance(tenure, date) else (1, 0),
            name,
        )

    ranked: list[InfluencerRank] = []
    for position, (name, entry) in enumerate(sorted(grouped.items(), key=sort_key), start=1):
        rics = entry["rics"]
        assert isinstance(rics, set)
        ranked.append(
            InfluencerRank(
                rank=position,
                full_name=name,
                job_role=entry["job_role"],  # type: ignore[arg-type]
                email=entry["email"],  # type: ignore[arg-type]
                phone=entry["phone"],  # type: ignore[arg-type]
                covered_rics=tuple(sorted(rics)),
                estimate_rating=entry["est"],  # type: ignore[arg-type]
                recommendation_rating=entry["rec"],  # type: ignore[arg-type]
                tenure_start=entry["tenure"],  # type: ignore[arg-type]
                verified=False,
            )
        )
    return ranked


def owners_from_registry(contacts: Iterable[RegistryContact]) -> list[InfluencerOwner]:
    """The ownership layer: every registry contact that did NOT come from the LSEG roster.

    That split is what makes the artifact two-source. An LSEG row is an analyst whose employer was
    inferred; anything else on the target was put there by a human, and carries the verification
    status that human recorded. Verified rows lead, because they are the usable path.
    """
    owners = [
        InfluencerOwner(
            full_name=contact.full_name,
            job_role=contact.job_role,
            verified=contact.verified,
            source=contact.source,
        )
        for contact in contacts
        if contact.source != _LSEG_SOURCE
    ]
    owners.sort(key=lambda o: (not o.verified, o.full_name))
    return owners


def generate_influencer_map(
    target: RegistryTarget,
    contacts: Iterable[RegistryContact],
    source: LsegRosterSource,
    *,
    sample_rics: Sequence[str],
    generated_on: date,
) -> InfluencerMap:
    """Pull the roster for `sample_rics`, rank this target's analysts, and build the artifact.

    Fails loud when the target has no curated `ctb_id`: without it the roster cannot be filtered to
    this institution, and generating a map from every contributor's analysts would be a confidently
    wrong answer rather than a missing one.
    """
    if target.ctb_id is None:
        raise RowError(
            f"Target '{target.target_id}' has no curated LSEG contributor id, so its analysts "
            f"cannot be identified in a roster pull."
        )
    if not sample_rics:
        raise RowError("An influencer map needs at least one sampled ticker.")

    rows = reconstruct_rows(source.fetch_cells(list(sample_rics), list(ROSTER_FIELDS)))
    influencers = rank_analysts(rows, ctb_id=target.ctb_id)
    for_contributor = [
        row
        for row in rows
        if (raw := null_if_unset(row.get("ctb_id"))) is not None
        and int(float(raw)) == target.ctb_id
    ]
    return InfluencerMap(
        target_id=target.target_id,
        target_name=target.name,
        provenance=InfluencerMapProvenance(
            generated_on=generated_on,
            ctb_id=target.ctb_id,
            sample_rics=tuple(sample_rics),
            connector=source.connector,
            rows_returned=len(rows),
            rows_for_contributor=len(for_contributor),
        ),
        influencers=tuple(influencers),
        owners=tuple(owners_from_registry(contacts)),
        raw_rows=tuple(for_contributor),
    )
