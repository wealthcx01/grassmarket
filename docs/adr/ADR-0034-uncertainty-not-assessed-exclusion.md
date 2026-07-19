# ADR-0034 — Not Assessed is excluded from the uncertainty layer, never imputed (D9 in Monte Carlo)

- **Status:** Accepted (2026-07-19). Founder-directed as part of the stress-test remediation program (raise advisor trust from a mean 57/100 toward ≥95).
- **Date:** 2026-07-19
- **Deciders:** Founder + engineering
- **Normative source:** `docs/ATLAS-Methodology-v1.5.md` §7 (this ADR is its rationale).
- **Implements:** GRS-0146.
- **Amends:** ADR-0008 (§7 uncertainty). **Reconciles with:** ADR-0001 (D9 — non-score states are never imputed).

## Context

The deterministic engine honours D9 correctly: a Not Assessed subcomponent carries `state`, not
`level`, and contributes to no score; a fully-unassessed module has `q_m = None` and is excluded from
L (`atlas/engine.py`). **But the uncertainty layer overrode this.** In Monte Carlo, `_perturb`
(`atlas/montecarlo.py`) replaced every Not Assessed subcomponent with a *uniform draw over all four
maturity levels* and **included it in the draw** — justified in a code comment as "maximal ignorance
widens the band."

A quant advisor (Deutsche Börse lens) found the failure mode in the July stress test: at **14%
coverage** the live panel showed a ~49–52 `q_m` band for **every** module — including ones with zero
assessed subcomponents — and confidently named an unassessed module ("EMS Gateway") the platform
bottleneck, advising "the fastest lift comes from fixing the weakest critical part." Three defects,
one root cause:

1. **Phantom module bands.** The uniform prior (mean 0.625) produced `q_m ≈ 0.7·0.625 + 0.3·0.2 ≈
   0.50` for a module nobody assessed — a fabricated, falsely-precise number.
2. **Phantom bottleneck.** Because every module got a band, a zero-coverage module was eligible to be
   ranked weakest — and was. The advice pointed the advisor at the one system nobody had looked at.
3. **Band too tight for the coverage.** Averaging many uniform draws concentrates by the law of large
   numbers, so 14% coverage still showed a ±2-point V band. Coverage drove only the *label* (the
   Assessment Uncertainty Rating), never the band width — an internally contradictory panel.

This directly violates D9's "never imputed" clause. It was ratified nowhere in the methodology — only
in that code comment, back-justified by the ADR-0008 §3 sentence "subcomponents always carry evidence
grades, so V/L/q_m are always modelled," which was only true *because* of the force-impute. (The
display symptom was band-aided by GRS-0145, which labels the bottleneck "provisional" below 50%
coverage; this ADR fixes the source.)

## Decision

**In the uncertainty layer, a Not Assessed subcomponent is excluded from every draw — never imputed.**
It passes through unchanged (level = None) exactly as a Not Applicable input does, so the kernel drops
it. Consequences, now identical to the deterministic engine:

1. A fully-unassessed module has `q_m = None` in every draw → **no band in `module_qm`** → it can
   never be shown as a precise band or named the bottleneck.
2. A partially-assessed module bands only over its assessed subcomponents — an honest range for the
   measured part.
3. **Ignorance about the unmeasured is carried by coverage, not a fabricated band:** the coverage-
   driven Assessment Uncertainty Rating (zero coverage → VERY_HIGH) and the deterministic tornado (a
   Not Assessed input spans Basic↔Frontier and tops the leverage ranking). The band expresses only
   the uncertainty of what was measured.

This is a **§7-only** change. The deterministic score path is untouched: both golden masters
(V = 0.478565; the four-index oracle) are byte-identical, verified by their existing direct-`score()`
tests, which never route through Monte Carlo. Only the **UncertaintyModel** methodology stamp bumps
(`1.2` → `1.5`); the CoefficientSets and the engine version are unchanged.

## Consequences

- `montecarlo.py`: the impute branch in `_perturb` becomes a pass-through; the dead `_uniform_level`
  helper is removed; the docstring and the `run_monte_carlo` comment are corrected; the two
  UncertaintyModels bump `methodology_version` to `1.5`.
- **Tests:** the old `test_not_assessed_widens_the_band_vs_assessed` inverts (Not Assessed can no
  longer inflate the band — excluding a sub is tighter than assessing it even at the widest grade).
  Two property tests are added: a zero-coverage module is absent from `module_qm` while its
  `module_uncertainty` is VERY_HIGH; and band width does not widen as coverage rises.
- **Frontend:** no change required — `module_qm` consumers simply never receive a zero-coverage
  module. GRS-0145's low-coverage caveat remains correct for the 0 < coverage < 0.5 case.
- **New methodology doc** `docs/ATLAS-Methodology-v1.5.md` (§7 amended, all else by reference).

## Alternatives considered

- **Keep imputing but widen the band at low coverage** (post-hoc inflate P10/P90 by a coverage
  factor). Rejected: it fabricates a width with no elicited basis (the exact "defaulted number"
  non-negotiable #3 forbids) and does not remove the phantom module/bottleneck — a module nobody
  assessed would still get a band.
- **Keep imputing but tag bands "modelled-from-ignorance" vs "-from-evidence."** Rejected as the
  primary fix: it still computes phantom bands and pushes the exclusion decision onto every renderer —
  the same latent-bug class GRS-0145 had to patch. Excluding the module outright is the cleaner signal
  and is what the deterministic engine already does.
