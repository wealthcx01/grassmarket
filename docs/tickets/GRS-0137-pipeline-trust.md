# GRS-0137 — Pipeline trust: forecast consistency + win-probability explainability

**Status:** In progress
**Loop:** Part 2 — critical review / trust hardening

## Why (outside-in critical review)

A skeptical-advisor stress test found the two numbers an advisor actually reads on the pipeline —
the per-deal win-probability pill and the headline "weighted forecast" KPI — **disagree with each
other**, and the KPI **counts already-won work as "expected won deals"**:

- `weighted_expected_deals` was `Σ (count × stage_base)` over *all* prospects, including `active` /
  `delivered` (base 1.0 — already won) and `nurture` (0.05). So the headline inflated with work
  already closed, and it ignored the per-prospect win probability the cards show. An advisor who adds
  up the pills gets a different number than the KPI — the fastest way to look broken.
- The win-probability estimate is computed *with* reasons and "what would sharpen it", but the whole
  explanation lived only in a hover `title` tooltip on the pill — invisible on touch, and absent from
  the deal slide-over (the one surface with room). The "explainable, not a black box" promise wasn't
  kept where an advisor looks.

## What changed

- **Forecast = sum of the pills.** `build_forecast` headline is now `Σ` each **non-settled** prospect's
  OWN win probability (base strictly in (0,1)) — identical to the sum of the win-probability pills, and
  free of already-won (`active`/`delivered`, base 1.0) and lost (`closed`, base 0.0) work. The per-stage
  funnel rows are unchanged. Contract description + KPI label updated ("Expected wins · open pipeline,
  Σ win-probabilities"). A test asserts KPI == Σ non-settled pills, with delivered/closed excluded.
- **Explainability shown, not hovered.** The deal slide-over now renders a "Win probability" section:
  the score + band, a "Why" list (the reasons), and a "Would sharpen the estimate" list (the gaps) —
  the same data that was hidden in the tooltip, now legible on every device.

## Flagged (not changed this pass)
- The win-probability rewards CRM completeness (contact/email/sector/notes) more than deal quality, and
  the stale penalty is a flat −10pp with no time-decay — real refinements, but they need calibrated
  weights + new buying signals (recency, workshop-delivered), a larger design change. Flagged.

## Acceptance
- The headline KPI equals the sum of the non-settled win-probability pills; already-won/lost work is
  excluded. The deal panel shows the win-probability reasons + gaps as visible text. Golden master
  untouched (pipeline is not the scoring path).
