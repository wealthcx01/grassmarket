# GRS-0096 — Primer: reading the outputs

**Status:** Shipped
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

## What shipped (Status: Shipped — branch grs-0096-primer-reading-outputs)

Expanded the primer's "Reading the outputs" section (`app/guide/page.tsx`) into four clearly-headed
concepts, each in plain English at a senior operator's depth:

- **Ranges, not points** — P50 is the best estimate, P10/P90 are how far it could reasonably sit given
  evidence quality; weak evidence widens the range honestly; always quote the range.
- **Words rate; numbers rank** — the rating (headline word, from rules) is what you defend; the ranking
  (continuous score) is what decides what to fix first — two outputs, two jobs, don't swap them.
- **The bottleneck sets the score** — the weakest critical element caps the whole (a module can't be
  Advanced if a critical part is Basic); the score-moving fix is usually the bottleneck.
- **The value bridge** — cost (£) / lever NPV (£, on the client's baselines) / strategic ordinal (words)
  kept apart; the Upgrade Priority Index says what first, the value bridge says what it's worth; never
  divide a score gap into pounds.

Frontend type-check · lint · vitest green. Completes the §2 Primer set (GRS-0092–0096).
