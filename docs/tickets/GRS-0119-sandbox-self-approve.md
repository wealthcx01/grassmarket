# GRS-0119 — Beta/sandbox self-approve mode

**Status:** Shipped
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** ADR-0029 (demo/illustrative records)

## Why

The *underlying* blocker behind GRS-0117 is that a solo/beta advisor cannot finalise their **own** test
assessment: the governance gate requires a second rater plus committee (ADR-0009). GRS-0117 fixes the
symptom (a seeded demo everyone can view); this fixes the root cause, letting a lone tester self-approve
and finalise their *own* assessment so they can see the **real AI-generated** deliverable drafts. It must
do this **without weakening the production governance gate**: sandbox records are flagged and segregated,
never client-deliverable, and never counted as ratified. The AI-approval non-negotiable (CLAUDE.md #8) is
preserved — a sandbox record is not a shortcut around approval for real work, it is a clearly-labelled
non-production mode. Founder decision (2026-07-16): "Both, demo first" — so this is sequenced **after**
GRS-0117.

## What to build

**Sandbox mode toggle + flag**
- Add a clearly-labelled **non-production sandbox mode** and a sandbox flag on the record, plumbed through
  `auth/`/scoping so sandbox records are segregated and identifiable at the data layer. REUSE the
  demo/illustrative-record semantics from ADR-0029 rather than inventing a parallel concept.

**Self-approve finalisation path (`deliverables/` gating, `workbench/` governance, wizard finalisation)**
- In sandbox mode only, allow the owning tester to self-approve and finalise their **own** assessment so
  the real deliverable generators run against it. The production dual-rating/committee path is unchanged
  for non-sandbox records.
- Sandbox finalisation is **never counted as ratified** and sandbox deliverables are **never
  client-deliverable** — carry the non-production label through every surface they reach.

## Acceptance / verification

- In sandbox mode a solo tester can self-approve and finalise their own assessment and see the real
  AI-generated deliverable drafts, with no second rater or committee.
- Sandbox records are flagged, segregated, never client-deliverable, and never counted as ratified.
- The production dual-rating/committee gate is unchanged for non-sandbox records; the AI-approval
  non-negotiable is preserved (sandbox is a labelled non-production mode, not a bypass of approval for
  real work).

## Not in scope

- The watermarked Revolut demo dataset — GRS-0117 (ships first).
- Any relaxation of the real governance gate for production/client records.
- Admin/oversight views of sandbox usage (deferred to Holy Corner per §6).

## What shipped (Status: Shipped — branch grs-0119-sandbox-self-approve)

The ADR-0029 **record provenance** flag + the sandbox self-approve path, so a solo tester can finalise
their OWN assessment and see the real deliverable drafts **without weakening the production gate**.

**Contract / storage**
- `RecordProvenance` enum (`production` default · `demo` · `sandbox`) + `Assessment.provenance`, set at
  creation and IMMUTABLE. `AssessmentORM.provenance` column + migration `0024_assessment_provenance`
  (existing rows backfill to production).

**Governance (the load-bearing part)**
- `finalise` router: a NON-production record self-approves — the dual-rating (`consensus_blockers`),
  committee (`committee_blockers`), and certified-lead gates are **skipped only when
  `provenance != production`**. Scoreability + the real scoring/deliverable generation are unchanged, so
  the outputs are genuine AI drafts. **The production path is byte-for-byte unchanged** — the AI-approval
  non-negotiable (CLAUDE.md #8) is intact; sandbox is a labelled non-production mode, not a bypass for
  real work.
- Segregation: `ingest_benchmark` refuses a confirmed non-production run — a sandbox score never enters
  the peer population. Non-promotable by construction (no API sets provenance after creation; the create
  route only ever grants `sandbox` or `production`, never `demo`).

**Frontend**
- `RecordProvenance` type + `Assessment.provenance`; `createAssessment(subject, provenance)`.
- A **"Sandbox (self-approve, non-production)"** checkbox on the create form.
- `ProvenanceBadge` watermark ("SANDBOX — non-production, not client-facing") shown in the assessment
  header for any non-production record.

## Acceptance / verification

`tests/test_sandbox_provenance.py` (5): sandbox finalises solo (no co-rater/committee); production still
requires the full gate on the same document; a client cannot mint a demo record; provenance is immutable
across updates; a sandbox run is excluded from the benchmark. Golden master untouched (provenance/gating,
not scoring). Backend + frontend gates green; schema parity green.
