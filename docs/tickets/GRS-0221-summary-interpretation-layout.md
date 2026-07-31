# GRS-0221 — Stage 6 layout: the panels that fight each other

**Status:** Fixed, in review (2026-07-31). **Priority:** MED-HIGH. **Type:** Bug.
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

## What shipped (2026-07-31)

Measured on the rendered page before touching anything, at 1280/1440/1920 and a 640px-tall
viewport. At the worst point in the scroll, **119px of the "recommended to sell" panel was behind
the pinned Platform Value card — the card's full height — at every viewport. It is now 0px**, with
paint order confirmed by probing the element stack, not inferred from rectangles. Evidence,
harness and screenshots in `docs/reviews/GRS-0221-stage6-layout/`.

Cause: the rail's *first child* was sticky while its siblings scrolled on in the same grid column.
Took option 1 of the two in scope item 2 — **the rail sticks as one block**, so nothing shares a
column with a pinned element. The intent (keep the headline number visible) was reasonable; only
the implementation was wrong, and dropping stickiness would have discarded both.

Auditing the whole step (scope item 3) found a second instance of the same defect: the site header
is itself sticky at z-index 50, and the rail pinned at `top: 1rem` sat **44px behind it** — the
part it ate was the score card's own heading, so the pinned panel lost the label for the number it
exists to show. It pre-dates this ticket. Now pinned against the header's own token,
`top: calc(var(--topbar-height) + 1rem)`, so the two cannot drift.

Short viewports (scope item 4): sticky is dropped entirely below 700px tall; above it the rail is
capped and scrolls internally, so it cannot strand its own tail.

Five guards added to `WizardLayout.test.ts` — verified to fail against the pre-fix code, so they
are not vacuous. They guard the declarations; the geometry above is the proof, per the GRS-0209
lesson that a passing declaration test can sit on top of a visibly wrong page.
