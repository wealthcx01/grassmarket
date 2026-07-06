# ADR-0008 — Metric & power input uncertainty; honest labelling of unmodelled uncertainty

- **Status:** Accepted (2026-07-05; folded into Methodology v1.2 §7). The per-grade spread *values*
  remain draft-pending-elicitation, carried with a Weight Provenance Record.
- **Date:** 2026-07-05
- **Deciders:** Founder + engineering + elicitation panel (Loop 2)
- **Normative source:** `docs/ATLAS-Methodology-v1.2.md` §7; ADR-0002, ADR-0004.
- **Raised by:** the Loop 1 wrap backlog — §7 modelled uncertainty only for subcomponents, so B and
  P came out as degenerate bands, and the wizard (GRS-0010) is about to render ranges to consultants.

## Context

Methodology v1.1 §7 turns each **subcomponent** rating into a distribution whose width is set by its
evidence grade, and Monte Carlo propagates that to V and L. But **metrics and powers carried no
confidence signal**, so B and P had zero modelled uncertainty — reported as degenerate P10=P50=P90
bands. Two problems: (a) the Business and Power indices are shown without honest ranges, and (b) a
zero-width band *looks* like high confidence when in fact the uncertainty was simply not modelled.
Before the wizard shows ranges, both must be fixed.

## Decision

### 1. Metric input uncertainty — a source/recency grade

Each business-metric observation may carry a **`MetricConfidence`** grade — `audited` /
`management_reported` / `self_reported` / `estimated` — a coarse read of how much the reported
number could move under a better source or fresher data. Monte Carlo applies a **relative
(multiplicative) spread** to the raw value: `raw' = raw · (1 + U(−h, +h))`, where the half-width `h`
is `metric_spreads[grade]`. The perturbed raw flows through the declared normalisation to `n_k`, so
B gets a real range. Audited is tight (draft `h = 2%`) → estimated is wide (draft `h = 40%`).

### 2. Power input uncertainty — evidence grades on Benefit and Barrier

Each power's **Benefit and Barrier** may each carry an ordinal **evidence grade** (E1–E4, the same
scale subcomponents use). Monte Carlo perturbs each graded side by the **adjacent-strength
categorical** already used for maturity levels (reusing `evidence_spreads`), and the engine still
takes the weaker side (Helmer). P gets a real range that widens as evidence weakens.

### 3. Honest labelling — unmodelled uncertainty is a point estimate, never a tight band

Every input grade is **optional**. An input with no grade is **not modelled**: it is held at its
point value and consumes no randomness. Each index band carries a **`modelled` flag** — `True` when
the index's inputs carried a confidence grade, `False` otherwise. **`modelled = False` ⟹ the band is
a point (P10=P50=P90)**, and a renderer must present it as a point labelled "uncertainty not
modelled" — never as a tight (and therefore falsely confident) band. A *modelled* band that happens
to be tight is legitimate confidence; the flag is what distinguishes the two.

Subcomponents always carry evidence grades, so **V, L and per-module q_m are always modelled**; B is
modelled iff at least one metric is graded; P iff at least one power side is graded.

## Consequences

- B and P carry real Monte Carlo ranges once metrics/powers are graded; the wizard can show honest
  bands, and the deliverable layer (later) labels unmodelled indices as points, not tight bands.
- The **families** (relative-multiplicative for metrics, adjacent-strength categorical for powers)
  are structural methodology choices; only the per-grade widths are elicited. Both spread tables are
  enforced non-increasing by grade strength (weaker → at least as wide), so the tight-strong /
  wide-weak guarantee is structural, not assumed.
- **Version stamping.** This changes §7 only; **§5 (the deterministic scores) is byte-identical to
  v1.1**. The deterministic engine, the CoefficientSet, and the ratified golden master therefore keep
  the `1.1` methodology stamp (John's ratified numbers are untouched); the `UncertaintyModel` carries
  the `1.2` stamp. Methodology v1.2 records this convention.
- **Open for ratification:** the metric-confidence grade definitions and both spread tables (draft);
  whether power confidence should instead reuse the committee sign-off record (§8) once dual-rating
  lands. Rater-agreement remains a third, still-unused §7 confidence input.
