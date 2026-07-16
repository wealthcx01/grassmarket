# GRS-0115 — Seed the target universe

**Status:** Planned
**Loop:** Part 2 — Pipeline / GTM engine (one program)
**Depends on:** ADR-0027 (Pipeline / GTM engine); GRS-0114 (LSEG influencer mapping)

## Why

For advisers to start prospecting on day one, the pipeline should ship pre-populated with a real target
universe rather than an empty board. The founder provided **`List of Banks.xlsx`** — 150 target banks
(Country, Company; roughly 50 each APAC / EU / US) — as the seed prospect universe. This ticket loads
those 150 banks as prospects and batch-prepopulates their influencer maps via the `bcap-lseg`
connector, applying the same Barclays-example method as GRS-0114. This is **greenfield — EliteVault has
nothing to port here.** It depends on GRS-0114 for the mapping mechanism.

## What to build

- A seed loader that imports the **150 banks** from `List of Banks.xlsx` (Country, Company) as
  first-class Company + Contact prospects (per GRS-0111's entity model), owner-scoped appropriately.
- **Batch-prepopulate influencer maps** for the seeded targets via the `bcap-lseg` connector, reusing
  GRS-0114's method (`TR.Analyst*` keyed by ticker → filter by contributor ID → dedup into an org
  chart + web overlay) — not a re-implementation.
- Keep the source workbook reference-only / not committed as client data; seed through scoped storage.

## Acceptance / verification

- Running the seed loads all 150 banks as prospects with Country + Company populated.
- Seeded targets carry batch-generated influencer maps produced through GRS-0114's mechanism.
- The seed is idempotent and owner-scoped; no client workbook is committed to the repo.

## Not in scope

- The influencer-mapping mechanism itself (GRS-0114).
- The CRM rebuild (GRS-0111), Google integration (GRS-0112), and GTM MCP surface (GRS-0113).
