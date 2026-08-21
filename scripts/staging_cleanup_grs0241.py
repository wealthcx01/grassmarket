"""Remove duplicate NON-PRODUCTION engagements (GRS-0241 scope 1).

The founder asked twice — 23/07 and 31/07 — for the duplicate demo rows on the Engagements page to
go. This is the tool that does it, and like `staging_cleanup_grs0177.py` it prints what it would
delete and exits; deleting needs an explicit `--execute`.

    uv run python scripts/staging_cleanup_grs0241.py --owner advisor@bruntsfield.capital
    uv run python scripts/staging_cleanup_grs0241.py --owner advisor@bruntsfield.capital --execute

**It cannot delete a production engagement.** Not by policy — by construction: the candidate query
filters on `provenance != production` before anything else, and each candidate is re-checked
immediately before deletion. ADR-0047's rule is that a production record is never deletable through
any path, and an engagement only gained a provenance column in GRS-0241, so rows created before that
migration are `production` and are therefore untouchable here. That is correct rather than
inconvenient: we cannot retroactively prove a historical row was demo data, and guessing is exactly
what ADR-0047 exists to prevent.

**What counts as a duplicate:** same owner, same prospect, same title, both non-production. Of each
group the SURVIVOR is the one with the most attached work (deliverables, then linked assessments,
then communications, then oldest) — so if the two rows are not really identical, the one carrying
something is the one that stays.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from bcap_contracts.assessments import RecordProvenance

from grassmarket.config import get_settings
from grassmarket.data.database import make_engine, make_session_factory
from grassmarket.data.repository import Principal, Repository


@dataclass(frozen=True)
class Duplicate:
    engagement_id: UUID
    title: str
    provenance: str
    deliverables: int
    assessments: int
    comms: int

    def describe(self) -> str:
        return (
            f"  {self.title:<44} {self.provenance:<10} "
            f"{self.deliverables} deliverables, {self.assessments} assessments, "
            f"{self.comms} comms   {self.engagement_id}"
        )


def _rank(engagement) -> tuple[int, int, int, str]:
    """Sort key: most work first, then oldest. The survivor is `max` of this.

    Ordering by attached work rather than by date is deliberate. Two rows that look identical in the
    list may not be — if one has a deliverable on it, deleting that one loses real output, and the
    'obvious' rule of keeping the oldest would sometimes do exactly that.
    """
    return (
        len(engagement.deliverables),
        len(engagement.assessment_ids),
        len(engagement.comms_log),
        # Negated via string comparison at the caller; created_at ascending means oldest wins ties.
        engagement.created_at.isoformat(),
    )


def find_duplicates(repo: Repository, principal: Principal) -> list[tuple[str, list[Duplicate]]]:
    """Groups of non-production engagements that share an owner, a prospect and a title."""
    groups: dict[tuple[UUID, str], list] = defaultdict(list)
    for engagement in repo.list_engagements(principal):
        # THE filter. Everything downstream operates on a list that cannot contain a production row.
        if engagement.provenance is RecordProvenance.PRODUCTION:
            continue
        groups[(engagement.prospect_id, engagement.title.strip().casefold())].append(engagement)

    doomed: list[tuple[str, list[Duplicate]]] = []
    for (_, _key), members in sorted(groups.items(), key=lambda kv: str(kv[0])):
        if len(members) < 2:
            continue
        survivor = max(members, key=_rank)
        losers = [m for m in members if m.id != survivor.id]
        doomed.append(
            (
                f"{survivor.title}  (keeping {survivor.id}, "
                f"{len(survivor.deliverables)} deliverables)",
                [
                    Duplicate(
                        engagement_id=m.id,
                        title=m.title,
                        provenance=m.provenance.value,
                        deliverables=len(m.deliverables),
                        assessments=len(m.assessment_ids),
                        comms=len(m.comms_log),
                    )
                    for m in losers
                ],
            )
        )
    return doomed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", required=True, help="Email of the consultant who owns the rows.")
    parser.add_argument(
        "--execute", action="store_true", help="Actually delete. Without this, prints and exits."
    )
    args = parser.parse_args()

    settings = get_settings()
    session_factory = make_session_factory(make_engine(settings.database_url))
    session = session_factory()
    try:
        repo = Repository(session)
        stored = repo.get_consultant_by_email(args.owner)
        if stored is None:
            print(f"No consultant with email {args.owner!r}.", file=sys.stderr)
            return 2
        principal = Principal(consultant_id=stored.id, role=stored.role)

        groups = find_duplicates(repo, principal)
        if not groups:
            print("No duplicate non-production engagements found.")
            return 0

        total = sum(len(losers) for _, losers in groups)
        print(f"{total} duplicate non-production engagement(s) in {len(groups)} group(s):\n")
        for heading, losers in groups:
            print(f"{heading}")
            for loser in losers:
                print(loser.describe())
            print()

        if not args.execute:
            print("Dry run. Re-run with --execute to delete the rows listed above.")
            return 0

        deleted = 0
        for _heading, losers in groups:
            for loser in losers:
                # Re-checked immediately before deletion rather than trusting the earlier filter.
                # Cheap, and it means a bug in the grouping cannot become a deleted client record.
                current = repo.get_engagement(principal, loser.engagement_id)
                if current.provenance is RecordProvenance.PRODUCTION:
                    print(f"  REFUSED (production): {loser.engagement_id}", file=sys.stderr)
                    continue
                repo.delete_engagement(principal, loser.engagement_id)
                deleted += 1
        session.commit()
        print(f"Deleted {deleted} duplicate engagement(s).")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    os.environ.setdefault("GM_ENV", "staging")
    raise SystemExit(main())
