# GRS-0060 — Dual-rating & committee sign-off have no UI (advisor cannot finalise in-product)

- **Loop:** 5 (Workbench + governance)
- **Status:** Open — found in the 2026-07-15 exhaustive every-control functional audit.
- **Severity:** HIGH (fit-for-purpose) — blocks the core workflow's completion through the UI.
  Not a defect in existing UI; a missing feature surface.

## Finding

The exhaustive audit drove every interactive control in the product (every route, nav link,
login/logout, the full assessment data-entry surface — metrics, powers, all 51 subcomponents,
guidance panels, scenarios, autosave — pipeline, prospect detail, stage moves, workshop schedule +
deliver, the earnings statement download, and every Workbench panel including drills, the practice
arena role-play, and calibration). **Every control works, with zero console/JS/5xx errors.**

The one real gap: the **Finalise & lock** button honestly reports its blockers — "solo-rated · needs
a second independent rater · consensus · Rating Committee sign-off" — but there is **no UI to resolve
them.** `lib/api.ts` exposes no committee or rating functions; no component invokes them; the
Workbench "Rating committee" panel only links to `/assessments`. The dual-rating flow (assign a
second rater, submit a blind co-rating, resolve consensus/dissent) and the committee decision flow
(queue → approve/reject with rationale) exist **only in the API/backend** — the local seed drives
them programmatically.

**Consequence:** a lone advisor working through the UI can score an assessment but **cannot finalise
it** — and therefore cannot generate a client deliverable — without out-of-band API calls. The
governance backend (dual-rating §9, committee §8) is fully built and unit-tested; only its UI is
missing.

## Scope for the implementing work

1. **Dual-rating UI** (on the assessment): assign/see the module raters, a second rater submits their
   blind rating, surface consensus vs documented dissent, and clear the §9 block.
2. **Committee UI**: a per-assessment queue of high-stakes items (power Established+, triad above
   None, module Frontier) with an approve/reject + rationale/dissent control (committee/admin only),
   clearing the §8 block. (Backend already enforces the peer-challenge + speculative-approval guards,
   GRS-0051.)
3. Wire `lib/api.ts` to the existing endpoints; role-gate the UI to mirror the JWT claims.

## Exit criteria

- An advisor (with a second rater and a committee member) can take an assessment from scored →
  consensus → committee sign-off → finalised entirely in the UI, and then generate a client pack.

## Audit note (no code defects found)

Nothing in the existing UI is broken. This ticket records a *missing* surface, not a regression. The
audit's transient failures were all test-harness artifacts (a strict selector, an unexported env
var), re-verified as correct product behaviour.
