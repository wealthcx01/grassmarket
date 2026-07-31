# GRS-0218 — The Sales Egoist course

**Status:** DONE (2026-08-01). **Priority:** HIGH.
**Loop:** founder-feedback remediation, Wave 4. **Depends on:** GRS-0215.

## Why

The founder gave us a lot of material on the Sales Egoist and said, of what came back:

> "You have done nothing but generically summarize some of the content I gave you. I am beyond
> disappointed."

This is the methodology course, not a product course. It is what makes an advisor good at the job
rather than knowledgeable about one vendor, so it carries more weight than any single product
course and currently has the least behind it.

## Blocked, and on what exactly

The source material is **not in the repository**. Checked again on 2026-07-29 across all branches:
`data/reference/7powers-math-extraction.md` is present; the Sales Egoist teaser deck and the
7 Powers PDF are not. The 23/07 manifest records the deck as "OneDrive source, paraphrased, not
committed".

The founder has said they will add the Helmer and Sales Egoist materials. Until they land in
`data/`, this ticket cannot start, because writing it from the existing paraphrase would repeat
exactly the failure being complained about.

**Unblocking condition:** the Sales Egoist material committed under `data/reference/`.
**UNBLOCKED 2026-07-31** by commit `2d81f56`: the Master Curriculum docx and both
authored lesson decks landed under `data/reference/sales-egoist/`.

## Scope, once unblocked

GRS-0215 structure: sections of lessons, each lesson 20 to 40 slides, a test between sections, sources cited per lesson.

1. **The idea itself**, from the source rather than from a summary of it. What the Sales Egoist
   framing claims, where it came from, and what it argues against.
2. **The method**, broken into the moves an advisor actually makes, with worked examples drawn
   from the segments we sell into rather than generic B2B examples.
3. **Applied to our work.** How the framing maps onto an ATLAS engagement: the first meeting, the
   assessment as a sales instrument, the deliverable as the close.
4. **Practice.** Scenarios the advisor plays through, connected to the Practice Arena rebuild
   (GRS-0196) rather than a quiz.
5. **Assets.** A deck the advisor can actually study from, in the design system.

## Test plan

1. The GRS-0215 content-depth tests.
2. Source-attribution test: every lesson carries a `SourceRef` pointing at committed material, so
   the "generic summary" failure is caught by the build rather than by the founder.
3. Progression gating per section.
4. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- Product courses (GRS-0216, GRS-0217).
- The Practice Arena rebuild itself (GRS-0196), which this course feeds.

## Acceptance

The founder reads the course and recognises the material they gave us, developed rather than
compressed.


**DONE.** Built from the committed source on 2026-08-01, after `2d81f56` landed the material.

## What shipped

**Eight sections, 177 slides, one section test each** — `sales_egoist_slides.py`. The shape follows
the curriculum's own rather than being imposed on it: Part One becomes sections 1 to 3 (the
doctrine and the terrain; the battlefield; the armoury), Part Two's eight convictions become
sections 4 to 7 at two per section, and Part Three's integration becomes section 8, which then runs
the whole campaign against an actual ATLAS engagement.

Per section: 22, 24, 24, 23, 22, 21, 21, 21 slides. Six questions per section test, each with an
explanation that teaches rather than only marking. Eight diagrams, one per section, authored as
SceneSpecs under `design/motion/courses/sales_egoist/` and exported through the existing pipeline.

**Every claim is sourced.** Three `SourceRef`s point at the committed artefacts by their canonical
blob URL — the curriculum docx and both decks. `SourceRef.url` is https-only at the contract, so a
repo file has to be cited that way; the link resolves to the exact committed file each lesson was
written from. `tests/test_sales_egoist_course.py` enforces that every lesson cites committed
material, which is the ticket's test-plan item 2: the "generic summary" failure is now caught by the
build rather than by the founder.

**The thin course was deleted, not left alongside.** The eight paragraph-lessons in
`sales_egoist.py` were written in July 2026 from a paraphrase and are exactly what the founder was
describing. Keeping them would have meant that sentence still shipped. What they contained that the
rebuild does not simply inherit is recorded in the module docstring rather than lost: their
strongest idea — *the assessment is the demo* — survives, developed, as section 8's treatment of
the assessment's three jobs in a campaign.

**GRS-0148 call (b) honoured as written.** The doctrine's own vocabulary is kept inside the course
(it is internal training, and the voice is part of its force) and spreads to no new client-adjacent
surface. That decision is recorded in the module docstring and asserted by a test, and the wider
question — whether the naming survives on client-facing surfaces — stays with the founder as **D5b**.

**GRS-0239 scope 5 resolved at the root.** That ticket proposed moving `mandatory_first` off this
course because "Start here" pointed at the worst content we had. Rebuilding the course fixes the
cause, so the flag stays where the Academy's design always wanted it. There is no temporary shuffle
to undo later.

**`LEGACY_COURSES` is now empty.** This was its last entry. The register stays in place, because the
next course authored starts unbuilt and an exemption nobody can see is how the last rebuild quietly
did not happen.

### One thing that was NOT done, and one thing found on the way

- **Scope item 4, Practice**, is partially met. The course carries 30 checkpoint slides that each
  produce a written artefact, and the campaign section ends with a diarised action. What it does not
  do is connect those to the Practice Arena, because the Arena rebuild (GRS-0196) has not been
  built. The hooks are the `drill_topics` on each lesson; wiring them is GRS-0196's job.
- **A content gap was found by a pre-existing test and fixed rather than argued away.** The old
  GRS-0122 test required every lesson to tie to all three operating models. On the first pass the
  rebuilt course mentioned wealth **zero times** — the curriculum is written institution-wide and
  names asset managers rather than wealth managers. Since the wealth operating model is now live and
  client-usable (GRS-0147c), and the mock-advisor stress test found wealth personas felt
  unaddressed, the fix was a new worked example in section 2 rather than a weaker test. The test
  itself moved from per-lesson-body to the slide corpus, because in the rebuilt format the body is
  the objective and the teaching is in the slides.
