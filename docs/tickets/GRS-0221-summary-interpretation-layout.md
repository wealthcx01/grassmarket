# GRS-0221 — Stage 6 layout: the panels that fight each other

**Status:** Planned (2026-07-26, staging review item 9). **Priority:** MED-HIGH. **Type:** Bug.
**Loop:** founder-feedback remediation, Wave 1. **Follows GRS-0182.**

## Why

The founder, on the Summary & Interpretation step:

> "The Platform Value Finalised box seems to be fixed on the [page], and then when you scroll the
> 'recommended to sell' box moves underneath, and it's not great experience."

GRS-0182 repaired the content of this step. The layout is still wrong, and it is wrong in the way
that is most annoying to a user: a sticky element overlapping the thing they are scrolling to read.
It gets its own ticket because it is a concrete, reproducible defect and should not wait behind the
report rebuild.

## Scope

1. **Reproduce and record.** Screenshot the overlap at the founder's viewport, plus 1280, 1440 and
   1920 wide, and at a short viewport height where sticky positioning misbehaves most. Say in the
   PR which widths and heights reproduce it.
2. **Decide what should be sticky, and why.** The Platform Value panel is sticky presumably so the
   headline number stays visible while reading the modules. That is a reasonable intent and the
   implementation is wrong. Either:
   - give the sticky panel its own column so nothing scrolls beneath it, or
   - stop it being sticky and let it scroll with the page.
   Pick one, state the reason in the PR, and do not leave a sticky element sharing a column with
   scrolling content.
3. **Check the whole step, not just the two panels.** The same pattern is likely to be present
   elsewhere on the step. Fix what is there rather than only the instance that was reported.
4. **Short viewports.** A sticky panel taller than the viewport is unusable. Cap its height and let
   it scroll internally, or drop stickiness below a height threshold.

## Test plan

1. Vitest on the step layout asserting the sticky panel and the scrolling column are not in the
   same grid column, or that stickiness is gone, whichever the PR chose.
2. Manual screenshots at four viewport sizes, before and after, in the PR. This is the proof; the
   unit test is the guard.
3. Standing gate: tsc, ESLint, per-file vitest.

## Out of scope

- The content of the step (GRS-0182, merged).
- The deliverable itself (GRS-0211, GRS-0219, GRS-0220).

## Acceptance

The founder scrolls the Summary & Interpretation step at their own window size and nothing slides
under anything else.
