# GRS-0122 — Sales Egoist = the "Sales 101" core module

**Status:** Shipped (v1 seed — founder deepens from the decks over the top)
**Loop:** Part 2 — Bruntsfield Academy / Workbench (one program)
**Depends on:** ADR-0028 (Bruntsfield Academy / Workbench), GRS-0121 (content CMS)

## Delivered

The 8-lesson Sales Egoist doctrine, authored **through the GRS-0121 CMS** as structured content (not
decks): `workbench/content/sales_egoist.py` builds the `CourseTree` (Zero-Sum Pipeline → Total
Account Awareness; the Relationship / Challenger / Demo weapons; qualify-with-assessment; awareness→
close). Each lesson has a spaced-repetition **drill** topic and a concrete **measurement** (new
`Lesson.measurement` field), and each ties the sales motion to the Platform Power assessment across
**retail brokerage / wealth / exchange**. The module is flagged **mandatory-first** (new
`CourseTree.mandatory_first`), so `list_published_courses` sorts it to the front of the learner
catalog. `workbench/content/seed.py` + `repo.upsert_published_course` seed it idempotently (stable
uuid5 lesson ids), wired into `scripts/seed_dev.py`. Editor exposes the mandatory-first toggle; the
catalog shows a "start here" badge. Grounded in the public Challenger Sales method + the codebase's
own operating models — **not** a copy of any proprietary deck; because it is versioned, the founder
deepening it from the uploaded decks is simply a new published version, never a code change.

## Why

Sales Egoist is the core sales doctrine of the Academy, but today it exists only as two teaser decks
and a partial curriculum (2 of 8 lessons built). It must become the **mandatory intro module every
advisor takes first**, deepened far beyond the teasers, and — critically — **tied to Bruntsfield's
assessment work** so advisers see how the sales motion connects to the Platform Power assessments they
run across retail brokerage, wealth, and exchange operating models.

## What to build

- Deepen the **8-lesson doctrine** (Zero-Sum Pipeline → Total Account Awareness; the Relationship /
  Challenger / Demo weapons; a per-lesson drill + measurement) well beyond the teaser decks, seeding
  from the uploaded Sales Egoist decks + curriculum + the Challenger Sales summary, with the VM
  deepening via research.
- **Tie each lesson to Bruntsfield's assessment work** across retail brokerage / wealth / exchange —
  every lesson connects the sales motion to what the assessment surfaces.
- Author all of it **through GRS-0121's CMS** (seed content lives under `workbench/`); mark it the
  mandatory first module in the learner path.

## Acceptance / verification

- All 8 lessons exist as structured CMS content (not decks), each with a drill and a measurement.
- Each lesson carries an explicit tie to assessment work across at least the three operating models.
- The module is flagged mandatory-first, so a new advisor's path opens on it.

## Not in scope

- The certification that sits on top of this module (GRS-0127).
- Practice-arena/calibration scenarios drawing on it (GRS-0130).
