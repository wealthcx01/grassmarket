# GRS-0200 — LSEG influencer dataset: the first network-wide pull

**Status:** Done — dataset produced (2026-07-23, founder feedback item 16). **Priority:** HIGH
within Wave 5 (it unblocks GRS-0193/0194). **Loop:** founder-feedback remediation, Wave 5.
Under ADR-0045. The ingest of this dataset into the product is GRS-0193; the per-target map
generator is GRS-0194. This ticket records the pull itself.

## Why

The founder asked to "use bcap lseg now to populate the database we need for the influencer
mapping per corporate bank and/or brokerage". This ticket is that pull: the first network-wide
extraction of sell-side research analyst rosters from LSEG/I-B-E-S, which both produces the seed
dataset and settles the method's mechanics against the live field catalogue so GRS-0194 can
productise it with no unknowns.

## What was done

- **Connector:** bcap-lseg MCP over LSEG Workspace (SDK 2.1.1), session confirmed connected.
- **Universe:** 54 RICs spanning the three wealth-platform segments plus the TMT coverage names
  the influencer method keys off — US TMT megacaps, US and UK/EU banks and brokerages, and the
  listed exchanges/market-infrastructure names (ICE, CME, NDAQ, LSEG, DB1, ENX, MKTX, TW).
- **Fields (nine per call, verified live):** `TR.AnalystName`, `TR.AnalystEmail`,
  `TR.AnalystPhone`, `TR.AnalystJobRole`, `TR.AnalystCtbID`, `TR.AnalystUID`,
  `TR.AnalystCreateDate`, `TR.OverallAnalystEstimateRating`,
  `TR.OverallAnalystRecommendationRatingT24M`.
- **Result:** 1,754 analyst rows (1,443 named; 1,266 with email, 1,188 with phone), 53 RICs
  succeeded, 1 failed honestly (AJB.L / AJ Bell — no analyst-coverage rows), 134 distinct
  contributor codes. Contributor 10333 resolved to Barclays with 50 rows, matching the Barclays
  Live influencer brief and validating the method end to end.
- **Deliverables (OneDrive `Business/Advisory/GTM Data/lseg-influencer-pull-2026-07-23/`, never
  the repo — PII policy):** `analysts_unified.csv`, `contributor_institution_map.csv`,
  `pull_summary_unified.json`, a `README.md` documenting provenance and caveats, and the raw
  per-shard files.

## Method facts settled for GRS-0194 (do not rediscover)

1. The analyst roster fields return multi-row rosters per RIC; cells come back as a flat
   (ric, field, value) list in analyst order, reconstructed by grouping per (ric, field) and
   zipping index-wise. `<NA>`/`NaT` mean unset, never zero.
2. **No contributor-NAME field exists.** Institution is inferred from the dominant analyst
   email domain per `ctb_id`. Clean for the big houses, noisy for a few — so the
   contributor→institution map is a curated table (this pull seeds its first draft), not a
   live lookup.
3. `TR.OverallAnalystRecommendationRatingT24M` returns epoch-nanosecond-encoded
   (`1970-01-01 00:00:00.000000054` = 54); decode to the trailing integer on ingest.
4. 311 anonymous contributor slots (blank identity, populated ratings) must be filtered on
   non-blank `analyst_name` for any outreach use.
5. Batch at 3-15 RICs with the connector's own inter-batch sleep; one RIC failing never aborts
   the run.

## Out of scope

- Importing this into the product database (GRS-0193) and the per-target map generator
  (GRS-0194) — both consume these files. Curating the contributor→institution map beyond the
  first-pass inference (a data task tracked under GRS-0193).

## Acceptance

Met: the unified dataset, the first-draft contributor map, and the provenance README exist in
the GTM Data estate; the numbers and caveats are recorded here and in the README; the Barclays
validation confirms the roster→institution method. No PII entered the repo.
