# GRS-0181 — Wizard pagination: smaller pages per module

**Status:** In review (2026-07-26) — both steps paged, show-all preference and sub-step
stepper shipped; PR open (stacked on GRS-0182).
(2026-07-23, founder feedback item 9.) **Priority:** MED-HIGH.
**Loop:** founder-feedback remediation, Wave 1. Frontend only; document autosave and engine untouched.

## Why

Density work (GRS-0160/0165) made the long steps collapsible, and the founder acknowledges the
improvement — but the instinct now is that "a long list may be daunting to an advisor, but lots
of smaller pages may be easier to handle". The Infrastructure step is still 9 modules / 51
subcomponents on one page; Customer Proposition is 10 C-modules plus the widget checklist.

## Scope

This is a presentation-only change inside two step components. Nothing about the shared
`AssessmentDocument`, the `update`/autosave path in
`frontend/app/assessments/[id]/WizardClient.tsx`, the live-score fetch, or any engine input
changes. The same one-click segmented `RatingControl` rows, `GradeSelect`, evidence inputs, and
`GuidancePanel` render exactly as today; only WHICH module's rows are on screen changes.

1. **A shared module-pager hook/component** in `frontend/components/steps.tsx` (kept in this file
   next to its only two callers; no new shared file, because it depends on the step-local
   registry/doc shapes and has no other consumer). New local component
   `ModulePagedSection({ modules, showAllKey, renderModule, ratedCount })`:
   - Holds `activeIndex` state (default 0) and reads/writes the "show all modules" preference
     (see §4). When "show all" is on, it renders every module stacked (today's collapsible view,
     preserved verbatim by delegating to the existing per-module render). When off, it renders only
     `modules[activeIndex]`.
   - Renders a **jump list**: one chip per module showing the module name and its `n/m` rated
     progress (reusing the exact count logic already computed in
     `InfrastructureDeepDiveStep`/`CustomerPropositionStep` — `rated = subcomponents with level != null`).
     The active module's chip is marked `data-active`; a fully-rated module's chip shows the ✓ the
     `SectionHeader` already uses. Clicking a chip sets `activeIndex`.
   - Renders **Previous module / Next module** controls under the module body, disabled at the ends,
     that step `activeIndex`. Decision: previous/next move between MODULES, not subcomponents, so an
     advisor never lands mid-module; subcomponents stay on one screen per module (the founder's
     "smaller pages" is per-module, and 51 one-subcomponent pages would be worse, not better).
   - On module change, scroll the step container to its top (`scrollIntoView` on the section
     wrapper) so a long module does not leave the advisor scrolled halfway down the next one.

2. **`InfrastructureDeepDiveStep`** (`steps.tsx`, currently around lines 641-766): wrap the
   `registry.modules.map(...)` body in `ModulePagedSection`. Each module still renders through the
   existing `SectionHeader` + `Card` + `RatingControl` block unchanged. When paged (not "show all"),
   the per-module collapse caret is redundant and is hidden — a paged module is always expanded,
   because it is the only thing on screen; the "Expand all / Collapse all" button is replaced by the
   "show all modules" toggle (§4). When "show all" is on, the collapse behaviour returns exactly as
   today. The intro paragraph ("Work each of the {n} modules…") stays above the pager.

3. **`CustomerPropositionStep`** (`steps.tsx`, currently around lines 861-1104): apply the same
   `ModulePagedSection` to `registry.c_modules`. The **Level-1 widget checklist** is appended as one
   final virtual page after the last C-module (a page whose body is the existing widget-category
   block), so the pager covers "10 C-modules + widget checklist" as 11 pages. The `cModelled ===
   false` early-return branch (non-retail segments with no C taxonomy) is untouched — no modules,
   nothing to page, it renders its single explanatory card as today. The `showGrid` scoping of the
   widget checklist to the widget profile is unchanged.

4. **"Show all modules" preference (per user, persisted).** A toggle in each paged step's header
   ("Show all modules on one page" ⇄ "Page through modules"). Persistence:
   `localStorage` under the key `gm:wizard:show-all-modules` holding `"1"` or `"0"`. Decision:
   localStorage, not a backend/account preference and not per-assessment state, because this is a
   personal display habit that should follow the advisor across every assessment on this device
   without a round-trip or a migration — it is a reading preference, exactly like the GRS-0177
   demo-note key, not account data. Read once on mount (guarded for SSR: `typeof window`), default
   OFF (paged) so a first-time advisor gets the smaller pages the founder asked for. The toggle is
   shared by both steps through the one key, so setting it in Infrastructure also pages Customer
   Proposition.

