# GRS-0182 — Summary & Interpretation repair

**Status:** Planned (2026-07-23, founder feedback item 10). **Priority:** HIGH.
**Loop:** founder-feedback remediation, Wave 1. Frontend only.

## Why

Verified on staging (finalised Revolut demo): the Rating Committee panel renders
"8 awaiting sign-off … before this assessment can be finalised" on an assessment that IS
finalised; the V score block renders twice (the step's own sticky LiveScorePanel plus the rail's
LiveSummary); the radar and waterfall SVGs use fixed pixel geometry that collides with long
labels; and the 20rem rail grid has no responsive breakpoint. The founder: "the UI/UX on the
Summary and Interpretation page is broken".

## Scope

Frontend only, inside `SummaryStep` and the three diagnostic sub-panels; no API, no engine, no
contract change. GRS-0188 later retires the governance panels entirely — this ticket ships the
live trust fix first, because a finalised demo record showing "awaiting sign-off" is a
credibility bug the founder is looking at now.

1. **The double-V bug — one score display.** In `frontend/components/steps.tsx` `SummaryStep`
   (around lines 1227-1389), REMOVE the embedded `<LiveScorePanel>` (lines 1235-1244). The
   always-visible rail (`LiveSummary` in `WizardClient.tsx`, already sticky and already headlining
   the locked/live V through `BandDisplay`/`LockedScore`) becomes the single V display. The Summary
   column now leads with the interpretation narrative (`Interpretation`, §4). Decision: keep the
   rail and drop the in-column panel, not the reverse, because the rail is visible on every step and
   is already the canonical one-number surface (ADR-0040); a second sticky panel inside the flow
   column was the duplication. The `L/B/P` breakdown, bottleneck, and module table that
   `LiveScorePanel` showed are preserved because `DiagnosticsPanel` already renders the module
   radar, the B→P→L→V waterfall, and the κ-annotated module table lower in the same step; the only
   thing lost is the redundant V headline.

2. **Governance panels tell the truth about state** (`SummaryStep`, the `DualRatingPanel` /
   `CommitteeReviewPanel` block around lines 1278-1286). Today `DualRatingPanel` renders only when
   `!readOnly` and `CommitteeReviewPanel` renders whenever `live?.scoreable`, so a FINALISED
   (`readOnly === true`) assessment still shows the committee panel with its pre-finalisation
   "awaiting sign-off" framing. Fix by branching on lifecycle state:
   - **Finalised** (`readOnly === true`): render neither the interactive dual-rating nor the
     "awaiting sign-off" committee panel. In their place render a compact, read-only **governance
     record** card: for a production record, "Finalised — inputs locked" plus whatever
     approval/consensus facts the already-fetched data exposes (rater/committee state as a recorded
     fact, past tense), never a call to action. For a demo/sandbox record, a one-line
     "Self-approved sandbox path — watermarked, never client-facing" note (the same posture the
     finalise confirm already states for the sandbox path). Decision: show the record, not the
     workflow, because on a locked assessment the governance step is history, not a to-do.
   - **Draft** (`!readOnly`): unchanged behaviour — the interactive `DualRatingPanel` and the
     `CommitteeReviewPanel` with its "awaiting sign-off before finalisation" framing are correct
     here, because finalisation genuinely is still ahead.
   Reuse the assessment `provenance` prop already threaded into `SummaryStep` to pick the
   production-vs-sandbox record copy. No new endpoint: the record uses data the step already holds.

