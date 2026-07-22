# GRS-0165 — Wizard density part 2: Customer-Proposition collapse + segmented rating control

**Status:** Done (2026-07-22). The two GRS-0160 scope items that shipped for Infrastructure
only (collapse) or not at all (segmented control) — the recorded demo-readiness residual.
**Priority:** MED-HIGH. **Loop:** demo-readiness. Frontend-only (presentation; golden master untouched).

## Why

GRS-0160 fixed the Infrastructure step's endless-scroll with per-module collapse, but the Customer
Proposition step still renders 10 C-modules plus the entire Level-1 widget checklist as one flat
scroll, and BOTH rating steps still rate through a native per-row `<select>` ("— unrated —" →
option) — two clicks and a popup per rating, hundreds of times per assessment.

## Scope

1. **Customer-Proposition collapse** — the same treatment Infrastructure got: per-C-module
   collapsible cards with a "n/m rated" affordance, fully-rated modules auto-collapsed,
   Expand/Collapse-all; the widget checklist's categories collapse the same way ("n/m recorded").
2. **Segmented rating control** — replace the maturity `<select>` in the Infrastructure AND
   Customer-Proposition rows with a one-click segmented control (Basic / Developing / Advanced /
   Frontier · N/A · Not assessed). Clicking the active segment clears back to unrated. Buttons, not
   a listbox — keyboard-fast, no popup.

## Acceptance

Rating a subcomponent is one click; the Customer Proposition step reads as navigable sections, not
an endless form. No scoring-path change (presentation only).
