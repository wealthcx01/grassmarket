# GRS-0096 — Primer: reading the outputs

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** —

## Why

The primer's treatment of how to read the assessment's outputs is too thin for senior operators. The
outputs carry deliberate methodology choices that a reader must understand to interpret a result
correctly: results are **ranges, not points**; **words and numbers do different jobs** (rating vs.
ranking); the **bottleneck** drives the score; and the **value bridge** prices the result. This ticket
expands the outputs section so a reader can actually interpret what the assessment produces.

## What to build

**Primer (`frontend/app/guide/page.tsx`)**
- Explain **ranges, not points** — why the result is a range (P10/P50/P90) and how to read it.
- Explain **words vs. numbers** — the difference between the rating (headline word) and the ranking
  (continuous score), and what each is for.
- Explain the **bottleneck** — how the weakest element sets the score.
- Explain the **value bridge** — how a score is priced (cost £ / lever NPV £ / strategic ordinal), at a
  reader's level of depth.
- Keep it detailed but plain-English.

## Acceptance / verification

- The primer explains ranges-not-points, words-vs-numbers (rate vs. rank), the bottleneck, and the value
  bridge.
- Each concept is explained in plain English with enough depth for a senior operator to interpret a real
  result.

## Not in scope

- The live-score preview and summary-panel copy in the wizard (§3 tickets).
- Any change to the scoring, Monte Carlo, or value-bridge computation.
