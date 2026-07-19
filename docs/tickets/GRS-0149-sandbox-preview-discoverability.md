# GRS-0149 — Surface the solo path: "Preview in sandbox" from the wizard

**Status:** In progress
**Loop:** Part 2 — stress-test remediation (GRS-0148 Item 1)

## Why

The single highest-consensus "the product can't do X" finding (4 of 5 stress-test personas): a
working-solo advisor concluded there was **no way to reach a finished score or see the client
deliverable**, because production finalise requires a second independent rater + committee sign-off.
The escape hatch already exists — a **sandbox** record self-approves and produces a real, watermarked
deliverable (GRS-0119, ADR-0029) — but it was a faint checkbox on the *create* page that testers left
behind, and there was no way to reach it once inside a production assessment.

## What changed (frontend-only, reuses shipped endpoints — no backend)

- **`SummaryStep` (`components/steps.tsx`)** — for a production assessment (not read-only) the finalise
  section now carries a **"Preview in sandbox"** affordance: "Working solo? A production score
  finalises with a second rater and committee sign-off. To see a finished, watermarked deliverable
  now, create a Sandbox preview — self-approved, never client-facing."
- **`WizardClient` (`previewInSandbox`)** — clones the current assessment into a sandbox copy by
  composing two existing endpoints: `createAssessment(subject, "sandbox", entity_id)` then
  `saveAssessment(copy.id, document)` (the document carries the full in-progress state incl. the
  operating-model profile), then opens the copy. In the copy, finalise self-approves and renders the
  real watermarked deliverable draft.
- **Create page (`app/assessments/page.tsx`)** — the sandbox checkbox copy is clarified to name the
  benefit ("finalise solo & see the real deliverable") and note it can also be spun up later from the
  Summary step.

## Acceptance
- A production assessment's Summary step offers "Preview in sandbox"; clicking it lands the advisor on
  a sandbox copy carrying the same inputs, which finalises solo into a watermarked deliverable.
- Typecheck, prod build, and all 19 frontend tests pass. No backend/contract/scoring change.
