# GRS-0225 — Diagrams for the courses, authored not decorated

**Status:** In review (2026-07-29, PR #220). **Priority:** HIGH. **Loop:** founder-feedback
remediation, Wave 4. **Depends on:** GRS-0206 (the Rive toolchain), GRS-0215 (the slide contract).

> **Not yet visible to an advisor.** The nine diagrams are on their slides and served by the API,
> but the Academy reader renders `lesson.body` and `lesson.assets` only — `slides` is not in the
> frontend types at all. So all 196 slides of GRS-0216, and these diagrams with them, are data
> nobody can see. The slide reader is its own build and this ticket's acceptance depends on it.

## Why

The OpenBB rebuild (GRS-0216) shipped 196 slides that meet the depth standard and **not one
diagram**. The `Slide` contract has an `asset` field and the rebuild used it zero times. That is a
real gap against what the founder asked for, in their words:

> "I asked for you to use your design capabilities to make this more interactive and generate power
> point assets"

Well-sourced prose is a large improvement on the paragraph it replaced. It is not the same thing as
a course that teaches visually, and several of the ideas in that course are spatial rather than
verbal: the two-product split, the anatomy of a widget, one parameter moving several widgets, the
AGPL decision, the segment-to-trigger map. Those are drawings that happen to be currently written
down as sentences.

## The thing that changed

`George-RD/rive-rs-cli` compiles a JSON scene spec to a real `.riv` and renders it with the actual
Rive runtime to verify. So a diagram here is **authored, versioned and reviewable as JSON**, and
the animated version costs little more than the static one. This ticket is possible in a way it
was not before that tool existed.

## Scope

1. **Static first, motion second.** Every diagram must read correctly as a single still frame,
   because that frame is also the reduced-motion fallback and the export into a deck. A diagram
   that only makes sense while moving is not finished.
2. **The OpenBB diagrams**, one per idea that is genuinely spatial:
   - **Two products, one company**: the open-source Open Data Platform beside the commercial
     Workspace, and which one a client buys. Section 1.
   - **Widget anatomy**: data source, metadata layer, visual presentation, parameters, as four
     labelled parts of one object. Section 3.
   - **Linked parameters**: one field changing and three widgets following it. This one is worth
     animating, because it *is* the demo the advisor will give. Section 3 and section 4.
   - **Dashboard to app**: a configured canvas becoming an exported `apps.json` the desk uses.
     Section 4.
   - **The AGPL decision**: internal use, versus modify-and-serve-to-clients, and where the
     commercial route enters. Section 6. A decision tree, and the highest-value drawing in the
     course because it is the one an advisor gets wrong under pressure.
   - **Segment to trigger**: the five registry segments and the irritation that opens each.
     Section 7.
   - **The sale**: first meeting, demo, technical, pilot, price, with the good outcome at each
     stage. Section 8.
3. **Committed as source plus binary.** The JSON SceneSpec next to the `.riv`, under
   `design/motion/courses/`. A binary whose source is not beside it is not reviewable.
4. **Rendered stills committed too**, as the fallback and as the deck asset. This is also what
   makes a pixel `compare` possible in CI.
5. **Design tokens.** Paper/ink, Bottle Green `#1A3B26`, Source Serif 4 and Inter. Not the colours
   the scaffold template ships with.
6. **Alt text is mandatory**, and `LessonAsset` already requires it. A diagram nobody can read with
   a screen reader is a diagram half the point of which is missing.

## Test plan

1. Every committed SceneSpec generates, validates and renders **non-blank**. The blank check is the
   one that catches real breakage.
2. `compare` against the committed reference frames, so a visual change shows up in review as a
   pixel delta rather than as an unreadable binary diff.
3. A depth-standard extension: every rebuilt course section carries at least one asset. This is the
   part that stops the next course from shipping 196 slides of prose again.
4. Reduced-motion: the static frame renders and carries the same information.
5. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

### What shipped against that plan

1 and 2 need `rive-cli` and a Rust toolchain, which CI does not have. They are a **local** gate:
`design/motion/render.sh` (generate → validate → render, refusing a blank frame) plus the SVG-vs-
still comparison documented in `design/motion/README.md`. Saying so is better than a CI job that
silently skips.

In CI instead, `tests/test_course_diagrams.py` (55 cases) proves what does not need the toolchain:
every scene exports; the generated content module and the committed `.svg` have not drifted from
the scenes; the SVG uses only constructs `frontend/lib/svg.ts` accepts; the emitter refuses an
unknown node, an unimplemented property, an unresolvable animated property and multi-line text; the
paint order is inverted; and every scene is actually on a slide. `frontend/lib/courseDiagrams.test.ts`
(28 cases) runs the real sanitiser over the real diagrams, because a rejected diagram renders as an
error message rather than a drawing.

3 shipped as `MIN_ASSETS_PER_LESSON` and `MIN_ASSET_ALT_CHARS` in `content/depth.py`, with two
tests that watch a thin fixture be refused. It needed **two more diagrams** than this ticket
listed: sections 2 and 5 had no spatial idea in the original seven, and a rule that two of eight
sections fail is not a rule. `what_runs_where` (your machine and the package versus their browser
and Workspace, with `localhost:6900` between them) and `three_jobs` (three miniature layouts,
because the job decides the shape) are both ideas the prose was already trying to draw.

## Out of scope

- The Rive toolchain decision and the runtime cost (GRS-0206).
- Course prose (GRS-0216 to GRS-0218), which is written.
- Wizard and pipeline motion (GRS-0206), and report visuals (GRS-0220).

## Acceptance

The founder opens the OpenBB course and the AGPL decision and the linked-parameter mechanic are
drawings rather than paragraphs, each with a still that works on its own, and the depth standard
refuses a future course that has no diagrams at all.
