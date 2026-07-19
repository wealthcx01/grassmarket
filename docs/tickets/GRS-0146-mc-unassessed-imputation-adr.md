# GRS-0146 — Reconcile Monte-Carlo unassessed-imputation with ADR-0001 D9 (needs an ADR)

**Status:** Implemented (2026-07-19) — founder greenlit the remediation program. ADR-0034 +
Methodology v1.5. See "Resolution" at the foot.
**Loop:** Part 2 — mock-advisor stress test / scoring integrity

## The finding (verified in source)

The deterministic engine correctly honours D9: a Not Assessed subcomponent contributes to no score,
and a fully-unassessed module has `q_m = None` and is excluded from L (`atlas/engine.py:188,202,289`;
`results.py`). **But the uncertainty layer overrides that:** `atlas/montecarlo.py:285-298` imputes a
*uniform-over-all-four-levels* prior for every Not Assessed subcomponent and includes it in each draw
(comment: "maximal ignorance … INCLUDED this draw so the unknown widens the band"). Consequences the
quant persona observed at 14% coverage:

1. **Phantom module bands.** Every module — including zero-coverage ones — gets a `q_m` band centred
   ~49–52 (uniform mean 0.625 → `q_m ≈ 0.7·0.625 + 0.3·0.2 ≈ 0.497`). The deterministic engine would
   return `None`. So the live panel shows confident-looking bands for modules nobody assessed.
2. **Phantom bottleneck.** Because `module_qm` now contains a band for every module, a zero-coverage
   module is eligible for — and was — named the "likely constraint" (display half fixed in GRS-0145).
3. **Band too tight for coverage.** Averaging many imputed uniform draws concentrates by the LLN, so a
   14%-coverage assessment can still show a ±2-point V band. Coverage drives only the *label*
   (`overall_uncertainty` → VERY_HIGH), never the band width.

This contradicts **ADR-0001**'s D9 ("an unassessed subcomponent contributes to no score; never
imputed") and is **not** ratified in the methodology docs — it lives only in the montecarlo comment,
justified after-the-fact by **ADR-0008 §3** ("subcomponents always carry evidence grades, so V/L/q_m
are always modelled") — which is only true *because* the code force-imputes.

## Why this is founder-gated

Per CLAUDE.md non-negotiables #2/#3, scoring/uncertainty behaviour changes are **ADRs + a methodology
version bump, never silent edits**. This touches the golden-master/uncertainty fixtures and the ADR-0001
↔ ADR-0008 tension directly. It must not be patched autonomously.

## Options to weigh (for the ADR)
- **Exclude zero-coverage modules** from `module_qm` (mirror the deterministic `None`), so the panel
  never shows or ranks a module nobody assessed.
- **Keep the imputation but make coverage widen the band** — a low-coverage module should show a wide
  band (honest ignorance), not a tight ~50. Feed coverage into the P10/P90 width.
- **Distinguish "modelled from evidence" from "imputed from ignorance"** in the band metadata, so the
  UI can render them differently.

## Acceptance (when scoped)
- A new ADR reconciles D9 with the uncertainty layer; the methodology version bumps; golden master +
  property tests updated intentionally; the live panel no longer presents a zero-coverage module as a
  precise band or a confident bottleneck.

## Resolution (2026-07-19)
Chose **Option A** (exclude, don't impute). `montecarlo.py` `_perturb` now passes a Not Assessed
subcomponent through unchanged (like N/A), so a fully-unassessed module has `q_m=None` every draw and
gets no band in `module_qm` — no phantom band, no phantom bottleneck. Ignorance stays carried by the
coverage-driven Assessment Uncertainty Rating (VERY_HIGH) and the tornado. UncertaintyModel stamp
`1.2`→`1.5`; deterministic engine + both golden masters byte-identical. ADR-0034 +
`docs/ATLAS-Methodology-v1.5.md`. Tests: inverted the old widening test + added two property tests
(zero-coverage module absent from `module_qm`; band width non-increasing in coverage).
