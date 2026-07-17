# GRS-0110 — Summary & Interpretation + Scenarios: more detail & analysis

**Status:** Shipped
**Loop:** Part 2 — Advisor Studio UI/UX review
**Phase:** A (build now)
**Depends on:** —

## Why

The wizard's Summary & Interpretation and Scenarios steps are both too thin for a senior-operator
deliverable — the founder wants them **deeper and more analytical**. The Summary should genuinely
interpret the result (the bottleneck, ranges-not-points, what the words-vs-numbers say, the value
bridge) rather than restate inputs, and Scenarios should support real what-if analysis. This ticket
raises the analytical depth of both steps, reusing the diagnostics the engine already produces.

## What to build

**Summary step (`components/steps.tsx` — SummaryStep, `DiagnosticsPanel`)**
- Expand the summary into a proper interpretation: surface the bottleneck, P10/P50/P90 ranges, rate-vs-
  rank words, and the value-bridge read, drawing on the existing `DiagnosticsPanel` output rather than
  recomputing.

**Scenarios step (`components/steps.tsx` — ScenariosStep)**
- Deepen scenarios into meaningful what-if analysis (compare against the base result, show the effect on
  the headline read), keeping scenarios editable and non-destructive to the finalised inputs.

## Acceptance / verification

- The Summary step interprets the result (bottleneck, ranges, words-vs-numbers, value bridge), sourced
  from `DiagnosticsPanel` / engine output.
- The Scenarios step supports a comparative what-if against the base assessment.

## Not in scope

- Changing scoring, diagnostics computation, or the value-bridge math.
- The confusing live-score rail message — GRS-0104.

## What shipped (Status: Shipped — branch grs-0110-summary-scenarios-depth)

Raised the analytical depth of both steps, reading the diagnostics the engine already produces (no
recomputation):

**Summary** (`SummaryStep` + new `Interpretation`)
- A "What this means" card that genuinely interprets the result rather than restating inputs:
  - **Read the range, not the point** — V's P50 with its P10–P90 range and overall uncertainty.
  - **The bottleneck** — names the weakest module (lowest `module_qm` P50) and explains it caps the
    whole, so the fastest lift is the weakest critical part.
  - **Words rate; numbers rank** — the module bands are what you defend; the scores decide what to fix
    first.
  - **The value bridge** — the deliverable prices gaps in three separate layers (cost £ / lever NPV £ /
    strategic words); never a score-gap-into-pounds.

**Scenarios** (`ScenariosStep`)
- A baseline→projected read above the Upgrade Priority Index: `Baseline V X → the top upgrade (…) lifts
  it to Y`, reiterating that ΔV is score-domain (what to fix first), not worth (the value bridge prices
  that). Scenarios stay editable and non-destructive to the finalised inputs.

## Acceptance / verification

The Summary interprets the result (bottleneck, ranges, rate-vs-rank, value bridge) from the existing
diagnostics; Scenarios show the effect on the headline read against the base. Frontend type-check ·
lint · vitest green. Completes §3 Wizard Phase A (the buildable set).
