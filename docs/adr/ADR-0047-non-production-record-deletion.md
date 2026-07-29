# ADR-0047 — Deleting a non-production assessment together with its scoring runs

- **Status:** Accepted
- **Date:** 2026-07-29
- **Supersedes / amends:** clarifies the scope of non-negotiable #6 (CLAUDE.md); relates to
  ADR-0029 (record provenance)
- **Driver:** GRS-0177 staging cleanup; founder review of 2026-07-26 ("the duplicate rows are
  still in the staging database")

## Context

Non-negotiable #6 says scoring runs are immutable, versioned and append-only. `delete_assessment`
implemented that literally: any assessment carrying any scoring run was refused.

That refusal made the cleanup tool useless for the thing it was built for. The staging duplicates
the founder wants gone are all *finalised* demo and sandbox records — WeBull (demo), Hargreaves
Lansdown (demo), Revolut (sandbox), Revolut (demo), each at 100% coverage with a run attached. The
script could delete nothing, so the confusing portfolio stayed confusing while the code reported
success.

The mistake was treating "a scoring run exists" as the thing #6 protects. What #6 protects is the
**audit trail of real client work**: the guarantee that a score shown to a client, priced against,
or entered into the benchmark population cannot be rewritten or quietly removed.

## Decision

`Repository.delete_assessment` takes an explicit keyword argument `discard_scoring_runs`
(default `False`).

1. **A production record is never deletable through this method.** No argument relaxes this. This
   guard is checked first and is unconditional.
2. **By default a record carrying any scoring run is refused**, exactly as before. The default
   path fails loud; nothing changes for existing callers.
3. **`discard_scoring_runs=True` permits deletion of a non-production record with its runs.**
   Because guard 1 runs first, this flag can only ever reach a `DEMO` or `SANDBOX` record.
4. Deleting the runs also deletes the rows that reference them by id — `AINarrativeORM`,
   `PredictionORM`, `DeliverableORM` — in the same transaction. Orphaned references are the silent
   inconsistency non-negotiable #3 exists to prevent.

`scripts/staging_cleanup_grs0177.py` exposes this as `--discard-scoring-runs`, and reports
separately on records it will not touch and why.

## Why this does not weaken #6

A demo or sandbox record is not an audit trail. By ADR-0029 it is:

- watermarked and labelled non-production wherever it is displayed,
- never client-facing,
- excluded from the benchmark population by an explicit check in `record_benchmark_row`,
- excluded from earnings and from any priced or committed output.

Nothing downstream depends on its run, so there is no trail to preserve. Refusing to remove one
protects no client and no record; it only leaves duplicate rows that make the product harder to
read.

The immutability guarantee that matters is unchanged and is now enforced by the guard that
actually expresses it — provenance — rather than by a proxy (run existence) that caught the wrong
records.

## What is still refused

- Any deletion of a production record, finalised or not.
- Any deletion of a scoring run on its own. Runs are still never updated in place and never
  individually removable; they are only discarded as part of removing the non-production
  assessment that owns them.
- Bulk or wildcard deletion. Every call still names one assessment id and is owner-scoped.

## Amendment, 2026-07-29 — deleting a production record by founder decision

The cleanup left two production strays on the staging advisor account: a `Revolut` draft at 0%
coverage and `Meridian Securities` finalised at 2%. Neither is client work. A record finalised on
2% of the evidence is not an assessment of anything, and a 0% draft is a mis-click. The founder
reviewed both and asked for them to go.

The original decision said no argument relaxes the production guard. That was right as a default
and wrong as an absolute: it left the only person entitled to make the call without a way to make
it, and the alternative was routing around the repository layer with raw SQL, which is worse.

So `delete_assessment` gains a second flag, `delete_production_record`, with three conditions that
all have to hold:

1. The flag is passed **in the call**, per record. It is not inferable from any criterion.
2. The caller is the **founder or an admin** (`ScopeViolationError` otherwise).
3. The deletion writes an **`ASSESSMENT_DELETED` audit event** naming the subject and the run
   count. The audit log is append-only, so the trace outlives the record.

`scripts/staging_cleanup_grs0177.py` exposes this as `--delete-production-id UUID`, repeatable and
**deliberately not driven by the matching criteria**. The script finds candidates by rule; a
production record is only removed when the founder has typed its id. A named id that matches no
candidate aborts the whole run rather than deleting on the strength of a possible typo.

What this does not do: it creates no bulk path, no criteria-driven production deletion, and no way
for an advisor to delete their own production record. The default is still refusal.

## Consequences

- The GRS-0177 cleanup can do its job on staging.
- `test_a_finalised_record_is_refused_because_its_scoring_run_is_immutable` still passes unchanged:
  the default is still refusal. Two tests are added for the new path — a finalised sandbox record
  is deletable with the flag and leaves no orphans; a production record is refused *with* the flag.
- A future operator-facing "retire" state (soft delete for production records) is still the right
  answer for real client work and remains unbuilt. This ADR deliberately does not create one.
