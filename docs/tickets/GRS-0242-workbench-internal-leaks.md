# GRS-0242 — The Workbench stops leaking internals and contradicting itself

**Status:** PARTLY DONE (2026-09-05) — scope 3 (the contradiction) fixed; scopes 1, 2 and 4 are
display and routing on surfaces the redesign replaces, deliberately held. _Previously:_ OPEN
(reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-31, first-time-user review). **Priority:** MED. **Type:** Bug._
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

---

## Scope 3 — the cause, and the rule chosen (2026-09-05)

**It was not two sources disagreeing.** Both tabs already read the level from the same place:
`ConsultantORM.assessor_level`, which is also what the JWT carries. `_to_certification_record`
populates the contract's `level` from it, and `summarise_performance` passes that straight through.
They could not have shown different values.

**The actual cause: a level and its evidence live in two different stores, and nothing ever
compared them.** The level sits on the consultant record, where an invite, a seed or an
administrator can set it directly. The evidence — coursework, exam, shadow count, observed lead,
sign-off — sits on `certification_records` and is only ever written by the ladder. A level granted
outside the ladder therefore rendered identically to one climbed through it.

The dev seed reproduces it exactly: all three consultants marked `certified_lead`, **zero
certification records**. That is what the founder walked into.

### The rule

Derive the highest rung the **evidence** supports, and carry it everywhere the level appears:

- `earned_level` — the ladder walked upward from Trained, stopping at the first rung whose evidence
  is missing. Cumulative, so a sign-off cannot carry someone past a missing exam.
- `level_is_evidenced` — false when the marked level sits above `earned_level`.

Both are derived on read and never stored. `CertificationRecord` and `PerformanceSummary` both
carry them, so Bench and the Certification ladder describe the same person the same way.

**The level is never hidden or silently reduced.** An administrator may legitimately grant one, and
quietly demoting it on screen would contradict the JWT the rest of the product enforces against.
What changes is that a level the evidence does not support *says so*.

### One implementation of the rung rules

`promotion_blockers` (the gate) and `earned_level` (the display) now both call `evidence_blockers`.
Two copies of the ladder rules is precisely how this class of bug arises, and a test asserts the
two cannot diverge.

### What rendering caught that the tests did not

The explanatory note went in first. Screenshotting showed **the ladder still filled every rung
solid green** — the sentence said "granted" while the picture said "earned", and a reader trusts
the picture. Earned rungs are now filled; rungs held but not evidenced are outlined and dashed.

## Still open — deliberately

Scopes **1** (catalogue display names), **2** (arena history) and **4** (addressable tabs) are
display and routing on Workbench surfaces the redesign replaces (GRS-0271). Fixing copy on a screen
about to change means fixing it twice — the same reasoning `docs/WORK-QUEUE.md` already gives for
holding GRS-0205. The snake_case course names are still on screen and still wrong.
