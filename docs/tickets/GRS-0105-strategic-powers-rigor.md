# GRS-0105 — Strategic Powers: rigor + Helmer depth + evidence

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Phase:** A (build now)
**Depends on:** —

## Why

The Strategic Powers step is too basic: for each power it offers only an "in a brokerage…" example and
an E-grade, then a strength dropdown — no real grounding and no rigor. Senior operators need the actual
Hamilton Helmer material: what each power is, its **benefit vs barrier**, why the **weaker side sets the
strength**, and how each power is genuinely assessed — so a rating is evidence-based and objective
rather than a guess picked from a dropdown. This ticket brings the Helmer literature into the step,
makes ratings evidence-based, and de-jargons the E-grades in place.

## What to build

**Strategic Powers step (`components/steps.tsx` — StrategicPowersStep)**
- For each power, present the Helmer benefit/barrier framing, how the power is assessed, and
  operating-model-relevant context (not only a brokerage example).
- Make the rating evidence-based: capture rationale/evidence supporting the chosen strength rather than
  a bare dropdown, and present E-grades in plain English.

**Power guidance content (`lib/powerGuidance.ts`)**
- REUSE and extend the per-power guidance authored in `lib/powerGuidance.ts` (GRS-0069) as the single
  source for the Helmer benefit/barrier/assessment content — author content there, don't inline it.

## Acceptance / verification

- Each power shows Helmer benefit/barrier + how-assessed content drawn from `lib/powerGuidance.ts`.
- A power rating captures supporting evidence/rationale, and E-grades render in plain English.

## Not in scope

- The generic cross-wizard evidence field mechanism — GRS-0107 (this step uses it for powers).
- Primer-side Helmer explainer — GRS-0094.
