# GRS-0238 — A Prospecting surface: browse the registry we imported

**Status:** DONE (2026-08-19). _Previously recorded as: Planned (2026-07-31, founder: "I can't see prospective clients from our bcap database")._
**Priority:** HIGH. **Loop:** first-time-user coherence. **Depends on:** GRS-0193.
**Relates to:** GRS-0194, GRS-0199, GRS-0207, GRS-0210, ADR-0045.

## Why

GRS-0193/0194 imported the universe — 150 banks, 1,001 exchange suppliers, 1,754 sell-side analysts
with contact details — and the only ways to reach any of it are (a) typing a name you already know
into entity search (max 8 results, query required), or (b) a per-prospect panel that requires an
exact lowercase name match after the prospect already exists. There is no page where an advisor can
*see* the prospective clients the network holds. The founder has now said so twice.

Also observed while testing search: typing "Barclays" offers "Barclays [BANK]", "barclays
[SELL-SIDE RESEARCH]" and "Barclays Capital [INDICES]" — a case-duplicate of the same firm from two
import sources, badged with raw source-category strings an advisor cannot interpret or choose
between.

## Scope

1. **Backend: list and filter.** `list_registry_targets(segment?, country?, q?, offset, limit)` on
   the repository plus `GET /entities` (paginated). Network-shared read per ADR-0045 §2 — no owner
   filter on targets; contacts stay behind the existing per-target endpoint. Include per-target
   contact count and, joined per-principal, whether *this* advisor already has a prospect claiming
   the target (prospects are owner-scoped; the join is per-principal by construction).
2. **Frontend: a Prospecting page.** Reachable from Pipeline ("Find your next prospect") and the
   nav. Segment and country filters mapping the stored columns; search; provenance shown per
   ADR-0045 (source, imported_on, verified flags on contacts); a **Create prospect** action that
   posts the target into the existing pipeline create flow and links the registry id.
3. **Human labels for source categories.** "BANK" / "SELL-SIDE RESEARCH" / "INDICES" become a
   mapping to advisor-meaningful labels ("Retail & commercial bank", "Sell-side research house",
   "Index provider"), owned as data beside the import definitions.
4. **Dedupe on import identity.** Case-insensitive name+domain merge at upsert so "Barclays" and
   "barclays" become one target with two sources recorded; a one-off merge migration for rows
   already imported. Refuse-loud on ambiguous merges (different domains, same name) — list them in
   the import summary rather than guessing.
5. **Not a CRM.** No outreach, no sequencing, no editing contacts from this surface — GRS-0207
   decides the CRM/outreach layer and GRS-0202–0204 hold the send path. This page is read →
   claim-as-prospect only, so it cannot pre-empt that decision.

## Test plan

1. Repository tests: pagination, filters, contact counts; scoping test proving targets are
   network-readable while the my-prospect join is per-principal (the scoping suite pattern).
2. Import dedupe tests: case-duplicate merges, ambiguous pair refuses and reports.
3. Vitest: filter interaction, provenance display, create-prospect handoff.
4. Manual: screenshot the page filtered to Banks, and the Barclays row now singular, in the PR.
5. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- Outreach/CRM platform (GRS-0207) and send paths (GRS-0202–0204).
- Opportunity Radar wiring (GRS-0199).
- Influencer-map UI beyond the existing admin-only pull (GRS-0194).

## Acceptance

The founder opens Prospecting, filters to exchanges, sees the imported universe with contacts and
provenance, and claims one as a pipeline prospect — without typing a name they had to already know.

---

## Status reconciliation — 2026-08-01

**DONE** — shipped 2026-08-19, all five scopes. Full measurement in
`docs/reviews/GRS-0238-prospecting-surface/measurement.md`.

## What the measurement found before anything was built

All four importers were run into a scratch database from the committed sources, because the ticket's
figures are **source rows, not registry rows**:

| | Ticket says | Actually in the registry |
|---|---|---|
| banks | 150 | 149 |
| exchange suppliers | 1,001 | 307 (many rows per supplier) |
| sell-side analysts | 1,754 | 128 institutions + 487 contacts |
| **total** | ~2,900 | **584 targets, 530 contacts** |

584 is a real universe worth a page; it is not 2,900, and the page does not imply it is.

## What shipped

**1 — `GET /entities` and `GET /entities/facets`**, plus `list_registry_targets`,
`registry_segments`, `registry_countries` on the repository. Paginated, filtered by segment /
country / name substring, with contact counts joined.

**2 — `/prospecting`**, reachable from the primary nav. Filters, provenance per row (source +
import date), and a **Add to pipeline** action that creates the prospect with
`registry_target_id` set — a real link, not a name match. Migration `0038` adds the column.

**3 — Human labels, grouped by KIND.** The 15 observed segment values are mapped in
`bcap_contracts.prospecting`. An unmapped value is shown **verbatim** under "Unclassified" rather
than title-cased: the ugliness is the signal that a new source arrived without anyone labelling its
vocabulary, and prettifying it would produce something that reads curated and is not.

**4 — Dedupe migration**, verified on the fully imported data: 584 → 576 targets, 9 → 1 duplicate
groups, **530 → 530 contacts (none lost)**.

**5 — Not a CRM.** Read, filter, claim. No outreach, no sequencing, no contact editing.

## Where the ticket's diagnosis was incomplete

**The `segment` column is a category error, not just an unfriendly label.** "Bank" and "Sell-side
research" say what a firm **is**; "Data", "Indices", "Fixings", "CORAX" say what a supplier
**supplies**. They share a column because two importers filled it from two different spreadsheet
fields. Scope 3 asked for nicer names; listing them flat under nicer names would still tell an
advisor they are alternatives of one kind. They are grouped by kind instead.

**Scope 4's merge fixes 8 of 128 bad rows, and the root cause is upstream.** The ticket reads the
duplicates as a casing problem. They are not: `data/gtm/lseg/contributor_institution_map.csv` has an
`inferred_institution` column holding **the stem of the domain** — `barclays`, `gs`, `jefferies`,
`db` — and **124 of 129 are all-lowercase**. The roster never had firm names to mis-case.

| | Count |
|---|---|
| roster institutions | 128 |
| match a bank-list firm by name | **8** |
| match by domain only | 0 |
| **no counterpart at all** | **120** |

The 120 include `gs`, `db`, `citi`, `bofa`, `clsa`, `zkb`, and — from clearly broken source rows —
`uk`, `us`, `hk`.

## The decision that follows, and why

**Unverified names are MARKED, never replaced.** Resolving `gs` → "Goldman Sachs" from `gs.com` is a
guess, and a guess written into a field the pipeline reads is indistinguishable from a fact
afterwards (#3). The row shows the stem with a `name unverified` badge explaining where it came
from. Suppressing the rows was rejected too: their contacts are real, and hiding them would trade a
visible data-quality problem for an invisible gap.

**Curating those 120 names is founder work, not engineering.** It needs someone who knows the
market to confirm `htsc` is Huatai and `zkb` is Zürcher Kantonalbank. Flagged for the decision list.

## Not done

- **No screenshot in this PR.** The test plan asks for one of the page filtered to Banks. The
  registry is empty in every environment I can reach — the imports are operator-run and have not
  been run on staging — so a screenshot would show an empty table and prove nothing. The measurement
  document contains the real data instead, produced by running the importers locally. **Running the
  importers on staging is the next step to make this page demonstrable.**
- The 120 unresolved stems (above).
- Outreach/CRM (GRS-0207), send paths (GRS-0202–0204), Opportunity Radar (GRS-0199) — out of scope
  and deliberately not pre-empted.
