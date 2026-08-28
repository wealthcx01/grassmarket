"""Load curated display names for registry targets (GRS-0238 / founder decision D8).

    uv run python scripts/load_curated_target_names.py <csv>            # dry run
    uv run python scripts/load_curated_target_names.py <csv> --execute

CSV columns: `stem, domain, contacts, real_company_name, confidence, basis`. A row with no name, or
a confidence that is not `high` or `medium`, is SKIPPED and reported — an override exists to remove
doubt, and one that carries doubt is worse than the raw stem, because the stem at least looks wrong.

Writes to `registry_target_name_overrides`, never to `registry_targets`: an importer upserts targets
by id, so a curated name written onto the row would be wiped by the next import. This is the whole
reason the table is separate.

Idempotent — re-running updates in place rather than duplicating.
"""

from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime

from sqlalchemy import select

from grassmarket.config import get_settings
from grassmarket.data.database import make_engine, make_session_factory
from grassmarket.data.models import RegistryTargetNameOverrideORM, RegistryTargetORM

ACCEPTED = {"high", "medium"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--set-by", default="claude-curated-2026-08")
    args = parser.parse_args()

    with open(args.csv_path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    session = make_session_factory(make_engine(get_settings().database_url))()
    try:
        # Match on the imported NAME, because the CSV was generated from it. Only roster rows are
        # candidates: a curated name for a correctly-named target would be a rename, not a repair.
        by_name = {
            r.name: r.target_id
            for r in session.execute(
                select(RegistryTargetORM).where(RegistryTargetORM.source == "lseg-roster")
            ).scalars()
        }

        planned, skipped, unmatched = [], [], []
        for row in rows:
            name = (row.get("real_company_name") or "").strip()
            confidence = (row.get("confidence") or "").strip().lower()
            stem = (row.get("stem") or "").strip()
            if not name or confidence not in ACCEPTED:
                skipped.append((stem, confidence or "no-name"))
                continue
            target_id = by_name.get(stem)
            if target_id is None:
                unmatched.append(stem)
                continue
            planned.append((target_id, stem, name, confidence, (row.get("basis") or "").strip()))

        print(f"{len(planned)} override(s) to write")
        for _, stem, name, confidence, _ in planned[:10]:
            print(f"   {stem:<24} -> {name}  ({confidence})")
        if len(planned) > 10:
            print(f"   … and {len(planned) - 10} more")
        if skipped:
            print(
                f"\nskipped {len(skipped)} (no name or unusable confidence): "
                f"{', '.join(s for s, _ in skipped)}"
            )
        if unmatched:
            print(f"\nNOT FOUND in the registry ({len(unmatched)}): {', '.join(unmatched)}")

        if not args.execute:
            print("\nDry run. Re-run with --execute to write.")
            return 0

        now = datetime.now(UTC)
        for target_id, _stem, name, confidence, basis in planned:
            existing = session.get(RegistryTargetNameOverrideORM, target_id)
            if existing is not None:
                existing.display_name, existing.confidence = name, confidence
                existing.basis, existing.set_by, existing.set_on = basis, args.set_by, now
            else:
                session.add(
                    RegistryTargetNameOverrideORM(
                        target_id=target_id,
                        display_name=name,
                        confidence=confidence,
                        basis=basis,
                        set_by=args.set_by,
                        set_on=now,
                    )
                )
        session.commit()
        print(f"\nWrote {len(planned)} override(s).")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
