# GRS-0239 — Lessons that teach before they test

**Status:** Planned (2026-07-31, founder: "the lessons are horrible and just tell me what I should
learn as opposed to actually being lessons? It just reference links").
**Priority:** MED-HIGH. **Loop:** first-time-user coherence. **Extends GRS-0215.**
**Relates to:** GRS-0218, GRS-0190, GRS-0226.

## Why

The founder's complaint is partly about content that no longer exists — and partly exactly right
about what still ships. Verified in source, 31/07/2026:

1. **The first course a new advisor meets is the old format.** Sales Egoist is `mandatory_first`
   in the catalogue and is still 8 paragraph-lessons, zero slides, zero tests
   (`src/grassmarket/workbench/content/sales_egoist.py`) — GRS-0218 is blocked on source material.
   "Start here" points at the worst content we have.
2. **Every rebuilt lesson opens with objective meta-language.** All rebuilt sections' `Lesson.body`
   begins "By the end of this lesson you can…", and the renderer places that paragraph *plus the
   lesson-level reference cards* above the slide deck — so the first screen of even the good
   courses is "what you should learn" + links, which is the founder's sentence almost verbatim.
   The actual teaching (slide 1) sits below the fold.
3. **Reference-card noise.** 139 of OpenBB's 196 slides carry references, each rendering a link-card
   strip under the slide body. Sourcing is doctrine (a claim with no source does not belong on a
   slide) — but a per-slide link strip makes every slide *look* like a pointer elsewhere.
4. **"Do this now" doesn't do anything.** CHECKPOINT slides render an imperative callout with no
   interaction — no confirmation, no input, no state — though the contract promises "the advisor
   produces something and confirms they did".
5. **Every product course ends in the old template** — four single-paragraph lessons
   ("relevance / white-label / sell-motion / commission", `product_course.py`) after 192 slides of
   the new standard.

## Scope

1. **Reorder the lesson opening.** The deck leads; the objective paragraph becomes a compact
   "What you'll be able to do" panel *after* the deck opener or collapsed above it, and lesson-level
   reference cards move to the lesson's end. First screen = teaching. (Renderer change in
   `frontend/app/workbench/academy/[slug]/page.tsx`; no content-schema change.)
2. **References become citations.** Per-slide sources render as a single footnote line
   ("Source: OpenBB Workspace docs ↗"), expanding on demand; the card strip goes. The depth rule
   (every claim sourced) is untouched — this is display, not doctrine.
3. **Checkpoints confirm.** CHECKPOINT slides gain the promised interaction: a confirm control
   ("I did this") persisted per advisor, counted in lesson completion, surfaced in section
   progress. Contract field usage unchanged; renderer + a small progress persistence addition
   (pattern: the existing recall-gate persistence).
4. **Retire the four-paragraph tail module.** The "— sell it" template section is rebuilt to the
   depth standard (it is the course's actual selling punchline and currently its thinnest part) or
   folded into each course's final rebuilt section. State which per course in the PR.
5. **Stop pointing "Start here" at the old format.** Until GRS-0218 unblocks, `mandatory_first`
   moves to the strongest rebuilt course, and Sales Egoist is labelled as awaiting its rebuild
   rather than presented as the front door. (GRS-0218 itself stays blocked on the founder
   committing source material under `data/reference/` — restate that dependency in the PR so it is
   seen again.)

## Test plan

1. Vitest: lesson page renders the deck before the objective panel; reference strip absent from
   slide body, citation line present; checkpoint confirm persists and reflects in progress.
2. Depth tests updated where the tail module is rebuilt (it enters the 8-section standard or the
   per-course exception is removed).
3. Content tests: `mandatory_first` no longer selects a legacy-format course while
   `depth.LEGACY_COURSES` contains it.
4. Manual: first screen of OpenBB lesson 1 before/after, in the PR.
5. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- The Sales Egoist course content (GRS-0218, blocked on source).
- New interactive block types beyond checkpoint confirmation (drag/order, branching — future, and
  GRS-0196 owns scenario practice).
- Section-test mechanics (GRS-0226, shipped).

## Acceptance

The founder opens the first course the catalogue offers and the first screen teaches them
something; links are citations, not the content; and ticking through a lesson means having *done*
its checkpoints, not scrolled past them.
