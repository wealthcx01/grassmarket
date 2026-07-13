# GRS-0031 — Prediction register + validation loop + benchmark ingestion

- **Loop:** 6
- **Branch:** `grs-0031-prediction-register-validation`
- **Status:** Planned
- **Normative source:** Methodology v1.2 §11 (validation loop, pre-registered staging); PRD §3.4.
- **Depends on:** GRS-0016 (levers exist in deliverables), GRS-0013 (engagements).

## Goal

The falsifiability machinery: log what we predicted, check it later, and start accumulating the benchmark population.

## Scope

1. Prediction register: at deliverable finalisation, lever-level predictions captured (lever, client baseline, predicted delta, horizon, linked scoring run).
2. Follow-up scheduler: 12/24-month re-contacts (retainer clients continuous); due follow-ups surfaced to the owning advisor.
3. Realised-value capture + hit-rate scoring (Brier scoring for probabilistic claims; simple hit/miss for directional ones).
4. Anonymised benchmark ingestion: finalised scores stripped of client identity into the benchmark population store. Stage 2 percentile normalisation is a FUTURE ticket triggered at n ≥ 10 — this ticket builds the store, not the normalisation.
5. Anonymisation provable: no identifier (name, entity id, contact) survives into the benchmark rows.

## Exit criteria

- Predictions auto-extracted from a roadmap's levers at finalisation.
- A due follow-up round-trips to a scored outcome.
- Anonymisation tested (identifier-absence assertions on benchmark rows).
- Full gate green; CI green.
