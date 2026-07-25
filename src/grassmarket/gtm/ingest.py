"""Row-to-contract mapping for the GTM registry imports (GRS-0193, ADR-0045).

Four source shapes feed one registry:

* the Exchange Supplier List (supplier-service rows with audited contact columns),
* the List of Banks (country + company, no contacts),
* the LSEG/I-B-E-S analyst roster pulled under GRS-0200, and
* the Barclays Live influencer workbook (analyst rows plus web-verified owner rows).

Everything here is pure: it takes rows that somebody else read off disk and returns contracts. The
fail-loud rule (#3) is applied at the row level — a row missing a REQUIRED field raises `RowError`
rather than being silently dropped, while a genuinely optional gap (an analyst with no published
email) records a `skipped` reason on the summary so the operator sees what did not import.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date

from bcap_contracts.entities import RegistryContact, RegistryTarget

# Values the LSEG connector uses for "unset". They are never zero, and never an empty rating —
# treating them as either is exactly the silent-fallback class of defect the scaffold exists to
# prevent (GRS-0200 method fact 1).
_UNSET_TOKENS = frozenset({"", "<na>", "na", "nat", "nan", "none", "null"})

# `TR.OverallAnalystRecommendationRatingT24M` comes back epoch-nanosecond-encoded: the timestamp
# 1970-01-01 00:00:00.000000054 means the rating 54 (GRS-0200 method fact 3).
_EPOCH_NS_RE = re.compile(r"^1970-01-01[ T]00:00:00\.(\d{1,9})$")


class RowError(ValueError):
    """A source row that cannot be imported without inventing data. Always fatal to that row."""


@dataclass
class ImportSummary:
    """What one import run did, printed by every script so a re-run is auditable."""

    source: str
    rows_read: int = 0
    targets_upserted: int = 0
    contacts_upserted: int = 0
    skipped: list[str] = field(default_factory=list)

    def skip(self, reason: str) -> None:
        self.skipped.append(reason)

    def as_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "rows_read": self.rows_read,
            "targets_upserted": self.targets_upserted,
            "contacts_upserted": self.contacts_upserted,
            "skipped": list(self.skipped),
        }


def null_if_unset(value: object) -> str | None:
    """Normalise a source cell to a string or None. `<NA>`, `NaT` and friends mean unset."""
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in _UNSET_TOKENS:
        return None
    return text


def decode_lseg_rating(value: object) -> int | None:
    """Decode a StarMine-style 1-100 rating, accepting either the plain integer or the
    epoch-nanosecond timestamp encoding the connector returns for the 24-month recommendation
    rating. Anything else raises rather than being coerced to a number that would rank an analyst.
    """
    text = null_if_unset(value)
    if text is None:
        return None
    stamped = _EPOCH_NS_RE.match(text)
    if stamped is not None:
        # The fractional seconds ARE the rating, counted in nanoseconds: ".000000054" -> 54. The
        # digits are right-padded because a fraction is positional, not an integer suffix.
        rating = int(stamped.group(1).ljust(9, "0"))
    else:
        try:
            rating = int(float(text))
        except ValueError as exc:
            raise RowError(f"Unrecognised analyst rating {text!r}.") from exc
    if not 0 <= rating <= 100:
        raise RowError(f"Analyst rating {rating} is outside the 0-100 scale.")
    return rating


def slugify(text: str, *, prefix: str = "") -> str:
    """A stable, readable id. Deterministic so that re-importing a source overwrites the same rows
    rather than duplicating them — idempotence is a property of the id, not of a dedupe pass."""
    normalised = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalised.lower()).strip("-")
    if not slug:
        raise RowError(f"Cannot derive an id from {text!r}.")
    return f"{prefix}{slug}" if prefix else slug


def _contact_id(target_id: str, *, email: str | None, name: str) -> str:
    """Prefer the email as the identity (one person, one row across sampled tickers); fall back to
    the name within the institution when no email was published."""
    key = email.lower() if email else name
    return f"{target_id}:{slugify(key)}"


# --------------------------------------------------------------------------- Exchange Supplier List


def parse_supplier_row(
    row: Mapping[str, object], *, imported_on: date, source: str = "exchange-supplier-list"
) -> tuple[RegistryTarget, list[RegistryContact]]:
    """One audited supplier-service row: the supplier becomes a target, and the audited contact
    columns become its contacts. A row with no supplier name is fatal — there is nothing to key on.
    """
    supplier = null_if_unset(row.get("Supplier"))
    if supplier is None:
        raise RowError("Supplier row has no 'Supplier' name.")
    target_id = slugify(supplier, prefix="xs-")
    url = null_if_unset(row.get("Audit: New URL")) or null_if_unset(row.get("Supplier URL"))
    target = RegistryTarget(
        target_id=target_id,
        name=supplier,
        aliases=(),
        domain=_domain_from_url(url),
        segment=null_if_unset(row.get("Content Type")) or "Exchange supplier",
        country=None,
        ric=None,
        ctb_id=None,
        source=source,
        imported_on=imported_on,
    )
    contacts: list[RegistryContact] = []
    name = null_if_unset(row.get("Audit: Contact Name"))
    email = null_if_unset(row.get("Audit: New Email")) or null_if_unset(row.get("Supplier Contact"))
    linkedin = null_if_unset(row.get("Audit: Contact LinkedIn"))
    if name is not None:
        contacts.append(
            RegistryContact(
                contact_id=_contact_id(target_id, email=email, name=name),
                target_id=target_id,
                full_name=name,
                email=email,
                phone=None,
                job_role=null_if_unset(row.get("Audit: Contact Title")),
                linkedin=linkedin,
                # The audit established the contact details, not the person's current role, so an
                # imported supplier contact is unverified until a human confirms it.
                verified=False,
                source=source,
                imported_on=imported_on,
            )
        )
    return target, contacts


def _domain_from_url(url: str | None) -> str | None:
    if url is None:
        return None
    match = re.match(r"^(?:https?://)?(?:www\.)?([^/\s]+)", url.strip())
    return match.group(1).lower() if match else None


# ------------------------------------------------------------------------------------ List of Banks


def parse_bank_row(
    row: Mapping[str, object], *, imported_on: date, source: str = "list-of-banks"
) -> RegistryTarget:
    """A `Country, Company` row. Targets only: the bank list carries no contacts."""
    company = null_if_unset(row.get("Company"))
    if company is None:
        raise RowError("Bank row has no 'Company' name.")
    return RegistryTarget(
        target_id=slugify(company, prefix="bank-"),
        name=company,
        aliases=(),
        domain=None,
        segment="Bank",
        country=null_if_unset(row.get("Country")),
        ric=None,
        ctb_id=None,
        source=source,
        imported_on=imported_on,
    )


# ------------------------------------------------------------------------------------- LSEG rosters


def parse_lseg_roster(
    rows: Iterable[Mapping[str, object]],
    institution_map: Mapping[int, Mapping[str, object]],
    *,
    imported_on: date,
    source: str = "lseg-roster",
    summary: ImportSummary | None = None,
) -> tuple[list[RegistryTarget], list[RegistryContact]]:
    """Group the flat analyst roster into one target per contributor and one contact per analyst.

    Applies the three GRS-0200 caveats. Rows with a blank `analyst_name` are the 311 anonymous
    contributor slots and are dropped, because a contact with no person is not a contact. `<NA>`
    and `NaT` become null rather than zero. The 24-month recommendation rating is decoded from its
    epoch-nanosecond encoding. A row with a name but no `ctb_id` cannot be attributed to an
    institution and is fatal, since guessing the employer is exactly the fabrication #3 forbids.
    """
    targets: dict[str, RegistryTarget] = {}
    contacts: dict[str, RegistryContact] = {}
    for row in rows:
        if summary is not None:
            summary.rows_read += 1
        name = null_if_unset(row.get("analyst_name"))
        if name is None:
            if summary is not None:
                summary.skip("anonymous contributor slot (blank analyst_name)")
            continue
        raw_ctb = null_if_unset(row.get("ctb_id"))
        if raw_ctb is None:
            raise RowError(f"Analyst {name!r} has no ctb_id, so their institution is unknown.")
        ctb_id = int(float(raw_ctb))
        # Decoded for its side effect: a malformed rating must fail the run rather than silently
        # rank an analyst by a number nobody can explain (GRS-0194 consumes these).
        decode_lseg_rating(row.get("rec_rating_24m"))
        mapped = institution_map.get(ctb_id)
        if mapped is None:
            if summary is not None:
                summary.skip(f"contributor {ctb_id} is not in the curated institution map")
            continue
        institution = null_if_unset(mapped.get("inferred_institution"))
        if institution is None:
            # The map is a FIRST-DRAFT inference from email domains, and a handful of contributors
            # published no domain to infer from. That is a gap in the map, not a malformed row, so
            # it is skipped and counted rather than aborting the run or being attributed to a
            # guessed employer. Curating these is the data task the ticket puts out of scope.
            if summary is not None:
                summary.skip(f"contributor {ctb_id} has no inferred institution in the map")
            continue
        target_id = slugify(institution, prefix="lseg-")
        ric = null_if_unset(row.get("ric"))
        existing = targets.get(target_id)
        targets[target_id] = RegistryTarget(
            target_id=target_id,
            name=institution,
            aliases=(),
            domain=null_if_unset(mapped.get("inferred_domain")),
            segment="Sell-side research",
            country=None,
            # The first RIC an institution is seen against is kept as a sample, not as a claim
            # that it is the only one; GRS-0194 pulls the full coverage per run.
            ric=existing.ric if existing is not None and existing.ric else ric,
            ctb_id=ctb_id,
            source=source,
            imported_on=imported_on,
        )
        email = null_if_unset(row.get("email"))
        contact_id = _contact_id(target_id, email=email, name=name)
        if contact_id not in contacts:
            contacts[contact_id] = RegistryContact(
                contact_id=contact_id,
                target_id=target_id,
                full_name=name,
                email=email,
                phone=null_if_unset(row.get("phone")),
                job_role=null_if_unset(row.get("job_role")),
                linkedin=None,
                # The institution is INFERRED from the dominant email domain (GRS-0200 method fact
                # 2), so no LSEG-derived contact is verified until the map is curated by a human.
                verified=False,
                source=source,
                imported_on=imported_on,
            )
    return list(targets.values()), list(contacts.values())


# ------------------------------------------------------------------------- Barclays influencer map


def parse_barclays_analyst_row(
    row: Mapping[str, object],
    *,
    target_id: str,
    imported_on: date,
    source: str = "barclays-influencer-map",
) -> RegistryContact:
    """One ranked analyst from the Influencer Map tab. These came from an LSEG pull, so like every
    LSEG-derived row they are unverified until a human confirms the person and the role."""
    name = null_if_unset(row.get("Name"))
    if name is None:
        raise RowError("Influencer-map row has no 'Name'.")
    email = null_if_unset(row.get("Email"))
    return RegistryContact(
        contact_id=_contact_id(target_id, email=email, name=name),
        target_id=target_id,
        full_name=name,
        email=email,
        phone=null_if_unset(row.get("Phone")),
        job_role=null_if_unset(row.get("Title (I/B/E/S)")),
        linkedin=None,
        verified=False,
        source=source,
        imported_on=imported_on,
    )


def parse_barclays_owner_row(
    row: Mapping[str, object],
    *,
    target_id: str,
    imported_on: date,
    source: str = "barclays-influencer-map",
) -> RegistryContact:
    """One row from the Target Owners tab, whose `Verification` column is a human's web research.

    Only a cleanly verified row imports as verified. "Partially verified", "Unverified - gap" and
    anything else keep `verified=False` and render flagged, which is the two-source rule GRS-0194
    depends on: the LSEG layer and the ownership layer never share a provenance.
    """
    name = null_if_unset(row.get("Name"))
    if name is None:
        raise RowError("Target-owner row has no 'Name'.")
    verification = (null_if_unset(row.get("Verification")) or "").lower()
    verified = verification.startswith("verified")
    return RegistryContact(
        contact_id=_contact_id(target_id, email=None, name=name),
        target_id=target_id,
        full_name=name,
        email=None,
        phone=None,
        job_role=null_if_unset(row.get("Title")),
        linkedin=None,
        verified=verified,
        source=source,
        imported_on=imported_on,
    )
