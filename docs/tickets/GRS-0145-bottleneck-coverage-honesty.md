# GRS-0145 — Low-coverage honesty caveat on the "likely constraint" callout

**Status:** In progress
**Loop:** Part 2 — mock-advisor stress test / trust hardening

## Why

The quant persona (Deutsche Börse lens) found the live panel's most actively-misleading behaviour: at
**14% coverage** it confidently named "EMS Gateway" the platform bottleneck and advised "the fastest
lift comes from fixing the weakest critical part" — a module she had **not assessed at all**. Root
cause (traced, see GRS-0146): the Monte-Carlo layer imputes a ~neutral band for Not Assessed
subcomponents, so a zero-coverage module still gets a `q_m` band and can rank weakest. The frontend
"likely constraint" selectors (`LiveScorePanel.tsx`, `steps.tsx`) pick the lowest-`p50` module with
**no coverage check**, turning a coverage gap into confident but wrong advice.

The underlying imputation is methodology-gated (**GRS-0146**, needs an ADR). This ticket fixes the
*display* half — which needs no scoring change and uses the existing top-level `coverage` field.

## What changed (frontend-only, no scoring/contract change)

- **`components/steps.tsx` (Summary interpretation)** — when `coverage < 0.5`, the bottleneck line
  drops the confident "fastest lift comes from fixing this" and instead reads: "at only N% coverage
  this is provisional: a module can rank weakest simply because it hasn't been assessed yet — assess
  more before acting on it."
- **`components/LiveScorePanel.tsx` (rail callout)** — at `coverage < 0.5` the header becomes
  "Likely constraint · provisional" and a caveat line explains that an unassessed module can rank
  weakest. Above half coverage both render exactly as before.

Consistent with the GRS-0136 anti-anchoring / AI-honesty precedent: never present a modelled artefact
as a confident fact. The scores themselves are untouched.

## Acceptance
- Below 50% coverage the bottleneck callout is labelled provisional and explains the coverage caveat;
  at/above 50% it is unchanged. Typecheck, prod build, and all 19 frontend tests pass. Golden master
  untouched (no scoring code).
