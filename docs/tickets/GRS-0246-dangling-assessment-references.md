# GRS-0246 — Deleting an assessment leaves engagements pointing at nothing

**Status:** OPEN (2026-08-21). **Priority:** MED-HIGH. **Type:** Bug (data integrity).
**Loop:** post-wave hardening. **Relates to:** ADR-0047, ADR-0048, GRS-0177, GRS-0241.

## Why

Found while cleaning the staging Engagements page on 2026-08-21. **Five of twelve engagements
referenced assessment ids that no longer existed** — 42% of the table.

The cause is `delete_assessment` (ADR-0047, exercised by `scripts/staging_cleanup_grs0177.py`). It
deletes an assessment and the rows that reference it *by foreign key* — `AINarrativeORM`,
`PredictionORM`, `DeliverableORM`, in the same transaction, exactly as the ADR requires. But an
engagement references its assessments through **`assessment_ids_json`, a JSON text column**, so
there is no foreign key, no cascade, and nothing to notice. The assessments vanished in July and the
engagements went on pointing at them for a month.

ADR-0047 §4 states the intent plainly — *"Orphaned references are the silent inconsistency
non-negotiable #3 exists to prevent"* — and the guarantee does not hold for this one relationship
precisely because it is the one not expressed as a foreign key.

## What it cost

The dangling rows were the duplicate engagements the founder asked about three times (23/07, 31/07,
21/08). They could not be removed by the ordinary tool: GRS-0241 derives an engagement's provenance
from its linked assessments, and an assessment that does not exist yields nothing, so they stayed
`production` and ADR-0047 correctly refused them. Clearing them needed a separate decision
(ADR-0048) and a separate deletion path.

So the visible symptom — duplicate rows that would not go away — was two levels downstream of a
missing referential guarantee.

## Scope

1. **Make the reference checkable.** Either a real join table (`engagement_assessments`) with a
   foreign key, or a documented integrity check run in the same transaction as
   `delete_assessment`. Prefer the join table: it is the only option that makes the class of bug
   impossible rather than merely detected.
2. **Decide what deletion means for a referencing engagement.** Refuse the assessment deletion while
   an engagement links it, or unlink and record that it happened. **Refusing is the recommendation**
   — silently unlinking would leave an engagement whose history quietly changed, which is the same
   dishonesty in a different place — but state the choice in the PR.
3. **A repair for existing data.** Whatever remains dangling in production and staging is
   identified and reported. Nothing is deleted by the repair: ADR-0048's path exists for that and
   requires founder authorisation.
4. **A standing check.** A test asserting no engagement references a missing assessment, run
   against the seeded fixture set; and a read-only script an operator can run against a live
   database.

## Test plan

1. Deleting an assessment linked by an engagement behaves as scope 2 decides — a test that fails
   against today's code (the current behaviour is a silent dangling reference).
2. The standing check above, verified to fail against a database with a dangling reference.
3. Migration test if the join table is chosen: existing `assessment_ids_json` migrates without loss,
   and dangling entries are dropped with a count reported rather than silently.
4. Standing gate: pytest, pyright, ruff.

## Out of scope

- Removing the already-orphaned rows (done under ADR-0048 on staging 2026-08-21; production
  checked and clean — see below).
- The duplicate-engagement cleanup itself (GRS-0241).

## Acceptance

An assessment cannot be deleted in a way that leaves an engagement pointing at nothing, and running
the standing check against staging and production reports zero dangling references.

## Production, checked

Checked read-only on 2026-08-21, before this ticket was even opened for work: **production holds one
engagement and zero dangling references.** The defect is real and the guarantee is still missing,
but nothing is broken in production today — the damage on staging came from the seed-and-clean
cycles that only ever ran there.

That lowers the urgency and does not change the scope: the reference is still unenforced, and the
next `delete_assessment` against a linked engagement will do the same thing wherever it runs.
