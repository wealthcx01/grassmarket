# GRS-0221 — Stage 6 layout: the panels that fight each other

The founder, on Summary & Interpretation:

> "The Platform Value Finalised box seems to be fixed on the [page], and then when you scroll the
> 'recommended to sell' box moves underneath, and it's not great experience."

Measured on the running page before changing anything, at the three widths GRS-0209 used plus the
short viewport the ticket asks about. Same harness both sides: `measure-rail.mjs`.

## What was measured, and why these numbers

A single scroll position proves nothing here — the defect is something you see *while* scrolling.
The harness sweeps the whole scroll range in 60 steps and keeps the **worst overlap that is
actually on screen**, then parks the page there so the screenshot shows that exact moment.

(First attempt measured at half-document and reported a 621px overlap. That was wrong: at that
scroll position the sell panel has already travelled above the viewport, so the rectangles overlap
but nothing is visible. Rectangle overlap is not the complaint; covered pixels are.)

Overlapping rectangles also aren't proof one is painted over the other, so `coveredByScoreCard`
probes the actual paint stack with `elementsFromPoint` at a point inside both.

| Viewport | overlapPx | covered | underHeaderPx | unreachablePx |
|---|---|---|---|---|
| 1280×950 | **119 → 0** | true → false | **44 → 0** | 0 → 0 |
| 1440×950 | **119 → 0** | true → false | **44 → 0** | 0 → 0 |
| 1920×1080 | **119 → 0** | true → false | **44 → 0** | 0 → 0 |
| 1440×640 (short) | **119 → 0** | true → false | **44 → 0** | 0 → 0 |

119px is the full height of the Platform Value card: at the worst point the sell panel was behind
**all** of it. It reproduces identically at every width, so it was never width-dependent.

## The cause, and what was changed

The rail's **first child** was sticky while its siblings — the suggestions panel, and the
"recommended to sell" panel on a finalised assessment — kept scrolling in the **same grid column**.
A sticky element must never share a column with content that scrolls past it.

Of the ticket's two options, this takes the first: **the rail sticks as one block**. The intent
behind the original stickiness (keep the headline number visible while reading the modules) is
reasonable — the implementation was what was wrong. Sticking the container preserves the intent and
removes the fight, where dropping stickiness would have removed both.

## A second defect, found by auditing the step

Scope item 3 asks to check the whole step rather than only the reported panels. Grepping every
sticky element in the wizard turned up one more, and it was the same defect one layer up:

The site header is itself sticky at `z-index: 50`. Pinned at `top: 1rem`, the rail sat **44px
behind it** — and the part it swallowed was the score card's own heading, so the pinned panel lost
the label for the number it exists to show. Compare `before-1440.png` (no heading above "62.9")
with `after-1440.png` ("Platform Value (V), finalised"). This pre-dates the ticket; the old sticky
card had it too. Fixed by pinning against the header's own token —
`top: calc(var(--topbar-height) + 1rem)` — so the two can't drift apart, with the height cap
subtracting the same amount.

## Short viewports

Below `700px` tall the rail stops being sticky altogether: a pinned block with its own scrollbar
owning most of a short screen is worse than one that simply scrolls with the page. Above it, the
rail is capped at `100vh - var(--topbar-height) - 2rem` and scrolls internally, so a rail taller
than the viewport can't strand its own tail. `unreachablePx` is measured at 80% scroll, where
sticky is actually engaged — at scroll 0 nothing is pinned yet and a rail below the fold is just a
long page, not a trap.

## Files

- `measure-rail.mjs` — the harness. `ASSESSMENT_ID=<finalised id> node measure-rail.mjs <before|after> <outdir>`
- `before-*.png` / `after-*.png` — the four viewports, parked at worst overlap
- `before-measurements.json` / `after-measurements.json` — full geometry per viewport

The unit guards in `frontend/app/assessments/[id]/WizardLayout.test.ts` are guards, not proof: they
catch the declaration being reverted. The proof is the geometry above. That split is the GRS-0209
lesson — its unit test passed while the page was visibly wrong, because declarations aren't
geometry. Verified the five new guards fail against the pre-fix code, so they aren't vacuous.
