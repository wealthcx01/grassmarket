# GRS-0007 — Uncertainty completeness + honest labelling

- **Loop:** 2, first ticket (see PRD §9)
- **Branch:** `grs-0007-uncertainty-completeness`
- **Status:** In review
- **Normative source:** `docs/ATLAS-Methodology-v1.2.md` §3.3, §7; ADR-0008.
- **Depends on:** GRS-0005 (Monte Carlo).

## Goal

Clear the Loop 1 debt **before** the wizard shows ranges: model metric and power input uncertainty
so §7 yields real B and P ranges (today only subcomponents carry evidence grades, so B/P were
degenerate bands), and **label unmodelled uncertainty honestly** — a point estimate, never a tight
(falsely confident) band.

## Decision (ADR-0008, Accepted; Methodology v1.2)

- **Metrics** carry an optional source/recency grade `MetricConfidence` (audited / management /
  self-reported / estimated). Monte Carlo applies a **relative multiplicative spread** to the raw
  (`raw' = raw·(1 + U(−h,+h))`), which flows through the declared normalisation → a real B range.
- **Powers** carry optional evidence grades on **Benefit and Barrier** (E1–E4). Monte Carlo perturbs
  each graded side by the **adjacent-strength categorical** already used for maturity levels; the
  engine still takes the weaker side → a real P range.
- **Honest labelling:** every grade is optional. An ungraded input is **not modelled** — held at its
  point value, consuming no randomness. Each `Band` carries a **`modelled` flag**; `modelled = False`
  ⟹ the band is a point (P10 = P50 = P90), which a renderer shows as a point labelled "uncertainty
  not modelled", never a tight band. Subcomponents always carry grades, so V, L and q_m are always
  modelled; B iff a metric is graded, P iff a power side is graded.
- **Version stamping:** §5 is byte-identical to v1.1, so the deterministic engine, CoefficientSet,
  and golden master keep the `1.1` stamp (John's ratified numbers untouched); the `UncertaintyModel`
  carries `1.2`. Methodology v1.2 records this convention and amends §3.3/§7 only.

## What shipped

- **Contracts:** `common.MetricConfidence` (ranked source grade); `UncertaintyModel.metric_spreads`
  (draft, provenance-carrying, non-increasing by grade); `MetricObservation.confidence` and
  `PowerObservation.benefit_grade` / `barrier_grade` (all optional).
- **Monte Carlo:** metric + power perturbation (a generic adjacent-ordinal sampler now serves both
  maturity levels and power strengths — the RNG stream for ungraded Meridian is byte-identical to
  v1.1, so every existing seeded test is unchanged); `Band.modelled` honesty flag; the draft model
  gains `metric_spreads` and is stamped `1.2`.
- **Docs:** ADR-0008 (Accepted); `docs/ATLAS-Methodology-v1.2.md` (supersedes v1.1); ADR README +
  CLAUDE.md normative pointer updated.

## Tests

- **B/P widen with weaker inputs** — audited-source B is strictly narrower than estimated-source B;
  E4 powers give a strictly narrower P than E1 powers; both modelled.
- **Honest labelling** — an unmodelled band (Meridian: B and P) is always a flagged point
  (`modelled=False`, P10=P50=P90); no unmodelled band is ever given a spurious width. V/L always
  modelled. The `UncertaintyModel` rejects incomplete metric_spreads.
- **No regression** — every Loop 1 Monte Carlo test (determinism, P50-on-point, evidence width,
  tornado, Not-Assessed) passes unchanged, because ungraded inputs consume no RNG.

## Out of scope (Loop 2 backlog, still open)

The deliverable layer must render `modelled=False` bands as points labelled honestly — that is
GRS-0010 (wizard) and the later deliverable builder. Rater-agreement remains an unused third §7
confidence input, pending dual-rating.
