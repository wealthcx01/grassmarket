# GRS-0148e — Deliverable generation uses the assessment's profile view (not the retail superset)

**Status:** Implemented (2026-07-20).
**Loop:** Part 2 — stress-test remediation (from the full re-measure)

## Why

The full re-measure found a real HIGH bug: generating an **internal-draft deliverable for a wealth
assessment 500'd** (surfaced to the browser as "Cannot reach API" because the 500 carried no CORS
headers). The client-facing branch returned a clean 409, so the endpoint was up — only the render
path broke.

Root cause: `_render` built the document against `load_registry()` (the **retail superset**) and
`active_coefficient_set()` (the **retail** coefficients). But a wealth/exchange run was scored against
its **profile view** — its modules and metrics are profile-specific (`WEALTH_SUITABILITY`, `EXCH_ADV`,
…) and are **not in the retail superset** — so the builder key-errored → 500.

## What changed (backend-only)

- `_render` now builds against the SAME `(registry view, coefficient set)` the assessment was scored
  under, via `profile_scoring_context(profile_key)` — identical to how the live score + finalise run.
- `_resolve_run` returns the operating-model profile key (from the linked assessment's
  `document.profile`); the download path derives it the same way. Retail is unchanged (its profile
  view == the superset).

## Acceptance
- Generating (and downloading) an internal-draft deliverable for a wealth or exchange assessment
  returns a real `.docx` (verified live: HTTP 201, "Platform Power Report — St. James's Place"), not a
  500. Retail deliverables unchanged. New regression test renders wealth + exchange deliverables;
  15 deliverable tests + ruff + pyright green.
