# GRS-0177 — Portfolio demo clarity: dedupe, explain, clean

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: In review (2026-07-26) — grouping, explanations and seed hygiene shipped; the._
staging cleanup script is written but has NOT been run (needs deploy access). **Priority:**
HIGH — the founder's own demo confusion.
**Loop:** founder-feedback remediation, Wave 1.

## Why

Verified on staging: Revolut, Hargreaves Lansdown and WeBull each appear twice — a
`DEMO — ILLUSTRATIVE ONLY` row (22/07 seed) and a `SANDBOX — NON-PRODUCTION` row (21/07 staging
run) with identical scores — plus a stray 0%-coverage Revolut draft and a "Meridian Securities"
record finalised at 2% coverage. Nothing groups same-subject records, and nothing explains what
"Sandbox preview" actually is. The founder: "the demo experience is actually quite confusing".

## Scope

1. **Grouping (frontend only; no API change).** In `frontend/app/assessments/page.tsx`
   (portfolio table, lines 222-301): group rows client-side by trimmed, case-folded `subject`.
   One primary row per subject; the rest are variants. Primary selection order: production
   before sandbox before demo, then latest `updated_at`. Reasoning: the row an advisor acts on
   should be the most real record they own. The primary row gains a count chip
   ("+2 variants") that toggles an indented sub-list of the variant rows (same columns, muted,
   each with its own `ProvenanceBadge` and link). Grouping state is per-render component state;
   nothing persists. Ungrouped subjects render exactly as today.
2. **Explanation.**
   - Rewrite the sandbox checkbox label and `title` tooltip (lines 207-213) in the STYLE-VOICE
     register: a sandbox is your own private practice copy; you can finalise it alone, its
     outputs are watermarked, and it can never reach a client.
   - `frontend/components/ProvenanceBadge.tsx`: add a `title` attribute per provenance with the
     same plain explanation (SANDBOX: private practice copy, self-finalised, watermarked;
     DEMO: illustrative seeded record, not real client work).
   - A dismissible first-visit note above the portfolio table explaining what the DEMO rows are
     and why they exist. Dismissal persists in `localStorage` under `gm:portfolio:demo-note`;
     decision: localStorage, not a backend preference, because the note is a one-time reading
     aid, not account state.
3. **Seed hygiene (backend).** In `src/grassmarket/demo/brokerage_showcase.py`:
   - The idempotency skip set (lines 348-352) currently checks only DEMO-provenance
     assessments. Change it to skip a subject when ANY finalised assessment for that subject
     already exists for the owner, whatever its provenance, so a subject already showcased as a
     sandbox record is not re-created as demo. Keep the per-subject summary status strings
     ("exists (skipped)") accurate about what was found.
   - Commission idempotency: before recording the illustrative commission (step 6, lines
     457-475), list the owner's commission lines and skip recording when a line with the same
     `engagement_id` and `product_id` already exists, so a partial re-run after a mid-seed
     failure can never double-record. Read through the repository/API only; no direct queries.
   - `scripts/seed_demo.py` is unchanged apart from its docstring reflecting the wider skip.
4. **Staging cleanup.** New reviewed script `scripts/staging_cleanup_grs0177.py`:
   - Targets, by explicit criteria: the stray Revolut draft at 0% coverage, the
     "Meridian Securities" assessment (and its engagement/deliverables if any), the 21/07
     sandbox duplicates of the three showcase subjects, and duplicated demo commission lines.
   - Default mode prints what would be deleted (subject, id, provenance, state) and exits;
     deletion requires an explicit `--execute` flag. All lookups and deletions go through
     `Repository`; if a needed delete method does not exist, add it to
     `src/grassmarket/data/repository.py` as an owner-scoped, explicit-id method (no bulk
     wildcard deletes).
   - After cleanup, `scripts/seed_demo.py` re-runs clean on staging; both runs are recorded in
     the PR description.

## Test plan

1. Backend, `uv run pytest tests/test_demo_seed.py` (extend):
   - Running `seed_brokerage_showcase` twice produces identical assessment, engagement,
     deliverable, and commission-line counts (a full-equality re-run assertion, not just
     "no error").
   - Pre-creating a finalised SANDBOX assessment for "Revolut" for the owner, then seeding,
     skips Revolut entirely (no DEMO duplicate, no commission line).
   - A simulated partial run (assessment exists, commission missing) re-run records the
     commission exactly once.
   - Scoping: the seed's records belong to the owner; a second consultant's principal lists
     none of them.
2. Frontend, `bunx vitest run frontend/app/assessments/page.test.tsx` (create):
   - Given a mocked portfolio with production+sandbox+demo rows for one subject, exactly one
     primary row renders with a "+2 variants" chip; expanding shows both variants with badges.
   - The primary row is the production one regardless of array order.
   - The first-visit note renders, and dismissing it sets the localStorage key and removes it.
3. Standing gate: pyright, ruff, tsc, ESLint. Golden master untouched (no scoring-path change;
   `uv run pytest tests/test_atlas_engine_golden_master.py` as the proof).

## Out of scope

- Any change to provenance semantics, the finalisation gate, or ADR-0029.
- The creation-form layout (GRS-0178) and the consulting-commission display (GRS-0187).
- Merging or re-parenting existing records; cleanup deletes strays, it never rewrites history
  on records that remain.
- Server-side grouping or portfolio API changes.

## Acceptance

The demo account's portfolio shows one row per subject with variants grouped behind a count
chip; a first-time viewer can say what SANDBOX and DEMO mean from the screen alone; re-running
the seed twice changes nothing (asserted by test); staging shows no Meridian or 0%-coverage
stray after the cleanup script runs; earnings shows each commission line once.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `a4630cd` (GRS-0177 follow-up: let the cleanup tool actually clean (ADR-0047)), `137c713` (GRS-0177: make the portfolio readable — group, explain, clean).

This ticket carried no *What shipped* record; the commits above are that record.
