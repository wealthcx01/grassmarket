"""Import the List of Banks into the GTM registry (GRS-0193).

    uv run python scripts/import_bank_list.py data/gtm/sources/list-of-banks.xlsx

Targets only: the bank list is `Country, Company` and carries no contacts, so nothing is invented
to fill that gap.
"""

from __future__ import annotations

import sys

from _gtm_import import import_date, read_xlsx_rows, resolve_path, run

from grassmarket.data.repository import Repository
from grassmarket.gtm import ImportSummary, parse_bank_row


def main() -> None:
    path = resolve_path(sys.argv, env_var="GTM_BANKS_XLSX", what="list-of-banks.xlsx")
    on = import_date()

    def build(repo: Repository) -> ImportSummary:
        summary = ImportSummary(source="list-of-banks")
        for row in read_xlsx_rows(path):
            summary.rows_read += 1
            if not any(v is not None for v in row.values()):
                summary.skip("blank row")
                continue
            repo.upsert_registry_target(parse_bank_row(row, imported_on=on))
            summary.targets_upserted += 1
        return summary

    run(build)


if __name__ == "__main__":
    main()
