# GRS-0105 — Strategic Powers: rigor + Helmer depth + evidence

**Status:** Shipped
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

## What shipped (Status: Shipped — branch grs-0105-powers-rigor)

Brought the Helmer material into the Strategic Powers step and made ratings evidence-grounded, with
the E-grades de-jargoned in place:

- **`lib/powerGuidance.ts`** — extended `PowerGuidance` with an **`assessment`** field ("how to assess
  this power objectively — what evidence establishes the benefit AND the barrier, and what makes it
  weak") authored for **all 7 powers**, single-sourced (the step imports it, GRS-0069).
- **`StrategicPowersStep`** — the per-power toggle "See an example" is now **"How to assess this
  power"**, opening a full panel: **Benefit** hint, **Barrier** hint (+ the weaker-side rule),
  **How to assess**, and the **Example** — the Helmer framing per power, not just a one-liner. The
  benefit/barrier strength + grade selects and the per-side rationale fields (GRS-0069) stay, so a
  rating captures WHY.
- **De-jargoned E-grades** — the step intro now spells out the ladder in plain English (**E1**
  client-said · **E2** interview · **E3** artifact · **E4** observed, weakest→strongest) and reiterates
  that grades drive §7 uncertainty, not the score.

## Acceptance / verification

Each power presents the Helmer benefit/barrier framing + how it is assessed + a grounded rationale
capture; E-grades read in plain English. Content is single-sourced in `powerGuidance.ts`. Frontend
type-check · lint · vitest green.
