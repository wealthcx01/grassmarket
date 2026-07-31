# GRS-0191 — Academy content depth program (the 100x)

**Status:** SUPERSEDED (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-23, founder feedback item 20). **Priority:** HIGH — the founder's._
sharpest criticism. **Loop:** founder-feedback remediation, Wave 4. Depends on GRS-0190.
Program ticket: expect one PR per course under this umbrella.

## Why

Founder verdict: current courses are "a bare minimum start" — generic summaries of supplied
material, when the expectation was serious enterprise B2B depth: backlinks to the products'
YouTube videos and docs, generated interpretive assets, per-product detail 100x deeper, OpenBB
1000x. The sources exist; the content program ingests them properly.

## Scope

All content is authored as reviewable in-repo data files under
`src/grassmarket/workbench/content/` (the existing pattern: `CourseTree` builders with
uuid5-derived IDs so re-seeding and re-publishing are idempotent), published through the
existing draft → approve → publish CMS. Partner-confidential terms stay out of the repo per
the ESTATE-RECONCILIATION policy; internal doctrine (e.g. the teaser deck) is paraphrased in
lesson bodies and never cited by URL; only public sources appear as GRS-0190 `references`.
Commission figures are never typed into lesson text — the product-course template resolves
them live from the Earnings v7 schedule (existing `product_course.py` mechanism, unchanged).

Per-course PRs, each republishing its course as a new `CourseVersion`:

1. **PR 1 — OpenBB (flagship)** (`openbb_course.py`): expand from 22 lessons to at least 60,
   organised as: (a) per-surface modules (Workspace, Platform/SDK, widgets, apps, AI copilot,
   deployment/governance) grounded in docs.openbb.co with the relevant docs page as a `docs`
   reference on every lesson; (b) per-endpoint-family Platform material (equity, fixed income,
   options, economy, news — one lesson per family with worked `obb.…` examples); (c) the
   Exchange Terminal Programme strategy as its own module: the terminal barbell, the four-layer
   product requirements (data / OMS execution / Symphony comms / AI copilot), and the exchange
   sell motion; (d) licensing deep-dive (AGPLv3 vs commercial) and competitive positioning,
   retained and sourced. Every lesson carries at least one reference; lessons with a matching
   OpenBB YouTube video carry it as `video_ref`. At least 6 interpretive SVG assets (e.g. the
   pivot timeline, the barbell, the four-layer stack).
2. **PR 2 — Benzinga** (`benzinga_course.py`): per-product-family modules generated from the
   37-row Full Product Catalog at `data/gtm/sources/benzinga-product-catalog.xlsx` — one lesson
   per family covering description, delivery mechanism, and use case, with the family's Docs URL
   and Marketing URL as two link cards. Decision: the catalog rows are transcribed into the
   content file as code data; a comment records the source file path and date.
3. **PR 3 — Brandfetch** (`brandfetch_course.py`): split into two tracks matching GRS-0185's
   segment scoping — Distribution (retail brokerages) and Redistribution (exchanges and
   information vendors) — as separate modules, each with the segment-correct sell motion,
   pricing-model explanation, and worked positioning; the segment note added under GRS-0185
   is superseded by the full split.
4. **PR 4 — Sales Egoist** (`sales_egoist.py`): the 8 doctrine lessons deepened from the full
   teaser-deck material (OneDrive source, paraphrased, not committed), plus worked
   objection-handling scripts (one lesson per major objection class) and per-segment plays
   (retail / wealth / exchange — one lesson each).
5. **PR 5 — Sales Ops Playbook** (`sales_ops_playbook.py`): per-pipeline-stage depth grounded
   in the strategy document's GTM plan — for each stage: entry/exit criteria, the plays, the
   artefacts (linking the relevant Studio surface), and a worked example.
6. **Cross-cutting, every PR:** every lesson keeps a `check_question`/`check_answer` pair;
   `drill_topics` extended so each new module maps to at least one drill topic, with new
   `DrillCard` prompt/answer content added to the drill seed for new topics; each course PR
   updates its content test (`test_benzinga_course.py` pattern) to pin the new structure.

## Test plan

Per course PR (pytest; the existing content-test pattern):
- Structure pins in `tests/test_openbb_course.py` (new), `test_benzinga_course.py`,
  `test_brandfetch_course.py`, and new `test_sales_egoist_course.py` /
  `test_sales_ops_course.py`: module count, lesson count at or above the floor stated in this
  ticket, every lesson has a non-empty body of at least 400 characters, a check question and
  answer, and at least one `SourceRef`; every `video_ref` is a YouTube URL/ID; every reference
  URL is https.
- Benzinga: exactly one lesson per catalog family; each carries both a `docs` and a `blog`
  (marketing) reference.
- Brandfetch: the distribution module never mentions redistribution licensing and vice versa
  (string-level guard for the segment split).
- No lesson body contains a currency amount for commissions (regex guard — figures come from
  config), and no lesson text contains the strings that mark confidential material (existing
  policy test pattern).
- Seed idempotence: seeding twice yields identical IDs and one course version bump per
  publish (`test_academy_seed.py` extended).
- Golden masters and all non-Academy suites untouched.

Frontend: no new tests (rendering is GRS-0190); existing academy page tests stay green.

## Out of scope

- Renderer/contract work (GRS-0190 — a prerequisite).
- Freshness watching (GRS-0192).
- New products or courses beyond the five named.
- Any change to the CMS, publishing, completion, or certification machinery.

## Acceptance

- Each course PR meets its numeric floor: OpenBB ≥ 60 lessons with ≥ 6 assets; Benzinga one
  lesson per catalog family with two link cards each; Brandfetch two segment tracks; Sales
  Egoist ≥ 16 lessons (8 doctrine + objections + 3 segment plays); Sales Ops one module per
  pipeline stage — all pinned by tests.
- Every lesson has a check question and at least one cited public source; video references
  render in the reader.
- The founder signs off course-by-course at PR review (recorded in the PR).
- Commission figures remain live-from-config; no confidential agreement text or operator
  spreadsheet is committed.

---

## Status reconciliation — 2026-08-01

**SUPERSEDED.** Superseded by GRS-0215. GRS-0215 'replaces the content half of GRS-0191'; the reader half became GRS-0226.
