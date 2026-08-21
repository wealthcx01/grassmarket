"""Remove engagements whose linked assessments no longer exist (ADR-0048, GRS-0241).

Founder-authorised, one-off. Prints what it would delete and exits; deleting needs `--execute`.

    uv run python scripts/cleanup_orphaned_engagements.py --owner advisor@bruntsfieldcapital.com
    uv run python scripts/cleanup_orphaned_engagements.py --owner ... --execute

**Why this exists separately from `staging_cleanup_grs0241.py`.** That script removes duplicate
*non-production* engagements. These rows are marked `production` — not because anyone believes they
are real client work, but because their assessments were deleted (by the GRS-0177 cleanup) and so
nothing can be derived about them. ADR-0047 forbids deleting a production record and no argument
relaxes that, which is correct and which left five rows nobody wants and nothing may remove.

The criterion here is therefore **orphan-hood, not provenance**: an engagement whose every linked
assessment resolves to no row, which produced no deliverable and holds no conversation. That is a
referential fact the database can answer rather than a guess about what a record was for. Marking
these rows non-production so the ordinary tool would take them was rejected: it would fabricate a
provenance record to obtain a deletion.

Every condition is enforced in `Repository.delete_orphaned_engagement`, not here — a guard a script
can forget to apply is not a guard.
"""

from __future__ import annotations

import argparse
import sys
from uuid import UUID

from grassmarket.config import get_settings
from grassmarket.data.database import make_engine, make_session_factory
from grassmarket.data.models import AssessmentORM
from grassmarket.data.repository import Principal, Repository


def find_orphans(repo: Repository, principal: Principal) -> list[tuple[UUID, str, int]]:
    """(id, title, dangling link count) for each engagement whose every link is dead."""
    orphans: list[tuple[UUID, str, int]] = []
    for engagement in repo.list_engagements(principal):
        linked = list(engagement.assessment_ids)
        if not linked:
            continue
        if any(repo._session.get(AssessmentORM, a) is not None for a in linked):
            continue
        if engagement.deliverables or engagement.comms_log:
            continue
        orphans.append((engagement.id, engagement.title, len(linked)))
    return orphans


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    session_factory = make_session_factory(make_engine(get_settings().database_url))
    session = session_factory()
    try:
        repo = Repository(session)
        stored = repo.get_consultant_by_email(args.owner)
        if stored is None:
            print(f"No consultant with email {args.owner!r}.", file=sys.stderr)
            return 2
        principal = Principal(consultant_id=stored.id, role=stored.role)

        orphans = find_orphans(repo, principal)
        if not orphans:
            print("No orphaned engagements found.")
            return 0

        print(f"{len(orphans)} orphaned engagement(s) — every linked assessment deleted:\n")
        for engagement_id, title, dangling in orphans:
            print(f"  {title:<40} {dangling} dangling link(s)   {engagement_id}")
        print()

        if not args.execute:
            print("Dry run. Re-run with --execute to delete the rows listed above.")
            return 0

        deleted = 0
        for engagement_id, title, _ in orphans:
            # `founder_authorised` is passed explicitly at the one call site that has it, so the
            # authorisation is visible in the diff rather than buried in a default.
            repo.delete_orphaned_engagement(principal, engagement_id, founder_authorised=True)
            print(f"  deleted {title}")
            deleted += 1
        session.commit()
        print(f"\nDeleted {deleted} orphaned engagement(s).")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
