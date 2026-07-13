# ADR-0012 — Calibration: the agreement statistics and the session scoping model

- **Status:** Accepted
- **Loop:** 5 (GRS-0022)
- **Normative source:** ATLAS Methodology §9 ("weighted kappa computed per anchor; target κ_w ≥
  0.75; Gwet's AC1 reported alongside while n is small; anchors scoring κ < 0.6 are rewritten");
  Landis-Koch kappa conventions; Gwet's AC1.
- **Builds on:** ADR-0010 (the blind-collection pattern this reuses); the golden-master discipline
  that governs the ATLAS engine (`docs/` testing rules).

## Context

Inter-rater reliability must be a *measured* quantity, computed the same way every quarter, so the
number is comparable across sessions and defensible to a client. Two decisions had to be pinned: the
exact statistics (the methodology names a family, not a formula), and how a shared, org-wide
calibration exercise fits the otherwise strictly owner-scoped data model.

## Decision

### 1. The two coefficients, defined exactly (golden-mastered)

Computed per anchor (a subcomponent) over the assessors who rated the shared vignettes, with the
maturity scale as ordinal categories (Basic=0 … Frontier=3):

- **Weighted kappa (κ_w):** Cohen's weighted kappa with **quadratic** ordinal weights
  (`w_ij = 1 − ((i−j)/(k−1))²`). For the multi-rater case (n > 2, the norm) it is the **mean of the
  pairwise** coefficients across all rater pairs — the standard Landis-Koch multi-rater treatment,
  and the one that keeps the ordinal weighting Cohen's kappa provides (Fleiss' kappa is nominal).
- **Gwet's AC1:** the multi-rater/multi-subject form, reported alongside because it is robust to the
  prevalence/skew that deflates kappa when n is small — the calibration reality. Its chance term
  uses `π_k(1−π_k)` rather than kappa's product of marginals.

Both are hand-computed in `tests/test_calibration_stats.py` (κ_w = 0.5 and AC1 = −1/3 on worked
fixtures) so the engine is pinned to an independently-derived answer, not to itself.

**Degenerate denominator (1 − p_e = 0):** when expected agreement is already perfect (every rater
always used one single category) the coefficient is 0/0. By convention it returns **1.0 iff observed
agreement is also perfect, else 0.0** — stated openly in the code, never a silent NaN (CLAUDE.md #3).

**Fail-loud inputs:** fewer than two raters, no subjects, an out-of-range category, or **ragged data
(raters who did not all rate every vignette for an anchor)** is a refusal, not a defaulted
coefficient. Calibration needs balanced, paired data; the submit endpoint enforces that a rating
covers **exactly** the session's anchors, so the stored data is always balanced.

### 2. Session scoping — shared content, blind results

Calibration is org-wide training/quality data with no client PII, so the strict owner-only rule is
relaxed for it, deliberately and narrowly:

- **Facilitator = admin.** Only an admin opens or closes a session (a non-admin is **403** — the
  action is refused, not the resource hidden, because sessions are not secret).
- **Sessions are readable org-wide.** Any authenticated consultant may list/read sessions and submit
  their own rating — that is how "all active assessors" participate.
- **Each rating is owner-scoped.** An assessor only ever reads their *own* rating (`/my-rating`);
  a co-rater's is never exposed.
- **The blind is structural, via results existence.** The per-anchor coefficients are computed once,
  on close, and stored immutably. While a session is OPEN the result **does not exist** —
  `/results` is a **409** — so a late rater cannot see the distribution before submitting (submitting
  happens only while open; results appear only once closed; the two windows never overlap). This is
  simpler than ADR-0010's per-item blind and sufficient here.

## Consequences

- The statistics are reproducible and comparable session-to-session, and pinned by a golden master —
  a future refactor cannot silently change the number.
- The flagged-anchor report (κ_w < 0.6) is a first-class output of every closed session; it feeds
  the rubric library's misgrading notes (GRS-0008 content) and assessor quality history (GRS-0023).
- **Accepted scope boundary:** results persist to the session; a per-assessor quality *history* view
  aggregating across sessions (GRS-0023 certification evidence) reads these results but is out of
  scope here. The vignette *content* (3–5 real vignettes) is a founder-track authoring task; the
  model, engine, and lifecycle are in place for it.
