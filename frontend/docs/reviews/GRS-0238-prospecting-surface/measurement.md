# GRS-0238 — what the registry actually contains

Measured 2026-08-19 by running all four committed importers into a scratch SQLite database from the
sources in `data/gtm/`. Reproduce:

```
GM_DATABASE_URL="sqlite:///$SCRATCH/gtm.db" uv run alembic upgrade head
GM_DATABASE_URL="sqlite:///$SCRATCH/gtm.db" uv run python scripts/import_bank_list.py data/gtm/sources/list-of-banks.xlsx
GM_DATABASE_URL="sqlite:///$SCRATCH/gtm.db" uv run python scripts/import_exchange_suppliers.py data/gtm/sources/exchange-supplier-list.xlsx
GM_DATABASE_URL="sqlite:///$SCRATCH/gtm.db" uv run python scripts/import_barclays_influencer.py data/gtm/sources/barclays-influencer-map.xlsx
GM_DATABASE_URL="sqlite:///$SCRATCH/gtm.db" uv run python scripts/import_lseg_rosters.py data/gtm/lseg/analysts_unified.csv
```

## Scale — the ticket overstates what is browsable

The ticket says "150 banks, 1,001 exchange suppliers, 1,754 sell-side analysts". Those are **source
rows**, not registry rows.

| | Source rows | Registry targets |
|---|---|---|
| list-of-banks | 150 | 149 |
| exchange-supplier-list | 1,001 | 307 (many rows per supplier) |
| lseg-roster | 1,754 analysts | 128 institutions + 487 contacts |
| barclays-influencer-map | — | 1 |
| **Total** | | **584 targets, 530 contacts** |

584 is a real universe worth a page. It is not 2,900, and the page should not imply it is.

## The `segment` column holds two different kinds of thing

15 distinct values across the four sources:

| Value | Count | Kind |
|---|---|---|
| Bank | 149 | firm type |
| Data | 144 | content type |
| Sell-side research | 128 | firm type |
| News | 50 | content type |
| Indices | 29 | content type |
| Data and Indices | 28 | content type |
| Fixings | 13 | content type |
| Fixed Income T&Cs | 11 | content type |
| Exchange supplier | 11 | firm type |
| Reference Data | 7 | content type |
| Funds | 6 | content type |
| Ratings | 5 | content type |
| IDB / CORAX / Broker content -IDB | 1 each | content type |

"Bank" says what a firm **is**. "Indices" says what a supplier **supplies**. They share a column
because two importers filled it from two different spreadsheet fields — `exchange-supplier-list`
uses its "Content Type" column, the bank and roster importers write a literal. The filter groups
them by kind rather than listing them flat.

Note `CORAX` and `Eikon App` are LSEG **product** names that reached a sector column. They are
labelled as content types rather than dressed up as segments.

## The duplicate problem, and its real cause

The founder saw "Barclays [BANK]" and "barclays [SELL-SIDE RESEARCH]". Confirmed — **9 duplicate
name groups**, 8 of them case-duplicates.

The cause is upstream of the merge the ticket proposes. `data/gtm/lseg/contributor_institution_map.csv`
has an `inferred_institution` column holding **the stem of the domain**, not the firm name:

```
ctb_id,inferred_domain,inferred_institution,analyst_rows
10333,barclays.com,barclays,50
6,gs.com,gs,48
138,jefferies.com,jefferies,48
```

**124 of 129 are all-lowercase.** So the roster does not merely mis-case names — it never had them.

### Only 8 of 128 are fixable by merging

| | Count |
|---|---|
| roster institutions | 128 |
| match a bank-list firm by name (case-insensitive) | **8** |
| match by domain only | 0 |
| **no counterpart at all** | **120** |

The 120 orphans include unreadable stems: `gs`, `db`, `citi`, `bofa`, `bmo`, `clsa`, `htsc`, `zkb`
— and from clearly broken source rows, `uk`, `us`, `hk`.

**This is why the page marks rather than merges.** Resolving `gs` → "Goldman Sachs" is a guess, and
a guess written into the database is indistinguishable from a fact afterwards (non-negotiable #3).
The rows are shown with a `name unverified` badge; curating them is founder work, not engineering.

## Migration result, on the real data

`0038_prospect_registry_link` run against the fully imported scratch database:

| | Before | After |
|---|---|---|
| targets | 584 | **576** |
| contacts | 530 | **530** (none lost) |
| duplicate name groups | 9 | **1** |

The surviving group is the one it should refuse:

```
Stock Exchange of Thailand [Bank] <list-of-banks>  |  Stock Exchange of Thailand [Indices] <exchange-supplier-list>
```

Both names are properly cased, so no "readable survivor" can be chosen without guessing which row
is the real firm — the ticket's refuse-loud requirement working as specified. (`Barclays Capital`
is correctly left as its own target: a different name, plausibly a different entity.)
