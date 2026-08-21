# ADR-0048 — Removing an engagement whose assessments no longer exist

- **Status:** Accepted
- **Date:** 2026-08-21
- **Context sources:** ADR-0047 (non-production record deletion); ADR-0029 (record provenance);
  GRS-0241; the staging measurement of 2026-08-21.

## Context

Five engagements on staging reference assessment ids that **no longer exist**. They were created by
demo seed runs on 20 and 22 July; the assessments they linked were later removed by the GRS-0177
cleanup, which deleted assessments without checking whether an engagement referenced them.

They are the duplicate rows the founder has asked about three times (23/07, 31/07, and again on
21/08). They cannot be removed under ADR-0047, and the reason is worth stating precisely rather
than treated as an obstacle:

- ADR-0047 §1 is unconditional — a **production** record is never deletable, and no argument
  relaxes it.
- GRS-0241 gave engagements a provenance and derived it for existing rows from their linked
  assessments. For these five the derivation produces nothing, because the assessments are gone.
  They stay `production` by default, which is the safe direction working correctly.

So the product is in a stable, correct, and useless state: rows nobody wants, which nothing is
permitted to remove. The temptation is to mark them non-production so the existing tool will take
them. **That would be fabricating a provenance record to obtain a deletion**, which is the exact
class of defect the whole codebase refuses (non-negotiable #3), and it would poison the one field
ADR-0029 exists to keep trustworthy.

## Decision

**A separate, narrower deletion path keyed on orphan-hood rather than on provenance**, requiring
recorded founder authorisation.

`Repository.delete_orphaned_engagement` removes an engagement only when **all** of the following
hold, each checked in the repository and none of them relaxable by an argument:

1. **Every linked assessment id resolves to no row.** Not "some" — an engagement with one live
   assessment and one dangling reference is a broken link to repair, not an orphan to delete.
2. **It links at least one assessment.** An engagement that never linked anything is not orphaned;
   it is simply new, and deleting it would remove work in progress.
3. **It has no deliverables.** A deliverable is output that may have reached a client. Its existence
   means the engagement did something, whatever its links now say.
4. **It has no communication-log entries.** Same reasoning: a recorded conversation is evidence of
   real work.
5. **The caller passes `founder_authorised=True`.** Named so it cannot be set absent-mindedly, and
   so the authorisation is visible at every call site.

ADR-0047 is **not** amended and `delete_assessment` is unchanged. This is a different act on a
different criterion: orphan-hood is a *referential fact* the database can answer, not an inference
about what a record was for.

## Consequences

- The five staging rows are removable, on the founder's explicit instruction, without anyone
  writing a false provenance.
- A production engagement that is *not* orphaned remains as undeletable as before. The new path
  cannot be used as a general escape hatch, because conditions 1–4 exclude every engagement that
  still refers to anything or produced anything.
- **The underlying defect is not fixed by this.** Deleting an assessment still leaves engagements
  pointing at nothing, and nothing catches it. That is GRS-0246, filed alongside this ADR. This
  decision cleans up the damage; it does not close the hole that caused it.
- If the referential-integrity fix (GRS-0246) lands and back-fills or repairs these links instead,
  this path becomes dead code and should be removed rather than kept "just in case" — a deletion
  route with no live use is a liability.
