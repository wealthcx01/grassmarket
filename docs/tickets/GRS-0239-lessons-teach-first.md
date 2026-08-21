# GRS-0239 — Lessons that teach before they test

**Status:** DONE (2026-08-21). _Previously recorded as: Planned (2026-07-31, founder: "the lessons are horrible and just tell me what I should._
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

---

## Status reconciliation — 2026-08-01

**MOSTLY DONE** — scopes 1, 2, 4 and 5 shipped 2026-08-19. **Scope 3 is not built**, stated below
rather than glossed.

## Two of the ticket's five findings were already fixed

Verified in source before building:

- **Finding 1 — "Sales Egoist is still 8 paragraph-lessons, zero slides"** — no longer true.
  GRS-0218 shipped it on 2026-08-01 as eight sections and 177 slides, and it is no longer blocked on
  source material (the material landed in `data/reference/sales-egoist/`).
- **Scope 5 — "stop pointing Start here at the old format"** — resolved by the same change.
  `mandatory_first=True` on `sales-egoist` is now the right answer, and `depth.LEGACY_COURSES` is
  **empty**: every Academy course is rebuilt.

Nothing was needed for either. The remaining three findings were all confirmed live.

## What shipped

**Scope 1 — the deck leads.** The renderer put the objective paragraph *and* the lesson's reference
cards above the slide deck, so the first screen of every rebuilt lesson was "what you should learn"
followed by a list of links, with slide 1 below the fold. That is the founder's sentence almost
verbatim, and it was a **layout** problem rather than a content one — the teaching was always there,
just second. The deck now renders first; the objective becomes a compact "What you'll be able to do"
panel after it; lesson references move to the end.

A legacy lesson (no slides) takes the original path unchanged, so nothing regresses for content the
rebuild has not reached.

**Scope 2 — references became citations.** `LessonReferences` gains a `footnote` variant: one line
("2 sources: docs.openbb.co") expanding on demand, used on slides. The card strip stays where
sources genuinely are the point — the end of a lesson. 139 of OpenBB's 196 slides carry references,
and a card strip under each made every slide look like a pointer elsewhere. **The depth rule is
untouched**: every claim still carries its source. This is display, not doctrine.

**Scope 4 — the four-paragraph tail, retired per course.** Retirement is now opt-in via
`covered_by_rebuilt`, declared by each course:

| Course | Retired | Kept | Why |
|---|---|---|---|
| OpenBB | relevance, sell-motion | white-label, commission | rebuilt `who-buys-and-why` and `how-and-when-to-sell` cover them |
| Brandfetch | relevance, sell-motion | white-label, commission | same |
| **Benzinga** | **none** | all four | its rebuilt slides do not cover this material — see below |

`commission` can never be retired by any course, and the builder raises if one tries: it carries
**live** Earnings v7 data that exists nowhere else and would go stale as authored slides.

## The mistake this scope made, and what caught it

The first implementation retired `relevance` and `sell-motion` **globally**, reasoning that every
course has a `who-buys-and-why` and a `how-and-when-to-sell` section.
`tests/test_benzinga_course.py::test_content_covers_the_key_facts_and_caveats` failed immediately:
Benzinga's rebuilt slides never mention **WIIM**, which its `relevance` paragraph teaches.

The generalisation was wrong, and shipping it would have been a silent content loss dressed as a
cleanup — the exact failure the depth register exists to prevent. Retirement is now a per-course
claim that each course has to make about itself.

(White-label was kept everywhere on the same principle: a grep found it in OpenBB's and
Brandfetch's rebuilt slides and **zero times** in Benzinga's.)

## Not done — scope 3, checkpoint confirmation

CHECKPOINT slides still render "Do this now:" as a callout with no interaction, exactly as the
ticket describes. The contract promises "the advisor produces something and confirms they did", and
it still does not.

This needs per-advisor persistence (a new table, a migration, an endpoint, and a change to how
lesson completion is counted) — a backend feature, not a renderer change like scopes 1 and 2. It is
the largest item in the ticket and I did not build it. **The ticket stays open on scope 3 alone.**

Its acceptance line — "ticking through a lesson means having *done* its checkpoints, not scrolled
past them" — is therefore **not met**. The first two-thirds of that sentence now is.

## Also not done

- **No before/after screenshot** (test-plan item 4). The Academy needs a seeded database and a
  signed-in advisor; the change is asserted by `lessonLayout.test.tsx` instead, which pins the
  ordering and the citation form directly.


---

## Scope 3 — shipped 2026-08-21

The ticket is now complete. CHECKPOINT slides have the interaction the content contract always
promised.

**What was there:** a callout reading "Do this now:" with no control, no state and no record, while
`Slide` has required a `checkpoint_prompt` on every checkpoint since GRS-0215 — the contract made
"the advisor produces something" enforceable, and the renderer then offered nothing to produce it
with. An instruction with no way to acknowledge it teaches an advisor that the instruction is
decorative, which is the complaint the whole ticket is about.

**What shipped:** an "I did this" control, persisted per advisor in `checkpoint_confirmations`
(migration `0041`), with `confirm_checkpoint` and `checkpoint_progress` on the repository and two
routes on the Workbench API.

Four decisions worth their reasons:

1. **Confirming twice is a no-op, not a 409** — deliberately the opposite of `complete_lesson`,
   which raises on a duplicate. Completing a lesson twice is a real mistake; re-ticking a
   self-reported checkpoint is not, and conflating them would teach advisors to ignore the error.
2. **Only a real CHECKPOINT slide can be confirmed.** Otherwise a client could invent progress the
   content model never offered, and the denominator in `checkpoint_progress` would mean nothing.
3. **The denominator comes from the published content**, so "0 of 2" is distinguishable from "no
   checkpoints here" — a bare zero says both.
4. **There is no un-confirm.** A checkpoint records that you *did* something; un-ticking it would
   be editing that record rather than correcting it. The state to be in if you redo the exercise is
   "done it twice".

The tick is set only **after** the write persists, and a failed save says so and restores the
button. A control that says "done" without a record would be the same empty gesture the callout
already was.

### The limitation, stated rather than buried

The key is `(advisor, lesson_id, slide_order)`. Lesson ids are deterministic and survive a
re-publish; **slide positions do not**. Re-ordering a lesson's slides carries a confirmation to
whichever slide now sits at that position.

The alternatives were worse: adding an id to `Slide` changes a frozen contract every course
validates against, and hashing the body would drop every confirmation the moment an author fixed a
typo. Position is the only key the content model offers today.

What *is* guaranteed: a stale confirmation can never inflate the count. `checkpoint_progress`
intersects the confirmed set with the **current** checkpoint positions, so progress cannot exceed
its own denominator — the part that would actually mislead someone. There is a test for exactly
that.

### Acceptance

The ticket's line — *"ticking through a lesson means having **done** its checkpoints, not scrolled
past them"* — is now met, with the honest caveat that "done" is self-reported. Nothing can verify
an advisor really opened the wizard; what changed is that the claim is explicit and recorded.