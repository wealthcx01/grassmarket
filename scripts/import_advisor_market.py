"""Import the curated advisor-market list into the GTM registry (GRS-0210).

    uv run python scripts/import_advisor_market.py data/gtm/sources/advisor-market.csv

The wealth managers, retail brokers, exchanges and vendors an advisor at this firm actually types.
Typed by hand once and committed, because the imported bank and supplier lists covered 42% of those
names and 4% of wealth managers — a gap in the corpus, not in the matching.

Targets only: the list carries no contacts, so nothing is invented to fill that gap.
"""

from __future__ import annotations

import csv
import sys

from _gtm_import import import_date, resolve_path, run

from grassmarket.data.repository import Repository
from grassmarket.gtm import ImportSummary, parse_advisor_market_row


def main() -> None:
    path = resolve_path(sys.argv, env_var="GTM_ADVISOR_MARKET_CSV", what="advisor-market.csv")
    on = import_date()

    def build(repo: Repository) -> ImportSummary:
        targets = 0
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                repo.upsert_registry_target(parse_advisor_market_row(row, imported_on=on))
                targets += 1
        return ImportSummary(source="advisor-market", targets=targets, contacts=0)

    run(build)


if __name__ == "__main__":
    main()
