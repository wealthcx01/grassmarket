# GRS-0167 — One-number rule: every surface quotes the deterministic score (ADR-0040)

**Status:** Done (2026-07-23). THE finding of the 2026-07-22 staging rerun (5/5 personas,
top severity). **Priority:** HIGHEST. **Loop:** staging-rerun remediation.

## Why

Live surfaces headline the Monte-Carlo P50; scenario baseline, build-up chart, AI narrative and
locked surfaces headline the deterministic score → the number jumps at finalisation (63.1→64.9
etc.), three V values coexist pre-lock, and approved narratives contradict the screen. Every
technical persona called it disqualifying. See ADR-0040.

## Scope

- `LiveScore` += deterministic `v_point/b_point/p_point/l_point` (from `AtlasResult.composite`).
- Frontend headlines bold the point with the MC band clamped around it, labelled
  "modelled P10–P90" (rail LiveSummary, Summary LiveScorePanel, Interpretation prose, waterfall).
- No scoring change; golden master untouched.

## Acceptance

The finalise click does not change the headline; the build-up chart recomputes to the headline;
rail = summary = scenario baseline = locked = portfolio = deliverable.
