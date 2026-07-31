# GRS-0022 — Calibration module

**Status:** DONE (reconciled 2026-08-01).

- **Loop:** 5
- **Branch:** `grs-0022-calibration-module`
- **Status:** In review — PR #24
- **Normative source:** Methodology v1.2 §9 (quarterly calibration; κ_w ≥ 0.75 target; AC1 alongside; anchors κ < 0.6 rewritten).
- **Depends on:** GRS-0020 (rating capture). Content dependency: 3–5 calibration vignettes (founder track).

## Goal

Inter-rater reliability as a measured, managed quantity.

## Scope

1. Vignette model: shared case excerpts with reference ratings (double as Practice Arena content, GRS-0025).
2. Calibration session lifecycle: open → collect blind ratings from all active assessors → close → compute.
3. Statistics: weighted kappa per anchor + Gwet's AC1 (skew-robust for small n); per-assessor and per-anchor agreement views.
4. Anchors scoring κ < 0.6 auto-flagged for rewrite; flags feed the rubric library's misgrading notes (GRS-0008 content).
5. Results persist to assessor quality history (feeds certification evidence, GRS-0023).

## Exit criteria

- κ_w and AC1 reproduce hand-computed fixture values exactly (golden-master discipline applies to the statistics).
- Blind collection enforced; late raters cannot see distributions before submitting.
- Flagged-anchor report generates.
- Full gate green; CI green.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `49c9358` (GRS-0022: calibration module (inter-rater reliability, golden-mastered)).

This ticket carried no *What shipped* record; the commits above are that record.
