# GRS-0144 — Metric input-domain validation (fail-loud, no more silent clamp)

**Status:** Implemented (2026-07-19) — ADR-0035 Phase 1.
**Loop:** Part 2 — segment-fit remediation

## Why

A stress-test persona entered a **negative −£999,999 "Assets Under Administration"**; it saved cleanly
and *scored*, because `_interpolate` silently **clamps** an out-of-range raw to the nearest anchor. A
visible non-negotiable #3 (fail-loud) violation: garbage fed the score with no refusal.

## What changed (additive; retail golden master byte-identical)

- **`MetricDef` gains optional `min_raw` / `max_raw`** (registry.py) plus `domain_violation(raw)`,
  which returns a plain-English refusal for a non-finite value (NaN/inf) or anything past an explicit
  bound. A value *inside* the domain but past the anchors still clamps (a valid-but-extreme firm) —
  bounds only reject values that cannot exist for the metric.
- **`metrics.yaml`**: the eight non-negative retail metrics (AUA, active clients, net revenue,
  revenue/client, cost-to-serve, take-rate, NRR, CAC payback) carry `min_raw: 0`. The two
  legitimately-signed metrics (gross margin, client growth rate) stay unbounded, so a negative margin
  or shrinking growth is still a valid input.
- **`scoreability_blockers`** now refuses an out-of-domain metric as a fail-loud blocker the advisor
  can fix — never a clamp, never a 500.
- **`MetricEntry` + `MetricObservation`** reject a non-finite raw at the contract boundary, so NaN/inf
  can never persist or reach scoring.
- Sign constraints follow the per-segment table in the stress-test synthesis / ADR-0035; the wealth
  and exchange metric sets (Phases 2–3) declare their own bounds.

## Acceptance
- A negative AUA blocks scoring with "Assets Under Administration can't be below 0 GBP (got …)"; a
  negative gross margin scores fine. Golden master V=0.478565 unchanged. Full backend suite + schema
  sync green.
