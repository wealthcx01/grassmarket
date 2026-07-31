# GRS-0176 — Vertical Kanban for the pipeline

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: In review (2026-07-25) — vertical stage bands, no horizontal scroll, per-card select removed; PR open. **Prior._
**Loop:** founder-feedback remediation, Wave 1. Frontend only.

## Why

The board renders ten fixed 15rem columns in a horizontal `overflowX` scroll (~150rem wide), so
most stages sit off-screen on any normal viewport. The founder wants a vertical arrangement
tried instead. The stage model itself is unchanged (it aligns with Holy Corner).

## Scope

All changes in `frontend/components/KanbanBoard.tsx` (304 lines) plus one small edit to its test
file. The public props (`board`, `onOpen`, `onMove`) and the parent page
(`frontend/app/pipeline/page.tsx`) are unchanged.

1. **Bands instead of columns.** Rework `Column` (lines 177-225) into a `StageBand`: a
   full-width horizontal section per stage, stacked vertically. The outer wrapper (line 270)
   loses `overflowX: "auto"` and becomes `display: flex; flexDirection: column; gap: 0.75rem`.
   Inside a band, cards lay out with `display: flex; flexWrap: wrap; gap: 0.5rem`, each card
   `flex: 0 1 15rem` so the existing card width is kept but cards wrap instead of scrolling.
   No horizontal page scroll at any width.
   Decision on band order: bands render in the canonical `PIPELINE_STAGES` lifecycle order, top
   to bottom, not "most recently active first". A stable order is scannable and drag targets do
   not move mid-interaction; recency ordering would reshuffle the page on every move.
2. **Empty stages collapse.** A band with zero entries renders as a single slim row: the stage
   label, a zero count, and the droppable surface at reduced height (`minHeight: 2.25rem`), so
   ten stages fit one screen when the pipeline is thin. An empty band is still a valid drop
   target (the `useDroppable` ref stays on the collapsed row).
3. **Drag, click, and error behaviour unchanged.** dnd-kit sensors, the 5px activation
   constraint, `closestCorners`, the `DragOverlay`, optimistic move with 409 revert, and
   click-to-open `DealDetailPanel` all carry over as-is. Only geometry changes.
4. **Remove the per-card stage select.** Delete the `StageMoveControl` render inside
   `DraggableCard` (lines 170-172) and its import if now unused here. The keyboard/mobile
   fallback remains `StageMoveControl` inside `DealDetailPanel` (already present at
   `frontend/components/DealDetailPanel.tsx` line 336), which is one click from any card. This
   removes ten tab stops of noise per card without losing the accessible path.
5. **Band header.** Keep the stage label and count; add the count styling as-is. KPI strip,
   search, and the stale filter on the pipeline page are untouched.

## Test plan

1. `frontend/components/KanbanBoard.test.tsx` (exists) updated; run
   `bunx vitest run frontend/components/KanbanBoard.test.tsx`. Asserts:
   - All ten stage bands render, in `PIPELINE_STAGES` order, as vertically stacked sections
     (assert the accessible names appear once each and in document order).
   - A card renders inside its stage's band; clicking it calls `onOpen` with the prospect id.
   - No `<select>` renders inside a card (the per-card `StageMoveControl` is gone); asserting
     zero comboboxes within a band that has cards.
   - An empty stage renders its label with count 0 (collapsed row present, still in the DOM as
     a droppable region).
   - The board wrapper carries no `overflowX` style.
   - The existing drag/onMove simulation (or the `onDragEnd` unit path) still calls `onMove`
     with the target stage; a same-stage drop calls nothing.
2. `frontend/components/StageMoveControl.test.tsx` and `DealDetailPanel` behaviour unchanged;
   re-run `bunx vitest run frontend/components/StageMoveControl.test.tsx` to confirm no drift.
3. Manual check recorded in the PR with screenshots at 1280px, 1024px, and 375px: full pipeline
   readable top-to-bottom, no horizontal scrollbar, drag between bands works, illegal move
   snaps back with the 409 banner.
4. Standing gate: tsc, ESLint.

## Out of scope

- Any backend, stage-model, or pipeline-config change (stages stay Holy Corner-aligned).
- `DealDetailPanel`, KPI strip, search, stale filter, and win-probability logic.
- Board persistence, saved filters, or per-user layout preferences.
- Copy rewrites beyond what the moved elements require (GRS-0174 owns the sweep).

## Acceptance

The full pipeline is readable top-to-bottom without horizontal scrolling at 1280px, 1024px, and
mobile widths; a card drags between bands; the illegal-move 409 banner behaviour is unchanged;
keyboard/mobile stage moves still work from the card detail; an empty stage occupies one slim
labelled row; the updated KanbanBoard test file passes.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `6c442fe` (GRS-0176: vertical Kanban for the pipeline).

This ticket carried no *What shipped* record; the commits above are that record.
