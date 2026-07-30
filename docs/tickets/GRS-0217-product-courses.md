# GRS-0217 — The remaining product courses, to the same standard

**Status:** In progress (2026-07-30) — Benzinga is PR 1 of n, opened at 2 of 8 sections.
**Priority:** HIGH. **Loop:** founder-feedback remediation, Wave 4. **Depends on:** GRS-0215,
GRS-0216 (sets the bar), GRS-0226 (the reader, without which none of it is visible).

## Ordering decision (scope asks for this to be a decision, not an accident)

By year-one advisor share from `commissions.yaml`: **Benzinga 1500 bps**, Brandfetch distribution
750, Brandfetch redistribution 375. Benzinga ties OpenBB at the top and is the only remaining
product with a committed structured source of truth, so it goes first. Brandfetch follows, and it
must teach the distribution / redistribution split as two products for two segments (GRS-0185),
because that is the specific thing the founder found us conflating. `sales-ops-playbook` is last.

## Progress

**PR 1 — Benzinga, sections 1 and 2 of 8.**

Written: "What Benzinga is, and what it is not" (24 slides, 9 hands-on) and "The catalogue, in four
families" (24 slides, 10 hands-on). Both meet the full GRS-0215 standard, each carries a diagram, and
each gates on a 6-question test.

Grounded in `data/gtm/sources/benzinga-product-catalog.xlsx` — 32 products, four families, with
delivery method, coverage universe, history depth, daily volume and differentiators per product. The
counts (9 / 11 / 8 / 4) and every product claim come from that sheet.

Eight diagrams authored for all eight planned sections, generated and rendered with the real
toolchain. `SECTIONS_PLANNED` lists the six sections still to write and
`test_the_course_is_not_finished_and_says_so` fails while it is non-empty, so this cannot read as
done before it is. `product-benzinga` stays in `LEGACY_COURSES` until then, and the rebuilt subtree
is held to the full standard meanwhile.

Still to write: how it arrives (delivery), the content layer, the event layer, the signal layer, who
buys which family, how to sell it.

**One consequence worth stating rather than leaving implicit.** Because the rebuilt sections come
first and the gate runs in reading order, the retained reference material now sits behind the two new
section tests. That material was kept so the course would not be thinner during the rebuild, and it
is now reachable only after an advisor passes sections 1 and 2. That is judged the right trade —
the reference modules are the paragraph-lessons the founder called basic, and gating the weaker
content behind the stronger content is not a loss — but it is a real behaviour change, not a
side effect nobody noticed.

### Two defects fixed on the way through

1. **The diagram toolchain could only hold one course.** `svg_export.py` hardcoded OpenBB in three
   places, including a `course=` parameter that `write_content_module` then ignored — so generating
   a second course would have silently overwritten `openbb_diagrams.py`.
2. **The OpenBB course had two sections sharing a module id.** The rebuilt "what-it-is" section and
   the retained reference module of the same name hashed to one uuid5 from the same namespace. The
   GRS-0226 section gate keys attempt records by module id, so passing the rebuilt section also
   marked the reference module passed. Fixed with a `reference-` key prefix, and `publish_course`
   now refuses duplicate section ids as well as duplicate orders. This was a live defect in what
   PR #220 shipped.

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
