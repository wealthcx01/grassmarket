# GRS-0217 — The remaining product courses, to the same standard

**Status:** In review (2026-07-30, PR #221) — **Benzinga complete, 8 of 8 sections.** Brandfetch
and sales-ops-playbook still to do, one PR each. **Priority:** HIGH. **Loop:** founder-feedback
remediation, Wave 4. **Depends on:** GRS-0215, GRS-0216 (sets the bar), GRS-0226 (the reader,
without which none of it is visible).

## Ordering decision (scope asks for this to be a decision, not an accident)

By year-one advisor share from `commissions.yaml`: **Benzinga 1500 bps**, Brandfetch distribution
750, Brandfetch redistribution 375. Benzinga ties OpenBB at the top and is the only remaining
product with a committed structured source of truth, so it went first. Brandfetch follows, and it
must teach the distribution / redistribution split as two products for two segments (GRS-0185),
because that is the specific thing the founder found us conflating. `sales-ops-playbook` is last.

## PR 1 — Benzinga: complete

Eight sections, **192 slides**, 48 test questions, 69 hands-on slides, one authored diagram per
section. Every section gates on a 6-question test at an 80% pass mark. The whole course meets the
GRS-0215 depth standard.

| # | Section | Slides | Hands-on |
|---|---|---|---|
| 1 | What Benzinga is, and what it is not | 24 | 9 |
| 2 | The catalogue, in four families | 24 | 10 |
| 3 | How it arrives, and what that costs to build | 24 | 9 |
| 4 | The content layer: what a user reads | 24 | 8 |
| 5 | The event layer: what a user plans around | 24 | 7 |
| 6 | The signal layer: what a desk trades on | 24 | 8 |
| 7 | Who buys which family, and what triggers it | 24 | 9 |
| 8 | How to sell it | 24 | 9 |

Grounded in `data/gtm/sources/benzinga-product-catalog.xlsx` — 32 products across four families
(8 / 11 / 9 / 4) with delivery method, coverage universe, history depth, daily volume, key fields and
differentiators per product. Those counts are now asserted against the spreadsheet by
`test_the_family_counts_match_the_committed_catalogue`, and the slides are asserted to quote the same
numbers.

`SECTIONS_PLANNED` is empty, `test_the_course_is_not_finished_and_says_so` has been deleted as its
own failure message asked, and `product-benzinga` has come off `depth.LEGACY_COURSES`. Worth noting
what that register is: nothing in `check_depth` reads it, so it never exempted anything mechanically
— it is the visible-debt list, and this debt is paid.

**The honesty discipline is carried in the content, not in a preamble.** Section 1 drills the three
things Benzinga is not. Section 4 makes the advisor say the AI provenance of Bulls Say Bears Say out
loud. Section 5 states the earnings accuracy figure precisely *and* forbids stretching it across the
other ten calendars. Section 6 is built around the alpha caveat and includes a slide asking the
advisor to rewrite their sentence if it contains the word "predicts". Section 8 ends on the four
lines an advisor never crosses: price, timeline, redistribution, attribution.

### Three defects fixed on the way through

1. **The diagram toolchain could only hold one course.** `svg_export.py` hardcoded OpenBB in three
   places, including a `course=` parameter that `write_content_module` then ignored — so generating
   a second course would have silently overwritten `openbb_diagrams.py`.
2. **The OpenBB course had two sections sharing a module id.** The rebuilt "what-it-is" section and
   the retained reference module of the same name hashed to one uuid5 from the same namespace. The
   GRS-0226 section gate keys attempt records by module id, so passing the rebuilt section also
   marked the reference module passed. Fixed with a `reference-` key prefix, and `publish_course`
   now refuses duplicate section ids as well as duplicate orders. This was a live defect in what
   PR #220 shipped.
3. **I had two family counts backwards.** Content and Alternative Data were swapped, and the error
   had reached a slide body, a walkthrough instruction, a test question, the diagram and its alt
   text before I recounted the sheet. The fix is the parity test, not the corrected numbers.

**One consequence worth stating rather than leaving implicit.** Because the rebuilt sections come
first and the gate runs in reading order, the retained reference material sits behind all eight new
section tests. That material was kept so the course would not be thinner during the rebuild. Now
that the rebuild is finished it is genuinely superseded, and GRS-0217's remaining work should
consider deleting it rather than leaving four locked modules at the end of a finished course.

## Why

The Academy has a course per product family we distribute, and each is currently a page of
summary. The founder's complaint applies to all of them, not only OpenBB: an advisor cannot sell a
product they have only read a paragraph about, and the products are the revenue.

OpenBB (GRS-0216) establishes the shape. This ticket applies it to the rest, one PR per course, so
each can be reviewed on its own merits rather than as part of a wall.

## Scope

One PR per product family. Each course follows the GRS-0215 structure: sections of lessons, each lesson 20 to 40 slides, a test between sections, at least one `SourceRef` per lesson, assets in the design system, a
downloadable deck.

Each course must answer the same five questions, because that is what an advisor needs in a room:

1. What is this product, and what problem does it solve?
2. How does it actually work? Enough that the advisor can demo it, not just describe it.
3. Who buys it, in which segment, and what triggers the purchase? Mapped to `RegistryTarget`
   segments so a lesson connects to the pipeline.
4. What does it cost, and how is it priced and packaged?
5. How do you sell it, and what are the objections?

**Sources, per course**, drawn from what is already committed under `data/gtm/sources/` plus the
product's own public material:

- **Benzinga** — `benzinga-product-catalog.xlsx`, plus their docs and newsroom.
- **Brandfetch** — distribution and redistribution are different products for different segments
  (GRS-0185); the course must teach that difference, since the founder found us conflating them.
- The remaining families in the current catalogue, one PR each.

**Ordering.** Highest-commission and most-distributed products first. The order goes in the PR
description so it is a decision, not an accident.

## Test plan

1. The GRS-0215 content-depth tests, run per course. A course that does not meet the bar fails the
   build rather than shipping thin.
2. Link integrity at build time.
3. Progression gating per section.
4. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- OpenBB (GRS-0216) and Sales Egoist (GRS-0218).
- The freshness watcher (GRS-0192), which keeps these current afterwards.
- Certification rules.

## Acceptance

An advisor can finish any product course and run a first client conversation about that product
without needing to be coached first.
