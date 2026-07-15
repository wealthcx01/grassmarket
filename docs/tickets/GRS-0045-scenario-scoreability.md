# GRS-0045 — Scenario evaluation must report an incomplete scenario, never 500

- **Loop:** 2 (Wizard Path A / scenarios)
- **Status:** Fixed — found in the 2026-07-14 adversarial API review.
- **Severity:** Medium — a schema-valid but structurally-incomplete request crashes the endpoint.
- **Normative source:** CLAUDE.md #3 (fail loud, but with a clean refusal — not an uncaught 500).

## Problem

`POST /assessments/{id}/scenarios` checked only the **baseline's** scoreability. Each *scenario*
document was then passed to `_complete_inputs`, which builds powers by indexing directly:

```python
powers = [_to_power_obs(doc_powers[k]) for k in sorted(registry.power_keys())]
```

A scenario document that omits any of the 7 power keys (or is otherwise unscoreable) raised
`KeyError`, uncaught through the router → **HTTP 500**.

## Change

`evaluate_scenarios` now runs `scoreability_blockers` on each scenario document before completing
it. If any scenario is unscoreable, it returns `ScenarioComparison(scoreable=False, blocking=…)`
with each blocker prefixed by the scenario name — mirroring the existing baseline path, a clean 200
refusal instead of a 500.

## Exit criteria

- A scenario missing powers (or otherwise unscoreable) returns 200 `scoreable=False` with a blocker
  naming the scenario — pinned by `test_scenario_missing_powers_reports_blocking_not_500`.
- The happy-path ranking and unscoreable-baseline behaviours are unchanged.
