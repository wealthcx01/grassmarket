# GRS-0194 — LSEG influencer maps via bcap-lseg

**Status:** Planned (2026-07-23, founder feedback item 16b). **Priority:** MED-HIGH.
**Loop:** founder-feedback remediation, Wave 5. Elevates the planned GRS-0114; depends on
GRS-0193 (registry) and GRS-0200 (the seed dataset pulled 2026-07-23).

## Why

The Barclays Live exercise proved the method: LSEG/I-B-E-S contributor records reconstruct a
bank's research organisation into a ranked influence map with a named path to the platform
owner. The founder wants this repeatable for any corporate bank or brokerage target. The first
network-wide dataset was pulled on 2026-07-23 (GRS-0200), which also settled the method's
mechanics against the live field catalogue.

## Method facts (verified against the live bcap-lseg connector, 2026-07-23)

- The analyst roster fields exist and return multi-row rosters per RIC:
  `TR.AnalystName`, `TR.AnalystEmail`, `TR.AnalystPhone`, `TR.AnalystJobRole`,
  `TR.AnalystCtbID` (integer contributor/broker code — the per-bank grouping key),
  `TR.AnalystUID`, `TR.AnalystCreateDate` (tenure signal), and the StarMine-style
  `TR.OverallAnalystEstimateRating` / `TR.OverallAnalystRecommendationRatingT24M`
  (1–100 influence-ranking signals the original Barclays workbook did not have).
- There is **no contributor-name field** in the catalogue: the contributor ID → institution
  mapping is inferred from the dominant analyst e-mail domain per `ctb_id` (e.g. 10333 →
  barclays.com) and curated once in the registry — a one-time mapping table, maintained as
  data.
- Cells return as a flat (ric, field, value) list in analyst order; rows are reconstructed by
  grouping per (ric, field) and zipping index-wise. `<NA>` means unset, never zero.

## Scope

1. **Generator service** (backend, operator/admin-triggered): given a target institution with a
   known `ctb_id`, select a ticker sample (default: the GRS-0200 basket filtered to tickers the
   contributor covers; override per run), pull the roster fields via bcap-lseg, filter to the
   contributor, and rank analysts: coverage breadth in the sample, then the rating fields,
   then tenure. Output the 3-tab influencer-map artifact (Influencer Map / Target Owners /
   Raw Data — the Barclays workbook shape) attached to the prospect/target record with run
   provenance (date, sample, connector version).
2. **Target Owners tab is explicitly two-source:** LSEG gives the analyst layer; the
   ownership/leadership layer (the Rogoff/Rouse equivalents) is web-verified by a human and
   entered with verification status. Unverified rows render flagged, never as verified.
3. **Compliance posture in-product:** every generated map carries the standing caveat —
   communications to sell-side research are compliance-logged; a warm referral beats a cold
   email — rendered on the artifact itself.
4. **No scheduled mass pulls:** each run is operator-triggered and recorded. Rate behaviour
   respects the connector's own batching (15-RIC batches, inter-batch sleep).

## Test plan

- Fixture-driven tests for the cell-parsing (grouping, zipping, `<NA>`, unequal-count
  padding fail-loud), contributor filtering, ranking order, and the two-source verification
  flags. No live LSEG calls in CI.
- Scoping: maps attach to targets/prospects under the ADR-0045 rules; a non-admin cannot
  trigger a pull.

## Out of scope

- The registry itself and the bulk seed dataset (GRS-0193, GRS-0200). Outreach automation
  (GRS-0195's spike decides that separately).

## Acceptance

Running the generator for a seeded target with a curated `ctb_id` produces the 3-tab artifact
with provenance, rankings, caveats, and verification flags, reproducing the Barclays workbook
shape from live data.
