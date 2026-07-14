# GRS-0043 — Economic Value must read Not Assessed, never a "None" moat floor

- **Loop:** 1 (ATLAS engine)
- **Status:** Fixed — found in the 2026-07-14 adversarial scoring review.
- **Severity:** High — a silent default in the deterministic scoring path produces a wrong,
  client-facing moat rating (defect D9 resurfacing: Not Assessed conflated with zero).
- **Normative source:** ATLAS Methodology v1.2 §2 (Platform Power triad); CLAUDE.md #3 (fail loud,
  Not Assessed never contributes); Feasibility Deep-Dive D9.

## Problem

`_score_triad` derived Economic Value from the `scale` + `unit_economics` metric group means:

```python
econ_src = [group_means[g] for g in _ECONOMIC_GROUPS if g in group_means]
economic = sum(econ_src) / len(econ_src) if econ_src else 0.0   # ← silent floor
```

An assessment is scoreable with **one business metric of any group** (`scoreability_blockers`
requires only "at least one business metric" — a `momentum` metric alone qualifies). So a valid,
scoreable assessment can have every `scale` and `unit_economics` metric Not Assessed, leaving
`econ_src` empty → `economic = 0.0` → `_to_ordinal(0.0)` → `"None"`. The client is told the platform
has **no economic moat**, when the truth is the dimension was **not assessed**. The B index already
renormalises honestly (drops absent groups); the triad ordinal did not — it hardcoded a `0.0` floor,
and `TriadDimensionResult.rating` could not even represent the honest answer.

## Change

- `TriadDimensionResult.rating` / `.score` are now `str | None` / `Score | None` — None = Not
  Assessed, mirroring the D9 `q_m: Score | None` discipline. Zero-filling is gone.
- `_score_triad` emits `TriadDimensionResult(rating=None, score=None)` when a dimension has no
  assessed source (economic or, defensively, perceived).
- Consumers handle None honestly: the live-score contract already types the triad fields
  `StrengthRating | None` (so None flows through untouched); the report and narrative render
  "Not assessed"; the committee gate no longer treats a Not-Assessed dimension as a high-stakes
  rating.

## Exit criteria

- With no scale/unit-economics metric assessed, Economic Value reports Not Assessed (rating/score
  None), never `"None"` — pinned by `test_triad_economic_is_not_assessed_never_a_none_floor`.
- The golden master (all dimensions assessed) is unchanged; the full suite stays green.
