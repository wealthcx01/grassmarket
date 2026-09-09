# GRS-0265 — Every page scrolls sideways on a phone, because the header prints a full email address

**Status:** OPEN (found 2026-09-09). **Priority:** MED. **Type:** Bug.
**Loop:** first-time-user coherence. **Found by:** the GRS-0242 screenshot pass.

## Why

Rendering the Workbench at phone size (393×851) to check GRS-0242, the full-page capture came back
**590px wide against a 393px viewport**. The page scrolls sideways.

One element causes it. The account button in the site header renders the signed-in advisor's whole
email address — `advisor@bruntsfieldcapital.com` — with no truncation and no wrap. It measures
258px wide and ends at x=590, dragging the document's scroll width with it.

Two things follow from that, and the second is the one a user notices:

1. The whole app scrolls horizontally on a phone. The header is shared, so this is not a Workbench
   bug — it is on every authenticated page.
2. **Content that should wrap does not.** Because the body is laid out 590px wide, the Bench "My
   performance" list positions its values against the wider box: every value sits at x=471, off the
   right of a 393px screen. The advisor's level, their pipeline conversion and their exam result
   are all pushed out of sight rather than wrapping into view. The Bench also keeps its two-column
   layout, because the columns are computed against 590px and never reach the breakpoint that
   would stack them: "Continue the Academy: Sales Egoist" wraps down five lines in a column about
   180px wide, beside a performance list the reader cannot fully see.

Confirmed pre-existing: `main` reproduces it identically at the same 590px, so GRS-0242 did not
introduce it. It has simply never been looked at on a phone.

## Scope

1. The header account control fits its container at 393px. Truncate the email with an ellipsis,
   or show only the part before the `@`, or collapse to the avatar alone below a breakpoint —
   whichever reads best when rendered. The full address stays available in the opened menu.
2. `document.documentElement.scrollWidth` equals the viewport width at 393px on every
   authenticated route. No horizontal scroll anywhere.
3. Re-render the Bench performance list afterwards and confirm its values wrap into view rather
   than sitting off-screen.

## Test plan

1. A Playwright assertion at 393×851 that `scrollWidth <= clientWidth` on the authenticated routes
   — the cheap check that stops this whole class of bug returning.
2. Screenshots at 1440×1000 and 393×851, before and after, in the PR.
3. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- Any other header or navigation change. This is the overflow only.

## Acceptance

The founder opens any page on a phone and cannot scroll it sideways, and the Bench performance
values are all on screen.
