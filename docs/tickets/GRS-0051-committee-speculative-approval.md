# GRS-0051 — Reject speculative committee pre-approval

- **Loop:** 5 (Workbench + governance)
- **Status:** Fixed — from the 2026-07-14 audit backlog (GRS-0049, API finding #4).
- **Severity:** Low — a privileged (committee) role can weaken the §8 peer-challenge gate.
- **Normative source:** ATLAS Methodology §8; ADR-0011 (rating gate); CLAUDE.md #8.

## Problem

`decide_committee_item` validated the decider's role, peer-challenge (not their own assessment), and
that the assessment isn't finalised — but it did **not** check that the submitted
`(item_type, item_key, rating)` is a currently-required high-stakes item. A committee member could
record `APPROVED` for a speculative rating (e.g. a power at "Wide" while it is only "Emerging").
Because the finalise / client-pack gate matches on the exact `(type, key, rating)`, if the score
later moved to that rating the gate would clear with **no contemporaneous review** — undercutting the
§8 peer-challenge intent.

## Change

The `POST /assessments/{id}/committee/decide` route now derives the assessment's current required
items (score the current document → `required_committee_items`) and refuses (409) any decision whose
`(item_type, item_key, rating)` is not in that set. Scoring stays in the engine/service layer, not
the repository (CLAUDE.md #5). An unscoreable document has no required items, so any decision on it
is refused.

## Exit criteria

- A decision at a rating the score has not reached, or on a non-existent item key, is 409; a genuine
  `(item, rating)` from the queue still succeeds — pinned by
  `test_a_speculative_pre_approval_is_refused`.
