# ADR-0040 — The one-number rule: the quoted point is always the deterministic score

- **Status:** Accepted (2026-07-23). From the 2026-07-22 staging persona rerun — 5/5 personas,
  top severity (`reports/mock-advisor-staging-rerun-2026-07-22.md`).
- **Date:** 2026-07-23
- **Deciders:** Engineering (presentation rule, not a scoring change), extending GRS-0161's rule.
- **Normative source:** Methodology §5 (deterministic scores unchanged), §7 (uncertainty as
  ranges), ADR-0008 (modelled flags), GRS-0161 (deliverable/portfolio already quote the
  deterministic `v_index`), GRS-0166 (locked wizard surfaces follow), non-negotiable #2 (scoring
  itself untouched — this is display).
- **Couples with:** ADR-0034 (uncertainty exclusions), the LockedScore presentation.

## Context

The platform computes two estimators from one document: the **deterministic engine score**
(Methodology §5 — the score of record; what a finalised run stores as `v_index`) and the **Monte
Carlo distribution** (§7 — uncertainty). Before this ADR the surfaces disagreed about which one to
headline: the live rail/summary bolded the MC **P50**, while the scenario baseline, the value
build-up chart, the AI narrative, and (since GRS-0166) every locked surface quoted the
**deterministic** score.

Five cold personas independently found the consequences disqualifying: the headline *changes at
the finalise click* with no input change (63.1→64.9, 56.1→58.0, 49.6→50.1); up to three V values
are visible pre-lock; an approved AI narrative quotes B/P/L that contradict the summary beside it;
and the locked point sits at ~P85 of a band computed around the P50 — statistically incoherent as
displayed. The MC median sits systematically below the deterministic score because bottleneck
`min()` terms under symmetric input noise bias draws downward — so the discrepancy is structural,
not occasional.

## Decision

**The quoted point is ALWAYS the deterministic engine score — on every surface, live or locked.
Monte Carlo supplies the range only.**

- `LiveScore` carries the deterministic `v_point`/`b_point`/`p_point`/`l_point` alongside the MC
  bands; every headline bolds the point.
- The displayed range is the MC P10–P90 **clamped to include the point** (the GRS-0161 deliverable
  presentation), labelled "modelled P10–P90" — never "P50", because the bold figure is not the
  median and must not claim to be.
- The finalise click therefore does not move the number: the stored `v_index` IS the point the
  advisor watched.
- The build-up chart, scenario baseline, narrative, portfolio, deliverable, and locked wizard all
  already quote deterministic values — after this change they agree with the rail exactly
  (θ_B·B + θ_P·P + θ_L·L recomputes to the headline to the displayed precision).

## Consequences

- No scoring change: engine, Monte Carlo, stored runs, and the golden master are byte-identical.
  This is which number gets bolded.
- The MC median is no longer displayed anywhere as a headline. It remains inside the band; anyone
  needing it has the P10–P90 and the uncertainty rating.
- A point may sit near the top of its clamped band — that is now *explained by construction* (a
  deterministic point vs a downward-biased modelled distribution) and the label no longer claims
  the point is a quantile of the band.
- Module-level diagnostics (q_m table, bottleneck) keep their existing values — persona
  recomputation already verified them against the displayed anchors.
