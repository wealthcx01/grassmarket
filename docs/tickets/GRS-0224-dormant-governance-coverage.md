# GRS-0224 — Repository-layer coverage for the dormant peer-governance code

**Status:** Planned (2026-07-29, arising from GRS-0188). **Priority:** LOW, unless the peer
machinery is re-mounted, in which case it is a blocker.

## Why

GRS-0188 retired the peer-rating, Rating Committee and calibration routes to 410 under ADR-0041.
The machinery behind them is deliberately dormant rather than deleted, so the decision is
reversible when the network is bigger than one founder and a handful of advisors.

The tests for that machinery were not so lucky. `tests/test_calibration.py`,
`tests/test_committee.py` and `tests/test_dual_rating.py` were HTTP-level end to end, so retiring
the routes retired their coverage with them. What survives is
`tests/test_calibration_stats.py` (the kappa/AC1 maths, pure) and `tests/committee_helpers.py`
(the approved-decision tuple the dormant `assert_committee_approved` unit tests need).

So today the repository sections for dual rating, committee decisions and calibration sessions are
untested. That is a real gap. It is recorded here rather than left for whoever re-mounts these
routes to discover the hard way.

## Scope

Rebuild the lost coverage against the repository layer, where it should arguably have lived all
along:

1. **Dual rating**: assignment, blind drafts, the submit lock, consensus resolution, and the
   scoping rule that lets an assigned rater reach the rating surface without reaching the owner's
   document (ADR-0010).
2. **Committee decisions**: recording a decision, the re-rating invalidation rule (a decision only
   clears while its rating still matches), and the peer-challenge rule that a member may never
   decide on their own assessment.
3. **Calibration sessions**: open, blind ratings, the submit lock, close with fewer than two
   raters refused, results blind until close and org-wide visible after.

All at the repository layer, with no HTTP involved, so the coverage survives the routes being
mounted or not.

## Test plan

The tests are the deliverable. Each of the three areas above becomes a file exercising the
repository methods directly.

## Out of scope

- Re-mounting any retired route. That is a founder decision and would reverse ADR-0041.
- The founder review gate (GRS-0188), which has its own tests.

## Acceptance

The dormant governance code is covered without any of its routes being reachable, so a future
decision to re-mount is a routing change rather than an act of faith.
