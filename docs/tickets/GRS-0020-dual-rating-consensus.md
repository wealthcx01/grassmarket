# GRS-0020 — Dual-rating + consensus (governance data model)

**Status:** DONE (reconciled 2026-08-01).

- **Loop:** 5
- **Branch:** `grs-0020-dual-rating-consensus`
- **Status:** In review — PR #22
- **Normative source:** Methodology v1.2 §9 ("solo ratings are drafts, never deliverables"); PRD §3.4.
- **Depends on:** GRS-0009 (assessment lifecycle). No Loop-4 dependency — may interleave with GRS-0016–0019.

## Goal

Methodology §9 enforced in the data model: minimum two raters per module, consensus characterisation, documented dissent.

## Scope

1. Rater assignment (≥2 per module) with independent, mutually-blind rating capture until both submit.
2. Consensus screenful per module: per-subcomponent agree/resolve, with mandatory dissent notes where raters differ and one yields.
3. Assessment lifecycle extended: draft → dual-rated → consensus → finalisable. Finalisation blocked until every assessed module has consensus.
4. Dissent notes persist into the immutable scoring-run record (they are audit evidence).
5. Contracts + Alembic migration; repository scoping preserved (raters see only assessments they are assigned to, plus their own).

## Exit criteria

- An assessment with a solo-rated module cannot finalise (service + HTTP tests).
- Blind-until-both-submit enforced (rater B cannot read rater A's draft ratings).
- Dissent renders into the scoring run and is retrievable for the methods appendix.
- Full gate green; CI green.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `cbc13f2` (GRS-0020: dual-rating + consensus (governance data model)).

This ticket carried no *What shipped* record; the commits above are that record.
