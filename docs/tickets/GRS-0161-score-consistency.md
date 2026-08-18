# GRS-0161 — Reconcile the two V numbers (portfolio deterministic vs deliverable median)

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: Done (2026-07-21). Deliverable headline + component statements now report the deterministic v_index (matching._
**Priority:** HIGH — trust/correctness. **Loop:** demo-readiness.

## Why

The same finalised assessment shows **two different V numbers** on two surfaces:
- the **Portfolio list** shows the **deterministic** engine V (Revolut 60.5, HL 57.2, WeBull 54.7 —
  reproduced exactly by an independent `compute_score` recompute of the locked inputs);
- the **deliverable** headline shows the **Monte-Carlo median** V (Revolut 58.8, HL 56.5, WeBull 53.5).

Both are legitimate outputs, but an advisor (or a hire being shown the demo) seeing 60.5 in the list and
58.8 in the report will read it as a bug and lose trust — exactly the founder's concern.

## Scope

- Decide the **canonical headline V** (recommendation: the deterministic point estimate is the score;
  the P10–P90 band conveys uncertainty) and make every surface report the same headline number.
- Wherever the median is shown, **label it** ("median of modelled range") so the point vs P50 distinction
  is explicit, never silent.
- Add a regression test asserting portfolio `v_index` == the deliverable headline for a fixed fixture.

## Acceptance

Portfolio, assessment detail, live-score, and every deliverable agree on the headline V for a given
assessment (or clearly label any deliberately-different figure).

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `7a36a1f` (GRS-0161: reconcile the two V numbers — deliverable headlines the stored v_ind).

This ticket carried no *What shipped* record; the commits above are that record.
