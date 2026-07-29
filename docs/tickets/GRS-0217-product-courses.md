# GRS-0217 — The remaining product courses, to the same standard

**Status:** Planned (2026-07-26, staging review item 14; 23/07 item 20). **Priority:** HIGH.
**Loop:** founder-feedback remediation, Wave 4. **Depends on:** GRS-0215, GRS-0216 (sets the bar).

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
