# GRS-0106 — Merge Module Overview into the Infrastructure Deep Dive

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Phase:** A (build now)
**Depends on:** —

## Why

The wizard has two adjacent infrastructure pages, and the Module Overview reads as "a random
high-level page linked to the deep dive" — a separate step that duplicates context the Infrastructure
Deep Dive already covers. This ticket combines them into one page: fold the overview into the deep dive
so the advisor works a single coherent infrastructure step, while keeping the valuable per-subcomponent
Guidance — integrated inline rather than stranded on its own screen. This is a **genuinely new** IA
simplification (one of the review's non-overlap asks), removing a step from the flow.

## What to build

**Wizard steps (`components/steps.tsx`, `app/assessments/[id]/WizardClient.tsx`)**
- Merge the Module Overview content into the Infrastructure Deep Dive step, integrating the
  per-subcomponent Guidance inline; drop the standalone overview step from `WIZARD_STEPS`.
- Ensure navigation, step numbering, and the live-summary rail account for the removed step.

## Acceptance / verification

- `WIZARD_STEPS` has one fewer step; there is no standalone Module Overview page.
- The per-subcomponent Guidance is preserved, integrated within the Infrastructure Deep Dive.
- Step navigation/numbering is correct after the merge (no dead links to the removed step).

## Not in scope

- Changing subcomponent scoring or the Guidance content itself.
- Widget checklist / C-index surfacing — GRS-0108.
