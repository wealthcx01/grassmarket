# GRS-0280 — The Workbench still scrolls sideways on a phone: the Bench's two columns never stack

**Status:** OPEN (filed 2026-10-08). **Priority:** HIGH — `main`'s CI is red until this is fixed.
**Type:** Bug. **Follows:** GRS-0279. **Found by:** GRS-0279's phone test.

## Why

GRS-0279 fixed the header that made every signed-in page scroll sideways on a phone. One page is
still too wide: **`/workbench` is 471px wide on a 393px screen.** On a phone, the advisor's level,
pipeline conversion and exam result in "My performance" still sit partly off the right edge.

It also matters for everyone working in this repo: **`main`'s CI has been red since GRS-0279 merged
(PR #284, 2026-10-08).** GRS-0279 added a browser test, `frontend/e2e/mobile-overflow.spec.ts`, that
checks thirteen signed-in pages at 393×851 and fails if any is wider than the screen. It fails on
`/workbench` only:

> `Error: /workbench is 471px wide on a 393px screen` (CI run 37787953928, job "E2E (Playwright)")

Until it passes, every pull request's E2E job is red too, so a real new failure would be easy to miss.

## The cause

The Bench tab lays out "Your next actions" and "My performance" side by side with a fixed inline
grid in `frontend/components/workbench/BenchDashboard.tsx`:

```tsx
<div style={{ display: "grid", gap: "1.5rem", gridTemplateColumns: "minmax(0, 1.3fr) minmax(0, 1fr)" }}>
```

There is no phone breakpoint, so the two columns never stack. GRS-0279's "What shipped" section has
the measurements: after the header fix, twelve of the thirteen pages are exactly 393px wide; this
one is 471px, with the performance values at x=334–471.

## Scope

1. Below the app's phone breakpoint (`40rem`, the one GRS-0279 used for the header), the Bench's two
   sections stack: "Your next actions" first, then "My performance", each full width. Move the
   inline grid into a class in `globals.css` (or the component's existing styling pattern) so it can
   have a media query.
2. Above the breakpoint, nothing changes: the desktop Workbench looks and measures the same.
3. Check that nothing else inside the Bench is wider than the screen once the columns stack (for
   example the performance list's values and the long action titles). Fix only what is needed for
   the page to fit.

## Test plan

1. The existing browser test `frontend/e2e/mobile-overflow.spec.ts` passes, with no change to it.
   **Note:** it checks the pages in order and stops at the first failure, so in CI it has never yet
   reached the five pages after `/workbench` (`/workbench/academy`, `/workbench/courses`, `/guide`,
   `/profile`, `/settings`). GRS-0279 measured them locally at 393px. Once this ticket's change is
   in, the test reaches them for the first time: if one of them fails, fix it here only if the fix is
   as small as this one; otherwise record it in "What shipped" and file the next ticket.
2. Screenshots of the Workbench's Bench tab at 1440×1000 and 393×851, before and after, in the PR,
   with each page's height. The desktop height should not change (1000px today).
3. Standing gate: the repo's `## Checks` (pytest, pyright, tsc, ESLint, vitest). The browser tests are
   not in that list and don't run on the planning box, so **the PR's own CI "E2E (Playwright)" job is
   the proof**: it must be green before this ticket is done.

## Out of scope

- Any other Workbench or header change. This is the Bench's phone layout only.
- Changing the phone test itself, for example skipping `/workbench`.

## Acceptance

- On a 393px phone, the Workbench's Bench tab does not scroll sideways, and the level, pipeline
  conversion and exam result are all on screen.
- On a desktop, the Bench looks the same as before.
- `main`'s CI is green again: the "E2E (Playwright)" job passes on this ticket's PR and after merge.

## What shipped

**The change.** The Bench's two-column grid moved out of an inline style in
`frontend/components/workbench/BenchDashboard.tsx` and into a `.bench-dashboard` class in
`frontend/app/globals.css`, next to GRS-0279's phone rule. The desktop values are exactly the old
ones. Below `40rem` the grid drops to one column, so "Your next actions" comes first and "My
performance" sits underneath it at full width. No other change was needed: once the columns stack,
nothing inside the Bench is wider than the screen. The phone test was not changed.

**Measured locally** (signed in as the seed advisor, on the CI-style sqlite database, Chromium):

| Bench tab | Before: width × height | After: width × height |
| --- | --- | --- |
| Phone, 393×851 | **471px** × 1,127px | **393px** × 1,201px |
| Desktop, 1440×1000 | 1,440px × 1,000px | 1,440px × 1,000px |

- On the phone, "before" reproduces the CI failure exactly: the performance values (level, pipeline
  conversion, exam result and the rest) ended at x=471. "After", every element ends inside the
  screen, and the level line ("Certified Lead · set outside the ladder") fits on one row.
- The phone page is 74px taller because the two sections now sit one above the other.
- On the desktop, the before and after screenshots are byte-for-byte the same file.

**The five pages the phone test had never reached.** `frontend/e2e/mobile-overflow.spec.ts` was run
locally against this change and passes on all thirteen pages. The five newly reached pages, at 393px:

- `/workbench/academy`: 393px wide, 1,454px tall.
- `/workbench/courses`: 393px wide, 856px tall.
- `/guide`: 393px wide, 26,579px tall. One table (the operating-model weights) is 442px wide, but it
  sits in its own sideways-scrolling box, so the page itself does not scroll sideways. That is the
  intended design, not a fault.
- `/profile`: 393px wide, 885px tall.
- `/settings`: 393px wide, 851px tall.

So no follow-up ticket is needed for phone width. The remaining proof is the pull request's own CI
"E2E (Playwright)" job, which has to be green before this ticket is done.
