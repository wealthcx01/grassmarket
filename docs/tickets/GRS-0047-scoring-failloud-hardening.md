# GRS-0047 — Scoring fail-loud hardening: triad key validation + B-index refusal

- **Loop:** 1 (ATLAS engine)
- **Status:** Fixed — found in the 2026-07-14 adversarial scoring review (findings F2, F3).
- **Severity:** Medium (F2, latent structural gap) / Low (F3, diagnosability).
- **Normative source:** CLAUDE.md #3 (fail loud) and #4 (every key validates against the registry);
  Feasibility Deep-Dive D1 (seed keys ≠ registry keys).

## Problems

- **F2 — triad source literals bypass registry validation.** `_score_triad` reads specific powers
  and metric groups by hardcoded literal (`_PERCEIVED_POWERS = ("BRANDING", "SWITCHING_COSTS")`,
  `_ECONOMIC_GROUPS = ("scale", "unit_economics")`) behind `if k in …` guards. Those literals are
  outside the coefficient/registry coverage checks, so a registry rename (BRANDING→BRAND, the literal
  D1 scenario) would be silently dropped by the guard and skew the ordinal — no error, a plausible
  wrong rating. (No wrong output today; the keys currently match — this closes the structural gap.)
- **F3 — B index raises a bare `ZeroDivisionError`.** If every business metric is Not Assessed,
  `_score_business` divides by an empty denominator and raises an opaque `ZeroDivisionError`, unlike
  the L path which raises an explicit, diagnosable refusal.

## Change

- `_assert_triad_sources_registered(registry)` runs in `score()` alongside the existing coverage
  checks: `_PERCEIVED_POWERS ⊆ registry.power_keys()` and `_ECONOMIC_GROUPS ⊆ registry metric
  groups`, else refuse to score. (Additive — it does not modify `_score_triad`.)
- `_score_business` refuses with `"Cannot compute B: no business metric is assessed."` before the
  division, matching `_score_l`.

## Exit criteria

- Scoring with all metrics Not Assessed raises the explicit B refusal (not ZeroDivisionError).
- A dangling triad source literal refuses to score. Both pinned in `test_atlas_engine_properties.py`;
  the golden master is unchanged.
