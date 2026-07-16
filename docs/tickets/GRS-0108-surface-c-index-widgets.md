# GRS-0108 — Surface the widget checklist + Customer Proposition Index in the wizard

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Phase:** A (build now)
**Depends on:** ADR-0023 (C-index) / GRS-0080–0085

## Why

The founder was emphatic here — "so crucial, we're missing the point": the widget checklist
(present/absent per widget) and the **Customer Proposition Index** (Ease / Usability / Depth feeding the
C-index) are the heart of judging how good a platform actually is, yet they're buried. The C-index and
its widget scoring already exist as Part-1 work (ADR-0023 / GRS-0080–0085); this ticket is a
**surfacing/prominence** job, not new computation — bring the widget checklist and C-index forward in
the wizard as a first-class, prominent step so advisors treat it as central rather than incidental.

## What to build

**Wizard (`components/steps.tsx`, `app/assessments/[id]/WizardClient.tsx`)**
- Present the widget checklist (present/absent) and the Ease / Usability / Depth inputs feeding the
  C-index as a prominent, first-class step in the flow.
- REUSE the Part-1 C-index computation and widget scoring (GRS-0080–0085) — this ticket surfaces and
  elevates them, it does not re-implement the index.

## Acceptance / verification

- The widget checklist and C-index (Ease/Usability/Depth) appear as a prominent wizard step, not a
  buried afterthought.
- The surfaced inputs feed the existing Part-1 C-index computation unchanged.

## Not in scope

- The C-index computation and widget model itself — GRS-0080–0085.
- Screen-recording → AI auto-population of the checklist — GRS-0109 (Phase B).
