# GRS-0055 — UX audit fixes (Robinhood-rubric pass)

- **Loop:** 2 / 3 (wizard + pipeline UX)
- **Status:** Fixed — from the 2026-07-15 UI/UX audit against a Robinhood-derived design rubric.
- **Severity:** Low/Medium — first-impression clarity, no correctness impact.
- **Rubric basis:** #2 (one-glance headline metric), #3 (progressive disclosure — show what the
  task needs now), #10 (informative empty states).

## Findings & change

1. **Finalised assessment led with a blank form, not the score (rubric #2/#3).** Opening a
   *finalised · locked* assessment landed on step 1 "Overview" — an empty Subject/Notes form the
   advisor can't edit — while the scored result sat two steps away. A finalised assessment is opened
   to be *read*, so it now defaults to the "Summary & Interpretation" step (V, the bottleneck, the
   weakest-first modules, and the honest uncertainty), which is what the advisor came for.
2. **Empty pipeline stages were blank voids (rubric #10).** An empty kanban column rendered nothing,
   reading as broken. Each empty stage now shows a muted "No prospects" placeholder, so empty reads
   as intentionally empty.

## Not changed (deliberate, per the rubric's [caution] tags)

The audit confirmed the product correctly *avoids* the Robinhood anti-patterns: no gamification /
confetti / streaks on finalising an assessment (#14), honest P10/P50/P90 + coverage + "uncertainty
Very High" shown as prominently as the headline (#9), two-track ordinal words never dressed as
decimals (#6/#15), and the Internal-draft default on client deliverables (#8/#15). Those are kept.

## Exit criteria

- A finalised assessment opens on the Summary step; every empty pipeline stage shows the placeholder
  — pinned by `KanbanBoard.test.tsx` and verified visually. Type-check / lint / build green.