3. **Responsive and robust charts** (`frontend/components/Diagnostics.tsx`).
   - **Radar** (`QmRadar`, around lines 44-108): already uses a `viewBox`; keep the intrinsic
     `viewBox="0 0 260 260"` but drop the fixed `width={size} height={size}` attributes in favour of
     `width="100%"` with `style={{ maxWidth: 260, height: "auto" }}` so it scales down inside a
     narrow rail/column without horizontal scroll. Add a label-length guard: truncate a spoke label
     to a sensible max (about 14 chars) with an ellipsis and put the full module name in a `<title>`
     child of the `<text>` so the collision with long module names (e.g. "Customer Trading
     Experience") stops. The `overflowX: auto` wrapper stays as a last-resort safety.
   - **Waterfall** (`ValueWaterfall`, around lines 112-177): today `width`, `labelW`, `barW`, and
     row geometry are fixed pixels. Convert to a `viewBox`-scaled SVG: keep the internal coordinate
     system (compute `width`/`height` as the viewBox as now) but render with `width="100%"
     preserveAspectRatio="xMinYMin meet"` and a `style={{ maxWidth: width }}` so it never overflows
     its panel and scales on small screens. Guard the row labels the same way (truncate + `<title>`)
     so a long lens label does not run under the bar. Keep the `overflowX: auto` wrapper.
   - `ModuleTable` already scrolls inside `overflowX: auto`; no change beyond confirming it stays
     wrapped.
4. **Responsive rail — breakpoint below ~900px.** The two-column grid in `WizardClient.tsx`
   (`gridTemplateColumns: "minmax(0,1fr) 20rem"`, around line 363) has no breakpoint, so on a
   phone/tablet the 20rem rail crushes the content column. Add a responsive rule so that below
   ~900px the grid collapses to a single column (`gridTemplateColumns: "1fr"`) with the rail
   stacked below the content. Decision: implement with a small CSS class in the app stylesheet (a
   media query at `max-width: 900px`) applied to the grid wrapper, rather than inline styles, because
   inline styles cannot hold a media query and this is the one place a breakpoint is needed. The rail
   ceases to be `position: sticky` at that width (a sticky element in a single stacked column just
   pins to the top oddly), reverting to normal flow. Name the class e.g. `wizard-two-col`.

5. **Story order in the Summary column**, in the STYLE-VOICE register: headline (now carried by the
   rail) → **what this means** (the `Interpretation` card, already first content after the removed
   panel) → **how V builds up** (the waterfall) → **module detail** (radar + module table) → the
   **governance record** (§2). Reorder the JSX in `SummaryStep` so `DiagnosticsPanel` sits after
   `Interpretation` and the governance record sits last before the finalise controls (draft) or the
   "finalised — locked" note (finalised). The `DeliverablePreviewButton`, the C-index card, the
   Platform Power triad card, and the finalise/sandbox controls keep their existing positions
   relative to this spine.

## Test plan

Frontend, vitest, per file. `tsc`, ESLint, `pyright` are the standing gate.
`uv run pytest tests/test_atlas_engine_golden_master.py` proves the scoring path is untouched.

1. `bunx vitest run frontend/components/steps.test.tsx` (extend/create) — `SummaryStep`:
   - **No double V:** rendering `SummaryStep` with a scoreable `live` produces exactly one element
     labelled "V — PLATFORM VALUE" (the embedded `LiveScorePanel` is gone). Assert the query for the
     V label returns a single node within the step (the rail is a separate component/tree).
   - **Finalised governance record:** with `readOnly=true` and `provenance="production"`, the step
     renders the read-only governance record card and does NOT render the "awaiting sign-off" text
     nor an interactive dual-rating control. With `readOnly=true` and `provenance="sandbox"`, it
     renders the self-approved-sandbox note.
   - **Draft unchanged:** with `readOnly=false`, the interactive `DualRatingPanel` renders and the
     pre-finalisation committee framing is present.
   - **Order:** the interpretation card precedes the diagnostics, which precede the governance record
     (assert DOM order).
2. `bunx vitest run frontend/components/Diagnostics.test.tsx` (extend/create):
   - The radar and waterfall SVGs render with a `viewBox` and without fixed `width`/`height` pixel
     attributes (assert `getAttribute("viewBox")` present, `width === "100%"`).
   - A module/lens label longer than the guard length is truncated in the visible `<text>` and its
     full name appears in a `<title>` child.
3. `bunx vitest run frontend/app/assessments/[id]/WizardClient.test.tsx` (extend/create):
   - The grid wrapper carries the `wizard-two-col` class (the breakpoint hook); a jsdom width probe
     is not reliable, so assert the class is applied rather than the computed columns.
4. **Manual responsive check, recorded in the PR:** a finalised assessment's Summary at 1280px,
   1024px, and a mobile width (~375px) shows one V, a truthful governance record, and no horizontal
   overflow or label collision on the radar/waterfall. Screenshots attached.

## Out of scope

- Retiring or deleting the governance panels, routes, or the dual-rating/committee machinery — that
  is GRS-0188. This ticket only makes their *display* truthful for the finalised state
  (one-ticket-one-PR).
- Any change to `live`, the scoring engine, uncertainty, the value bridge, or contracts.
- The report storytelling rebuild (GRS-0189) and the founder review gate (GRS-0188).
- Restyling the rail's content or the interpretation copy beyond the register/order changes above.

## Acceptance

A finalised assessment's Summary shows exactly one V (the rail), a truthful past-tense governance
record with no "awaiting sign-off" call to action, and no broken or colliding layout at 1280px,
1024px, and mobile widths — the radar and waterfall scale and never collide with long labels, and
the rail collapses below ~900px. Draft assessments are unchanged except for the copy/order edits.
The golden-master test stays green.
