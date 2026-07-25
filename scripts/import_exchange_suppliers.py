"""Import the Exchange Supplier List into the GTM registry (GRS-0193).

    uv run python scripts/import_exchange_suppliers.py data/gtm/sources/exchange-supplier-list.xlsx

One target per supplier, plus a contact for every audited contact row. Idempotent: re-running
overwrites the same rows by id. Column names below are the workbook's own headers, kept here rather
than in the parsing layer so the mapping stays reviewable next to the file it describes.
"""

from __future__ import annotations

import sys

from _gtm_import import import_date, read_xlsx_rows, resolve_path, run

from grassmarket.data.repository import Repository
from grassmarket.gtm import ImportSummary, parse_supplier_row

SHEET = "Supplier List (Cleaned)"


def main() -> None:
    path = resolve_path(sys.argv, env_var="GTM_SUPPLIER_XLSX", what="exchange-supplier-list.xlsx")
    on = import_date()

    def build(repo: Repository) -> ImportSummary:
        summary = ImportSummary(source="exchange-supplier-list")
        # A supplier appears once per service it provides, so the same target is upserted several
        # times; that is the idempotence working, not duplication.
        for row in read_xlsx_rows(path, SHEET):
            summary.rows_read += 1
            if not any(v is not None for v in row.values()):
                summary.skip("blank row")
                continue
            target, contacts = parse_supplier_row(row, imported_on=on)
            repo.upsert_registry_target(target)
            summary.targets_upserted += 1
            for contact in contacts:
                repo.upsert_registry_contact(contact)
                summary.contacts_upserted += 1
            if not contacts:
                summary.skip(f"{target.name}: no audited contact name")
        return summary

    run(build)


if __name__ == "__main__":
    main()
