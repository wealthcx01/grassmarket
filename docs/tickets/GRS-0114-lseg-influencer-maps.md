# GRS-0114 — LSEG influencer mapping (bcap-lseg)

**Status:** Planned
**Loop:** Part 2 — Pipeline / GTM engine (one program)
**Depends on:** ADR-0027 (Pipeline / GTM engine)

## Why

The differentiator of the GTM engine is warm-intro intelligence: for a target bank/platform, surface
the analysts/influencers who cover the relevant stocks and want retail flow, plus the suggested path to
the real product owner. The key concept is that **LSEG surfaces influencers, not the digital product
owners** — the Barclays worked example (`barclays_live_influencer_map.xlsx` +
`barclays_live_influencer_brief.md`) shows analysts ranked Tier 1–3 by proximity to the platform owner
(Barclays Live is Research-owned; chain analyst → Rob Rouse → Brad Rogoff), and that Barclays Live ≠
Smart Investor. This is **greenfield — EliteVault's "LSEG" is a client-billing page, not a market-data
feed; there is nothing to port.** It uses the existing `bcap-lseg` MCP connector.

## What to build

- Per-target **influencer maps** in-app: for a given bank/platform, surface the analysts/influencers
  from LSEG contributor data who cover relevant stocks, plus the suggested warm-intro path to the real
  owner, preserving the **influencer ≠ owner** distinction (Barclays Live vs Smart Investor).
- Implement the guide's method: **`TR.Analyst*` fields keyed by ticker → filter by the brokerage's
  contributor ID → dedup into an org chart**, with a **web overlay** for the actual digital-product
  owners. Rank analysts Tier 1–3 by proximity to the owner as in the Barclays example.
- Data source: the existing **`bcap-lseg` MCP connector** (no new market-data plumbing).
- Deliverable shape mirrors the Barclays workbook's **3 tabs**: Influencer Map · Target Owners ·
  LSEG Raw Data.

## Acceptance / verification

- For a target with a known ticker, the influencer map returns analysts filtered by contributor ID,
  deduped into an org chart, with a suggested warm-intro path to the owner.
- The map keeps the influencer ≠ owner distinction (analysts are door-openers, not the product owner).
- Output is presentable in the 3-tab shape (Influencer Map · Target Owners · LSEG Raw Data), sourced
  via the `bcap-lseg` connector.

## Not in scope

- Bulk seeding the 150-bank universe (GRS-0115 — depends on this).
- The CRM rebuild (GRS-0111), Google integration (GRS-0112), and GTM MCP surface (GRS-0113).
