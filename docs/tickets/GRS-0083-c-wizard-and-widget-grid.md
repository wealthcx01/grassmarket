# GRS-0083 — C wizard step + widget-capture grid

**Status:** Planned
**Loop:** Loop 7 — C-index (Customer Proposition)
**Depends on:** ADR-0023 (Accepted), ATLAS-Methodology-v1.3

## Why

With the C registry (GRS-0080), anchors (GRS-0081) and engine (GRS-0082) in place, a consultant
needs a way to capture the customer proposition during an assessment. The Infrastructure Deep Dive
step is the proven template: C is a structurally identical module-plus-subcomponent step, plus a
widget-capture grid unique to the customer profile. This ticket adds the wizard step, the grid, the
document collection that persists it, and the Summary read-out of C beside V.

## What to build

Files:
- `frontend/components/steps.tsx` — add a `CustomerPropositionStep` to `WIZARD_STEPS`
  (`steps.tsx:704`), cloning `InfrastructureDeepDiveStep` (`steps.tsx:460`) for the 10 C modules /
  subcomponents. Add a **widget-capture grid**: per widget → Present Y/N, Ease / Usability / Depth
  1–5, and the rarity tag (read from registry). Non-present widgets support the new
  `PRESENT_PAYWALLED` / `PRESENT_DEFECTIVE` states from GRS-0082.
- `src/grassmarket/atlas/assessments.py` — add a `customer` / widgets collection to
  `AssessmentDocument` (`assessments.py:379`).
- `frontend/lib/types.ts` — mirror the `customer` / widgets collection on the document
  (`types.ts:77`).
- `frontend/lib/doc.ts` — edit helpers for the customer collection (add/update/remove widget rows),
  same pattern as existing subcomponent/power helpers.
- Summary — the `DiagnosticsPanel` renders C alongside V (reported, not summed — Stage 1).

Refs / reuse:
- `InfrastructureDeepDiveStep` (`steps.tsx:460`) is the step template.
- `_complete_inputs` Not-Assessed completion (`atlas/assessments/service.py:128`) is reused as-is so
  un-touched C subcomponents complete to Not Assessed exactly like B/P/L.
- The `Guidance` toggle and grade-select patterns from existing steps.

New:
- The widget grid control (Present Y/N + Ease/Usability/Depth 1–5 + rarity display).
- The `customer` document collection and its edit helpers.

## Acceptance / verification

- The C step renders all 10 modules, their subcomponents, and the 93-widget grid for a retail-profile
  assessment; a non-retail profile does not show the retail grid.
- Widget rows persist round-trip through `AssessmentDocument` (save → reload identical).
- `PRESENT_PAYWALLED` / `PRESENT_DEFECTIVE` selectable and serialise correctly.
- Untouched C subcomponents complete to Not Assessed via `_complete_inputs` (no zero-fill).
- Summary shows C beside V; front-end suite (type-check · lint · vitest) green.
- Golden master unchanged (Stage 1 reporting-only).

## Not in scope

- Registry/anchors/engine — GRS-0080/0081/0082 (prerequisites).
- Benchmark rows — GRS-0084; deliverable sections — GRS-0085; V fold-in — GRS-0086.
