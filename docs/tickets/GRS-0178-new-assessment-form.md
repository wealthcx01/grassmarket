# GRS-0178 — New-assessment creation form redesign

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: In review (2026-07-26) — grid layout shipped, PR open (stacked on GRS-0177)._
(2026-07-23, founder feedback item 5.) **Priority:** MED.
**Loop:** founder-feedback remediation, Wave 1. Frontend only.

## Why

The creation controls sit in one flex row with `alignItems: flex-end` and the sandbox checkbox
hacked into vertical alignment with a magic-number `paddingBottom: "0.55rem"`
(frontend/app/assessments/page.tsx:162-214). The founder: the type box and Operating Model
dropdown "are not even aligned" and may not be in the right positions at all.

## Scope

All changes in `frontend/app/assessments/page.tsx` (the `<form>` at lines 162-214). Submission
behaviour (`onCreate`, lines 122-146), `EntitySubjectField`, and the wizard's own Overview
profile selector are untouched.

1. **Grid layout.** Replace the flex row with a two-row grid:
   - Row 1: `display: grid; gridTemplateColumns: "minmax(0, 2fr) minmax(0, 1fr) auto";
     gap: 0.75rem; alignItems: end`. Cell 1 is the subject field, cell 2 the operating-model
     select, cell 3 the "Create & open" button. Each labelled field uses the same structure:
     a block label (`display: block; marginBottom: 0.3rem; fontWeight: 500`) above the input,
     so the two inputs share one baseline by construction and the button bottom-aligns with
     them via `alignItems: end` on real content, not padding.
   - Row 2: the sandbox option on its own full-width line beneath
     (`gridColumn: "1 / -1"`), a checkbox followed by the GRS-0177 plain-register explanation
     as visible helper text beside it (not only a `title` tooltip).
   - Below roughly 40rem the grid stacks: wrap the columns with
     `gridTemplateColumns: "minmax(0, 1fr)"` via a small CSS class in
     `frontend/app/globals.css` (inline styles cannot carry media queries). Class name
     `form-create-assessment`, defined once with the breakpoint.
   - Delete the `paddingBottom: "0.55rem"` magic number and the `flex-end` row.
2. **Decision: single-step form, no two-step flow.** The earlier draft left a two-step split
   open; the grid resolves the alignment complaint without adding navigation, and three fields
   do not justify a wizard. If the founder still finds it cramped after seeing it, that is a
   new ticket with the screenshot evidence.
3. **Field semantics unchanged.** Subject + optional entity id from `EntitySubjectField`,
   profile select defaulting to retail (non-default saved after create exactly as today, lines
   133-140), sandbox checkbox mapping to provenance on `createAssessment`. Copy for labels and
   helper text follows STYLE-VOICE (GRS-0174).

## Test plan

1. `bunx vitest run frontend/app/assessments/page.test.tsx` (created by GRS-0177; extend here,
   or create if this ticket lands first):
   - The form renders subject, operating-model, and submit in one grid row and the sandbox
     option on its own row (assert grid classes/inline styles and DOM order).
   - No element in the form carries a `paddingBottom` inline style (the magic number is gone).
   - Submitting with a subject calls `api.createAssessment(subject, "production", entityId)`
     and routes to the new assessment; with the sandbox box ticked it passes `"sandbox"`.
   - With a non-retail profile selected, `api.saveAssessment` is called with the profile-set
     document after creation; with retail it is not called (the byte-clean retail rule).
   - The sandbox helper text is visible in the DOM (not only a title attribute).
2. Manual screenshots in the PR at 1280px, 1024px, and 375px showing the shared baseline and
   the stacked mobile layout.
3. Standing gate: tsc, ESLint.

## Out of scope

- Backend/API changes of any kind; `createAssessment` and `saveAssessment` are used as-is.
- The portfolio table, grouping, and demo-note work (GRS-0177).
- The wizard Overview step's duplicate Operating Model selector (explicitly unchanged).
- Redesigning `EntitySubjectField` internals.

## Acceptance

Fields align on a shared grid at every viewport width, stacking cleanly below the breakpoint;
no magic-number spacing remains in the form; the sandbox option sits on its own line with its
explanation visible; creating an assessment (retail and non-retail profile, production and
sandbox) behaves exactly as before, asserted by test.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `66fd529` (GRS-0178: align the new-assessment form by structure).

This ticket carried no *What shipped* record; the commits above are that record.
