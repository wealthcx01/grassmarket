# GRS-0119 — Beta/sandbox self-approve mode

**Status:** Planned
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
