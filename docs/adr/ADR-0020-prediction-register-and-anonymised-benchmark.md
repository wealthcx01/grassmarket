# ADR-0020 — Prediction register, Brier scoring, and an anonymised benchmark

- **Status:** Accepted
- **Loop:** 6 (GRS-0031)
- **Normative source:** Methodology v1.2 §11 (validation loop, pre-registered staging); PRD §3.4;
  CLAUDE.md #6 (immutable runs), #9 (scoping), ADR-0002 (score ≠ currency).
- **Builds on:** GRS-0016 (value-bridge levers), GRS-0009 (the scoring runs predictions cite).

## Context

The methodology is only credible if it is falsifiable: we must record what we predicted, check it
later, and accumulate a benchmark population — without ever exposing a client. Three decisions:
what a prediction is, how a realised outcome is scored, and how the benchmark stays anonymous.

## Decision

### 1. Predictions are lever-level and pre-registered against an immutable run

At finalisation each value-bridge **lever** becomes a `Prediction`: its NPV as the predicted signed
value impact, a horizon, a follow-up date, a probability (the model's confidence the direction
holds), and the **scoring-run id** it is staked against. `predictions_from_levers` does the
extraction deterministically (one prediction per lever, order-preserving), so a roadmap's levers ARE
its pre-registered predictions. Registration is owner-scoped (the run must be the caller's own).

### 2. Scoring is a directional hit/miss plus a Brier score

On follow-up, `record_realised_value` scores the prediction with the pure `score_prediction`:

- **Directional** — a HIT iff the realised value moved in the same non-zero direction as predicted
  (a predicted gain realised as a gain; a predicted reduction realised as a reduction). A realised
  zero is no move → MISS.
- **Brier** — `(probability − outcome)²`, outcome 1 for a hit / 0 for a miss: confidence is rewarded
  when right and penalised when wrong. Golden-mastered (0.8→hit = 0.04; 0.8→miss = 0.64).

Money stays Money (a cross-currency realised value is refused — no FX). Scoring is single-shot: a
prediction scores once, then is locked. Due follow-ups (past date, still pending) are surfaced to
the owning advisor.

### 3. The benchmark population is anonymised BY CONSTRUCTION — provably de-identified

Ingesting a **finalised** scoring run into the benchmark copies ONLY the score (`v_index`, P10/P90),
its uncertainty rating, the methodology/coefficient versions, and a non-identifying `sector`. The
`BenchmarkRow` contract and its table have **no** column that could re-identify anyone — no owner,
no assessment id, no scoring-run id, no client name/entity/contact. This is a structural guarantee,
not a scrubbing step: there is nowhere for an identifier to live. Tests assert the identifier-field
set is disjoint from the row's fields AND that none of the source run's identifiers appear in a
dumped row. The benchmark is org-wide and de-identified, so it is **not** owner-scoped — reading it
leaks nothing. Only a finalised run may enter (a draft score is not a benchmark).

## Consequences

- Every finalisation can pre-register falsifiable predictions and feed an anonymous benchmark; the
  validation loop can now accumulate hit-rates and a population.
- De-identification cannot regress by accident — the anonymised row physically has no field to leak.
- **Accepted scope boundaries:** Stage-2 percentile normalisation over the benchmark population is a
  FUTURE ticket, triggered at n ≥ 10 (this ticket builds the store, not the normalisation). The
  follow-up **scheduler** (retainer-continuous re-contacts, notifications) surfaces due items via
  `list_due_follow_ups`; the automatic notification/cron is out of scope. Auto-registration at
  deliverable finalisation is wired via the `/predictions` register endpoint fed by the roadmap's
  levers; the exact finalisation hook is a thin call the deliverable flow makes.
