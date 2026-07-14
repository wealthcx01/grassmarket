# GRS-0036 — UI audit: pipeline board + forecast overflow (not responsive)

- **Loop:** UI retro-audit (grs-ui-retro-audit)
- **Status:** Triage — found in the 2026-07-14 visual retro-audit; NOT yet fixed.
- **Severity:** High — the pipeline is the CRM's main screen (GRS-0014) and it's broken on mobile.
- **Found by:** Visual audit of the CI screenshot gallery (first-ever visual verification of the
  frontend). Repro screenshots: `assets/ui-audit-pipeline.desktop.png`,
  `assets/ui-audit-pipeline.mobile.png`.

## Defects

1. **Kanban board overflows horizontally with no scroll affordance.** The ten pipeline stages don't
   fit the viewport; only ~4.5 columns show on desktop (1280px) and ~1.5 on mobile (390px). The rest
   ("Scoped", "Contracted", "Active"…) run off the right edge with no scrollbar, gradient, or arrow
   to signal there's more. **A prospect in a later stage is invisible** — the seeded "Contracted"
   prospect can't be seen on the board at all without discovering the horizontal scroll.

2. **Forecast panel is not responsive.** Its header ("deal volume · not £-denominated") is truncated
   at the right edge on desktop, and on mobile the entire forecast card **and** its
   Stage/Count/P(win)/Weighted table overflow the viewport — the card's right border and the
   "Weighted" column are clipped off-screen.

## Repro

Seed + run the app (`scripts/seed_dev.py`), log in as the demo advisor, open `/pipeline` at 1280×800
and 390×844. See the attached screenshots.

## Suggested direction (not prescriptive — for the implementing ticket)

- Give the kanban a horizontal scroll container with a visible affordance (scrollbar / edge fade),
  or a responsive layout that reflows stages (e.g. a stage picker + single-column list on narrow
  viewports).
- Make the forecast panel responsive: allow the table to scroll within its own container
  (`overflow-x: auto`) and stop the header text from clipping.

## Exit criteria (for the fix ticket, later)

- No horizontal clipping of the forecast at ≥360px; the table scrolls within its card if needed.
- The kanban either fits, reflows, or scrolls with a clear affordance; every stage (and any prospect
  in it) is reachable.
