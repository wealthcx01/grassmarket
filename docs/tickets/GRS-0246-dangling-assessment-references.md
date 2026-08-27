# GRS-0246 — Deleting an assessment leaves engagements pointing at nothing

**Status:** MOSTLY DONE (2026-08-27) — scopes 2 and 4 shipped; 1 and 3 deliberately not. **Priority:** MED-HIGH. **Type:** Bug (data integrity).
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


---

## Shipped 2026-08-27 — the hole is closed

**Scope 2 — the decision, and it is REFUSE.** `delete_assessment` now refuses while any engagement
links the assessment, naming the engagements in the message. Silently unlinking was the alternative
and it is worse: it leaves an engagement whose history quietly changed, which is the same dishonesty
moved somewhere harder to notice. The link is a record of what the engagement drew on, so removing
it is a decision, not a side effect.

The check is **deliberately not owner-scoped**. The question is referential — *would deleting this
break something?* — and an engagement belonging to another advisor is exactly the one whose breakage
nobody would notice. The caller's own access to the assessment has already been checked.

It parses the JSON rather than matching a substring, because a `LIKE` against a raw JSON blob
matches a partial UUID. There is a test for that.

**Scope 4 — the standing check.** `dangling_assessment_references()` reports every engagement
holding a dead link. Read-only and unscoped: it **reports rather than repairs**, because what to do
about a dangling reference is a decision (ADR-0048), not something a health check should take. A
test asserts calling it twice still reports the same breakage — nothing is quietly cleaned up.

## What is deliberately NOT done

**Scope 1 — the join table.** Replacing `assessment_ids_json` with `engagement_assessments` and a
real foreign key is the only change that makes this class of bug *impossible* rather than *guarded*,
and it remains the better answer. It needs a migration that moves existing links without loss and
reports rather than silently drops any dangling entries — a contained piece of work, but a schema
change to a live relationship, which is not something to bundle into a housekeeping pass.

**Scope 3 — the repair.** Staging was already repaired on 2026-08-21 under ADR-0048, and production
was measured clean the same day (1 engagement, zero dangling references). There is nothing left to
repair, so the guard and the check are what matter.

The ticket stays open on scope 1.