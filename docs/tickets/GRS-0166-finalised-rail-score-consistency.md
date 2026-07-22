# GRS-0166 — Finalised assessment: the wizard rail quotes the locked score (third-surface echo)

**Status:** Done (2026-07-22). The recorded GRS-0161 residual.
**Priority:** MED-HIGH — a trust bug on the surface an advisor shows a client over their shoulder.
**Loop:** demo-readiness.

## Why

GRS-0161 reconciled the deliverable headline with the portfolio: both quote the immutable run's
deterministic `v_index` (with the clamped P10–P90 band). But a FINALISED assessment's wizard —
the rail and the Summary step — still recomputes a live Monte-Carlo score and headlines the P50
median. Same locked inputs, third different number on screen (e.g. rail 58.9 vs portfolio /
deliverable 60.5). An advisor cannot explain that difference to a client.

## Scope

- `BrokeragePortfolioEntry` gains `v_p10`/`v_p90` from the stored run (the repository already
  reads the run for `v_index`); schema + TS mirror.
- When an assessment is finalised, the wizard fetches its portfolio entry and the rail + the
  Summary step's score panel headline the STORED `v_index` with the STORED clamped band and a
  "finalised · locked" label — the same presentation rule the deliverable uses (GRS-0161). The
  live engine still powers the module diagnostics (deterministic, identical on locked inputs);
  only the headline V stops being a live MC recompute.

## Acceptance

Open a finalised assessment: the rail's V equals the portfolio row's V equals the deliverable
headline, labelled as the locked score. Draft/in-progress assessments are unchanged.
