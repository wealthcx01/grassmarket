"""GTM target & contact registry ingest (GRS-0193, ADR-0045).

The parsing layer is deliberately separate from the scripts that read files: every function here
maps already-read rows to contracts and can be tested offline with rows built in code, which is
what keeps the imported PII out of the test fixtures (§7). `scripts/import_*.py` are thin readers
that call into this module and print the summary it returns.
"""

from grassmarket.gtm.influencer_map import (
    ROSTER_FIELDS,
    LsegCell,
    LsegRosterSource,
    generate_influencer_map,
    owners_from_registry,
    rank_analysts,
    reconstruct_rows,
)
from grassmarket.gtm.ingest import (
    ImportSummary,
    RowError,
    decode_lseg_rating,
    null_if_unset,
    parse_advisor_market_row,
    parse_bank_row,
    parse_barclays_analyst_row,
    parse_barclays_owner_row,
    parse_lseg_roster,
    parse_supplier_row,
    slugify,
)

__all__ = [
    "ROSTER_FIELDS",
    "ImportSummary",
    "LsegCell",
    "LsegRosterSource",
    "RowError",
    "decode_lseg_rating",
    "null_if_unset",
    "parse_advisor_market_row",
    "parse_bank_row",
    "parse_barclays_analyst_row",
    "parse_barclays_owner_row",
    "parse_lseg_roster",
    "parse_supplier_row",
    "generate_influencer_map",
    "owners_from_registry",
    "rank_analysts",
    "reconstruct_rows",
    "slugify",
]