5. **Sub-step-aware Stepper** (`WizardClient.tsx`, `Stepper`, around lines 401-419). The stepper
   pill for a paged step shows the sub-position when that step is active and paging is on, e.g.
   "4. Infrastructure Deep Dive · module 3 of 9". Implementation: the paged step reports its
   `(activeIndex, total)` up to `WizardClient` via a lightweight callback prop threaded through
   `StepProps` (new optional `onSubStepChange?: (label: string | null) => void`), and `WizardClient`
   holds a `subStepLabel` string it appends to the active pill's text. Decision: a callback, not
   lifting the whole pager state into `WizardClient`, keeps the paging logic local to the step and
   the orchestrator ignorant of registry shapes; a `null` label (show-all mode, or a non-paged step)
   renders the plain pill. The label clears when the active step changes.

6. **The live-score rail stays visible throughout.** No change to the two-column grid in
   `WizardClient.tsx` (`gridTemplateColumns: "minmax(0,1fr) 20rem"`) or the `LiveSummary` rail; the
   pager lives entirely inside the left column, so the rail is on screen on every module page. This
   is stated explicitly so no one "helpfully" moves the rail into the pager.

## Test plan

Frontend, vitest, per file. `tsc`, ESLint, and `pyright` (unaffected — no Python) are the standing
gate. `uv run pytest tests/test_atlas_engine_golden_master.py` proves no scoring input moved.

1. `bunx vitest run frontend/components/steps.test.tsx` (extend, or create if absent):
   - **Paged default:** with `gm:wizard:show-all-modules` unset, `InfrastructureDeepDiveStep`
     renders exactly one module's subcomponents (assert the second module's first subcomponent name
     is NOT in the document) plus a jump list with one entry per registry module.
   - **Jump + next/previous:** clicking the third module's jump chip renders that module and hides
     the first; "Next module" from the last module is disabled; "Previous module" from the first is
     disabled.
   - **Progress in jump list:** a module with all subcomponents rated shows its `m/m ✓`; a partially
     rated one shows `n/m`. Assert the counts match the number of rated subcomponents in the mock
     document.
   - **Rating still flows through `update`:** rating a subcomponent on the active module calls
     `update` with the same doc mutation as before (spy on the `update` prop) — the pager does not
     intercept or alter edits.
   - **Show-all toggle:** toggling "Show all modules" sets the localStorage key to `"1"`, renders
     every module at once, and restores the collapse caret; reloading the component with the key set
     starts in show-all mode.
   - **Customer Proposition widget page:** `CustomerPropositionStep` pages the C-modules and exposes
     the widget checklist as the final page; the `cModelled=false` branch renders its single card and
     no pager.
2. `bunx vitest run frontend/app/assessments/[id]/WizardClient.test.tsx` (extend, or create):
   - The stepper pill for the active paged step shows "module k of n"; switching to a non-paged step
     (e.g. Overview) clears the sub-step label; enabling show-all clears it too.
   - The live-score rail (`LiveSummary`) is present in the DOM while a paged step is active.

## Out of scope

- Any change to `update`, autosave debounce, `persist`, `refreshLive`, or the document/registry
  contracts — paging is view-only (one-ticket-one-PR).
- Paginating the other five steps (Overview, Business Metrics, Powers, Summary, Scenarios); they are
  short enough and out of scope for this ticket.
- A backend/account-level display preference or any migration — the preference is localStorage only.
- Subcomponent-level pagination; pages are per-module by decision (§1).
- Re-theming, restyling, or re-copying the rating rows themselves.

## Acceptance

An advisor can complete Infrastructure one module at a time — each screen shows a single module's
subcomponents, a jump list with per-module `n/m` progress, and previous/next module controls —
without ever seeing a 5,000px page. The stepper reads "module k of n" for the active paged step.
A "show all modules" toggle restores the single-page collapsible view and its choice persists per
user across assessments (localStorage `gm:wizard:show-all-modules`). The live-score rail is visible
on every page. Autosave, scoring, and the golden master are untouched (proven by the golden-master
test staying green).
