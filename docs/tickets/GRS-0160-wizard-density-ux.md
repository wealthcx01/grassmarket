# GRS-0160 — Assessment wizard density UX pass (the core "clunky" fix)

**Status:** Done (2026-07-21). Infrastructure step now collapsible; live rail was already sticky. From the founder's "clunky, hard to use" feedback + the staging audit.
**Priority:** HIGH — the headline UX debt. **Loop:** demo-readiness. Frontend-led.

## Why

The wizard content and microcopy are excellent and the design system is clean, but the **dense rating
steps** make it feel like work. The Infrastructure Deep Dive is a single ~5,100px page: 51 subcomponents
across 9 modules, each a native `<select>` ("— unrated —") + Guidance button, stacked vertically with no
collapse. The Customer Proposition repeats it for the widget checklist; Powers is 7 benefit/barrier cards.
Completing one assessment = hundreds of dropdown selections down a long scroll, with **no bulk-fill, no
per-module N/A, no collapse of finished modules**, and the live-score rail only at the top so the score
leaves the viewport as you scroll.

## Scope (interaction model, not content)

- **Sticky live-score + coverage rail** that stays in view while scrolling the long steps.
- **Per-module collapse/expand with a progress affordance** (e.g. "Front End 4/6 · Advanced"); collapse
  completed modules by default.
- **Faster rating control** — replace the native per-row `<select>` with a segmented control
  (Basic/Developing/Advanced/Frontier · N/A · Not Assessed) that rates in one click and is keyboard-fast.
- **Bulk actions** — "mark this module Not Applicable / Not Assessed", and a quick way to set a module
  baseline then override outliers.
- Apply the same to the Customer Proposition step.

## Acceptance

A realistic assessment can be completed in a fraction of the clicks, the score stays visible, and the
Infrastructure/Customer-Proposition steps no longer read as an endless form. Golden master untouched
(this is presentation only).
