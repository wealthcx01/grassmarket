# GRS-0238 — A Prospecting surface: browse the registry we imported

**Status:** OPEN (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-31, founder: "I can't see prospective clients from our bcap database")._
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

**OPEN.** Scheduled in the GRS-0229–0245 wave (see docs/BACKLOG.md for the build order).
