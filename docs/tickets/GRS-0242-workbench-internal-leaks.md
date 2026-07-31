# GRS-0242 — The Workbench stops leaking internals and contradicting itself

**Status:** OPEN (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-31, first-time-user review). **Priority:** MED. **Type:** Bug._
**Loop:** first-time-user coherence. **Relates to:** GRS-0196, GRS-0205.

## Why

Walked tab by tab as a first-time user, 31/07/2026:

- **Practice Arena history renders a raw enum:** the history list literally shows
  "in progress / in_progress" — the same state once as words and once as the wire value, with no
  scenario name, date, or way back into the session.
- **Certification lists raw product keys as course names:** "benzinga product",
  "brandfetch_distribution product", "brandfetch_redistribution product", "openbb product" —
  snake_case keys beside the properly titled "Sales Egoist".
- **Two tabs disagree about the same person.** Bench's "My performance" says
  "Level: certified lead" while Certification shows a ladder with coursework Outstanding, the exam
  Not taken, zero shadow assessments and no promotions recorded. One of these is not true; both are
  on screen at once. (Likely the dev-seeded admin level vs the evidence-derived view — find the
  actual cause, do not paper over it.)
- **Tabs are not addressable.** `?tab=practice` in the URL still lands on Bench; nothing deep-links
  to a Workbench tab, so no other surface (or ticket, or the founder's own notes) can point at one.

Each of these is small; together they make the Workbench read as unfinished scaffolding, which is
the founder's overall "none of it makes sense" in miniature.

## Scope

1. **Display names come from the catalogue.** Certification rows and any surface naming a course or
   product render the catalogue display title; a lint-style test greps rendered output for
   snake_case leakage (pattern: the copy-register approach in GRS-0205).
2. **Arena history becomes a list of sessions:** scenario title, started date, state as words,
   resume/review link. State labels from one mapping; the wire value never renders.
3. **Reconcile the level.** Establish where "certified lead" comes from; the Bench panel and the
   Certification ladder must derive from the same source, and evidence-contradicting levels render
   with their provenance ("set by administrator") rather than as earned. State the cause and the
   chosen rule in the PR.
4. **Addressable tabs.** Workbench tabs sync to `?tab=`; unknown values fall back to Bench; the
   Bench next-action links use them (today "Practise discovery" points at the tab it cannot open).

## Test plan

1. Vitest: certification names, arena history rendering, tab routing from URL, and the
   snake_case-leak sweep across Workbench rendered output.
2. Backend: whichever level rule scope 3 picks, a test pinning Bench and Certification to the same
   derivation.
3. Manual: all five tabs screenshotted after, in the PR.
4. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- Practice Arena interaction redesign (GRS-0196).
- Certification policy or ladder changes — display and consistency only.
- Founder review tab (correct today).

## Acceptance

The founder clicks through all five Workbench tabs and meets no snake_case, no raw enum, no two
tabs disagreeing about their level, and can send someone a link to a specific tab.

---

## Status reconciliation — 2026-08-01

**OPEN.** Scheduled in the GRS-0229–0245 wave (see docs/BACKLOG.md for the build order).
