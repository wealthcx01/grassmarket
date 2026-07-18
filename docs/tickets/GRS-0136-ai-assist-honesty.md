# GRS-0136 — AI-assist honesty + anti-anchoring (critical-review hardening)

**Status:** In progress
**Loop:** Part 2 — critical review / trust hardening
**Amends:** ADR-0032 (wizard AI-assist)

## Why (outside-in critical review)

A skeptical-advisor stress test of the product surfaced two trust problems in the wizard assist and
one advertised-but-inert AI feature:

1. **The carry-forward PREFILL anchors the assessment.** GRS-0101 proposed the module's *modal* rated
   level as a starting value for an unrated subcomponent. But ATLAS is **bottleneck-sensitive** — the
   weakest subcomponent drives the module score (the monotonicity/bottleneck property the engine
   exists to surface). Pre-planting the mode pulls an unrated subcomponent *toward the herd*, which
   both inflates the module score and **masks the binding constraint**. A one-click "Accept" on a
   plausible pre-planted number is the path of least resistance, and a routine subcomponent has no
   independent downstream check. This is a real assessment-quality risk, not a neutral convenience.

2. **A deterministic heuristic is labelled "AI".** The suggester is a pure `Counter.most_common` +
   if-statements (`heuristic-v1`), yet the panel says "AI suggestions" / "AI-proposed". Internally the
   team is honest (ADR-0032 calls it heuristic); to the advisor it is not. An advisor who discovers a
   modal-counter behind "AI" reasonably distrusts every other AI claim. The win-probability surface is
   the model to copy: it says "Win probability", never "AI".

3. **Meeting extraction is advertised as a working AI feature but ships as `EmptyExtractor` (a no-op).**
   The help copy promises "meeting extraction… AI-drafted"; the wired extractor proposes nothing.

## What to change

- **Defuse the anchor.** The suggester stops emitting a `PREFILL` with a pre-planted `proposed_level`
  for the carry-forward case. It emits a **GUIDANCE** nudge instead: "N subcomponents still unrated in
  {module} — assess each on its own evidence; the weakest drives the score." No number is planted, no
  "Accept" affordance. (The `PREFILL` kind stays in the contract for a future genuinely-safe prefill.)
- **Relabel honestly.** The wizard panel says "Suggestions" / "Assistant checks — suggestions, not
  scores", not "AI". Behaviour unchanged.
- **Stop over-advertising extraction.** Soften the help copy to reflect that meeting extraction is not
  yet wired (no live model), so no advisor tries it and gets nothing.

## Not in scope / flagged for the founder
- Single-senior self-approval of client narratives — ADR-0009 *deliberately* permits a Consultant-tier
  author to self-approve; changing it is an ADR decision, not a silent edit. Flagged, not changed.
- "AI drafted" on deliverable narratives (template-fill) — gated + per-run; softer issue, flagged.
- Deepening the mandatory doctrine courses; wiring the drill/quiz comprehension loop — separate builds.

## Acceptance
- No wizard suggestion pre-plants a maturity level; the assist is guidance-only. Copy says "Suggestions",
  not "AI". Help no longer promises live meeting extraction. Golden master untouched.
