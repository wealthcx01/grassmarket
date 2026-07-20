# GRS-0153 — Wizard number legibility: P10/P50/P90 band labels + inline metric-domain validation

**Status:** Done (2026-07-20). From the mock-advisor re-measure (Elena/Deutsche Börse, quant lens) + UX audit.
**Loop:** Part 2 — trust. Frontend-only (backend already serves the data).

## Why

1. **The uncertainty band was shown unlabeled** — `58.3 (45.2–67.8)` with nothing marking the bounds
   as percentiles. Elena (a market-risk professional): *"a quant can't tell if the bounds are P10/P90,
   P5/P95, or ±1σ."* The honesty machinery (point-vs-range) was right; the labelling wasn't.
2. **Metric values outside their domain saved silently** — Elena entered ADV = −500 and a 12-digit
   value; both saved ("all changes saved") with no field feedback. The backend domain check
   (`min_raw`/`max_raw`, GRS-0144) exists but only fires as a *score-time* blocker, so a nonsensical
   value isn't caught at entry.

## What shipped

- **P10/P50/P90 labels on the band.** `BandDisplay` now labels the range: the bold figure is the P50
  (median), the parenthesised pair is the P10–P90 range, with a `title` and a small "P50 · P10–P90"
  caption. (low/mid/high already mapped to p10/p50/p90 — this only labels them.)
- **Inline metric-domain validation.** `RegistryMetric` now carries `min_raw`/`max_raw` (already
  serialized by `GET /registry` via the Pydantic model); the Business-Metrics input sets `min`/`max`,
  flags `aria-invalid` + a red border, and shows an inline `role="alert"` error mirroring the backend
  `domain_violation` copy — so an impossible value is caught at ENTRY, not only at score time.

Frontend type-check + lint + BandDisplay/LiveSummary vitest green. No backend change.
