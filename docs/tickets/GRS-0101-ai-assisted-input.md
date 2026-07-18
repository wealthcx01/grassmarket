# GRS-0101 — AI-assisted input in the wizard

**Status:** Shipped
**Loop:** Part 2 — Advisor Studio UI/UX review
**Phase:** B (flagged follow-up — its own ADR/ticket set later)
**Depends on:** —

## Why

The founder's core theme for the wizard is that it should stop being raw data entry and become
**AI-assisted** — suggestions, prefill, and contextual help as the advisor works, so the flow feels
like assisted homework rather than filling boxes. This ticket is the **umbrella** for the broad
AI-assist surface across the wizard's input steps. It is a new capability spanning multiple steps and
depends on the AI-approval gating discipline, so it is **deferred behind Phase A** and scoped later in
its own ADR / ticket set (with GRS-0100 and GRS-0109). Phase A's specific ingestion items — surfacing
Path B meeting upload (GRS-0102) and the widget/video work (GRS-0108/0109) — sit under this umbrella but
are ticketed separately.

## What to build

**Wizard input assistance (`components/steps.tsx`, `app/assessments/[id]/WizardClient.tsx`)**
- Add AI-assisted suggestion / prefill / contextual-help affordances on the input steps so advisors get
  proposed values and guidance rather than a blank form, with every AI-proposed value clearly labelled
  and human-approved before it counts (AI proposes, humans approve).

## Acceptance / verification

- Input steps offer AI-proposed suggestions/prefill that the advisor explicitly accepts or edits.
- No AI-proposed value is committed without a visible approve step.

## Not in scope

- Path B meeting-recording upload — GRS-0102 (Phase A).
- Screen-recording → video dissection → widget auto-population — GRS-0109.
- Entity/company linking — GRS-0100.
