"""Import the LSEG/I-B-E-S analyst rosters into the GTM registry (GRS-0193, consuming GRS-0200).

    uv run python scripts/import_lseg_rosters.py data/gtm/lseg/analysts_unified.csv

The contributor-to-institution map is read from `contributor_institution_map.csv` beside the roster,
or from $GTM_LSEG_MAP_CSV. One target per contributor, one contact per named analyst. The three
GRS-0200 caveats (anonymous slots dropped, epoch-nanosecond ratings decoded, `<NA>` nulled) are
applied in `grassmarket.gtm.ingest`, where they are unit-tested.
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

from _gtm_import import import_date, resolve_path, run

from grassmarket.data.repository import Repository
from grassmarket.gtm import ImportSummary, parse_lseg_roster

MAP_FILENAME = "contributor_institution_map.csv"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _institution_map(roster_path: Path) -> dict[int, dict[str, str]]:
    override = os.environ.get("GTM_LSEG_MAP_CSV")
    map_path = Path(override) if override else roster_path.parent / MAP_FILENAME
    if not map_path.is_file():
        raise SystemExit(
            f"Contributor map not found at {map_path}. The roster cannot be attributed to "
            f"institutions without it (set GTM_LSEG_MAP_CSV to override)."
        )
    mapped: dict[int, dict[str, str]] = {}
    for row in _read_csv(map_path):
        raw = (row.get("ctb_id") or "").strip()
        if not raw:
            continue
        mapped[int(float(raw))] = row
    return mapped


def main() -> None:
    roster_path = resolve_path(sys.argv, env_var="GTM_LSEG_CSV", what="analysts_unified.csv")
    mapped = _institution_map(roster_path)
    on = import_date()

    def build(repo: Repository) -> ImportSummary:
        summary = ImportSummary(source="lseg-roster")
        targets, contacts = parse_lseg_roster(
            _read_csv(roster_path), mapped, imported_on=on, summary=summary
        )
        # Targets first: a contact whose institution is missing is refused by the repository.
        for target in targets:
            repo.upsert_registry_target(target)
            summary.targets_upserted += 1
        for contact in contacts:
            repo.upsert_registry_contact(contact)
            summary.contacts_upserted += 1
        return summary

    run(build)


if __name__ == "__main__":
    main()
