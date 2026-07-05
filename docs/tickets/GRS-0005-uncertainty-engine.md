# GRS-0005 — Uncertainty engine (Monte Carlo, §7)

- **Loop:** 1 (see PRD §9)
- **Branch:** `grs-0005-uncertainty-engine`
- **Status:** In review
- **Normative source:** `docs/ATLAS-Methodology-v1.1.md` §7; ADR-0001, ADR-0002.
- **Depends on:** GRS-0004 (the deterministic engine — the kernel Monte Carlo wraps).

## Goal

Monte Carlo per §7, producing P10/P50/P90 ranges, Assessment Uncertainty Ratings, tornado data, and
weight-stability intervals. **Monte Carlo wraps `score()`** — it perturbs the *inputs* and runs the
untouched deterministic engine, so the point estimate and every band come from one code path.

## Precursor (GRS-0004 audit follow-up)

The golden-master fixture now stores non-score states as the CONTRACT enum VALUES ("Not Applicable"
/ "Not Assessed", D8), matching what the engine emits. `build_golden_master.py` binds the constants
to `NonScoreState.*.value`; the fixture was regenerated with **only the three subcomponent state
strings changed — every ratified number is byte-stable (V = 0.478565)**. The `_state_value` alias in
the golden-master test is deleted; states compare directly.

## Randomness discipline (the key design point)

This is the first randomness in the codebase. The RNG is **injected and seeded** — a `random.Random`
or a numpy `Generator`, both satisfying the `.random()` protocol — passed into `run_monte_carlo`.
It is never module-global and never time-seeded. Draws consume the RNG in a fixed registry order, so
**same seed + same draws ⇒ byte-identical result**. The deterministic golden-master guarantee is
untouched: `score()` has no RNG; only the wrapper does, and only through the injected generator.

## Input-distribution model (§7)

Maturity is ordinal, so uncertainty is modelled as a distribution over *which level is true* — a
draw samples a level and feeds it to `score()` (no continuous index leaks in — the engine stays the
kernel). Per assessed subcomponent at level ℓ with evidence grade g:

- **Family:** adjacent-level categorical. `P(ℓ) = 1 − spread(g)`; the remaining `spread(g)` goes to
  the adjacent level(s), split evenly, or wholly onto the single neighbour at the Basic/Frontier ends.
- **Per-grade widths `spread(g)`** (draft coefficients, provenance-carrying, `client_usable=False`,
  in `bcap_contracts.uncertainty.UncertaintyModel`): **E4 0.02 · E3 0.10 · E2 0.25 · E1 0.50**.
  Enforced non-increasing E1 ≥ E2 ≥ E3 ≥ E4, so the "E4 tight → E1 wide" guarantee is structural, not
  assumed. At E1 half the mass leaves the point level — an E1 rating genuinely *spans the adjacent
  level*.
- **Not Assessed:** sampled **uniform over all four levels** (max-entropy — "we don't know, it could
  be anything") and INCLUDED in the draw, so a missing assessment *widens* the band. This is a
  structural choice (max-entropy prior), documented here, not a tunable weight. (Not Applicable stays
  out of scope in every draw.)

**v1 scope boundary:** §7's input-distribution mechanism is evidence-grade-driven, and only
subcomponents carry evidence grades. Metric and power inputs have no evidence grade, so **B and P are
held at their point values and reported as degenerate bands** (P10 = P50 = P90) until their own input
-uncertainty models — financial measurement error for metrics, committee confidence for powers — are
added. **V and L carry real Monte Carlo ranges.** This is called out so the degeneracy reads as
scope, not a bug.

## Outputs

- **Bands** — P10/P50/P90 for V, L, B, P, and per-module q_m (linear-interpolation percentiles).
- **Assessment Uncertainty Rating** (Low/Medium/High/Very High), per module and overall, from
  **coverage × evidence factor** (mean assessed evidence rank / 4). Cut-offs 0.75 / 0.50 / 0.25 are a
  §7 reporting discretisation. **Rater agreement is a third §7 confidence input** that arrives with
  dual-rating in a later loop — noted, not yet used.
- **Tornado** — each input's one-at-a-time swing on V across its uncertainty support (others at
  point): assessed subcomponents move ±1 level, a Not-Assessed subcomponent spans Basic↔Frontier.
  Ranked by |swing|, so both structural leverage (a bottleneck in a critical-for-L module) and
  missing evidence surface at the top.
- **Weight-stability interval** — V recomputed as θ/α move over a documented neighbourhood; a narrow
  interval means the headline survives weight movement. The draft sweep is a placeholder for the
  swing-elicitation panel's stability intervals (§6).

## Tests

Deterministic (fixed seed): bands ordered and reproducible run-to-run (`r1 == r2`); P50 sits on the
deterministic V (±0.01) and the point lies inside [P10, P90]; **all-E4 V range strictly narrower than
all-E1** (evidence drives width) with matching overall ratings (Low vs High); tornado ranks a known
high-leverage input (a Not-Assessed subcomponent in critical-for-L OEMS) first; **Not Assessed widens
the band vs the same input assessed**; the weight-stability interval brackets the point; the
`UncertaintyModel` rejects non-monotone/incomplete widths. Meridian is the worked case.

## Out of scope

The value bridge and scenario re-scoring (GRS-0006); metric/power input-uncertainty models; rater
-agreement input (needs dual-rating). No changes to `score()`.
