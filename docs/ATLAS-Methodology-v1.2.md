# ATLAS Methodology v1.2

**Bruntsfield Capital — CONFIDENTIAL — July 2026**

The Bruntsfield Platform Power assessment method. This document is **normative** for the Grassmarket
scoring engine and **supersedes v1.1**. It is a focused successor: it amends **§3.3 and §7 only** —
the uncertainty machinery — and restates those sections in full below. **All other sections (§1–§2,
§4–§6, §8–§12) are unchanged from v1.1** and are incorporated by reference.

---

## 1.1 Changelog: v1.1 → v1.2

v1.2 completes §7: modelled uncertainty now covers **metrics and powers**, not only subcomponents,
and unmodelled uncertainty is **labelled honestly** (a point estimate, never a tight band). Each is
an accepted ADR; **no coefficient value changes** and **the deterministic scores (§5) are
byte-identical to v1.1**.

| Amendment | Section | ADR |
|---|---|---|
| Metric observations carry a **source/recency grade** (`MetricConfidence`) driving a relative spread on the raw → real B ranges | §3.3, §7 | ADR-0008 |
| Power **Benefit/Barrier** carry optional evidence grades → real P ranges (adjacent-strength categorical) | §7 | ADR-0008 |
| **Honest labelling:** an ungraded input is not modelled; its index band is a **point estimate** flagged `modelled = False`, never a tight band | §7 | ADR-0008 |

### Version-stamping convention (v1.2)

§5 is unchanged, so the **deterministic engine, the CoefficientSet, and the ratified golden master
retain the `1.1` methodology stamp** — John's ratified numbers are untouched. Only the **uncertainty
model** carries the `1.2` stamp, because §7 is what this version extends.

## 3.3 Evidence-strength & source scales (amended)

Every **subcomponent and power** rating carries an **evidence-strength grade**, which drives
uncertainty (§7):

| Grade | Meaning |
|---|---|
| E1 Self-reported | Client statement only, no corroboration |
| E2 Interview | Corroborated in structured interview with the accountable owner |
| E3 Artifact | Verified against documents, dashboards, configs, metrics |
| E4 Observed | Directly demonstrated / inspected by the assessor |

Every **business-metric** observation may carry a **source/recency grade** (`MetricConfidence`),
which drives its uncertainty (§7) — a coarse read of how much the reported number could move under a
better source or fresher data:

| Grade | Meaning |
|---|---|
| Audited | Audited / current filings — tightest |
| Management-reported | Management accounts |
| Self-reported | Client statement only |
| Estimated | Derived or stale — widest |

All grades are **optional**: an ungraded input is not modelled for uncertainty (§7, honest labelling).

## 7. Uncertainty (amended)

ATLAS captures confidence and uses it — the differentiator most maturity assessments lack. Four
mechanisms:

- **Input distributions.** Every input that carries a confidence signal becomes a distribution:
  - a **subcomponent** rating, by its evidence grade (E4 → tight; E1 → wide, spanning the adjacent
    level), sampled as an adjacent-level categorical over the maturity scale;
  - a **power's** Benefit and Barrier, each by its evidence grade, sampled as an adjacent-strength
    categorical over None/Emerging/Established/Wide (the engine still takes the weaker side, §8);
  - a **metric's** raw value, by its source/recency grade, sampled as a relative multiplicative
    spread `raw' = raw·(1 + U(−h,+h))` and flowed through the declared normalisation.

  Monte Carlo over all inputs yields V, L, B and P (and per-module q_m) as P10/P50/P90 ranges.
  Reports state "V = 61 (range 55–68)", never a bare point. The per-grade widths are elicited
  coefficients with provenance; both spread tables are **non-increasing by grade strength** (weaker
  evidence is at least as wide), so the tight-strong / wide-weak guarantee is structural.

- **Honest labelling (v1.2).** Input grades are optional. An input with **no grade is not modelled**:
  it is held at its point value, and its index band is a **point estimate** flagged `modelled =
  False` (P10 = P50 = P90). A renderer must present an unmodelled band as a **point** labelled
  "uncertainty not modelled" — never as a tight, and therefore falsely confident, band. Because
  subcomponents always carry evidence grades, **V, L and q_m are always modelled**; B is modelled iff
  a metric is graded; P iff a power side is graded. A zero-width band is never presented as confidence.

- **Assessment Uncertainty Rating** (Low / Medium / High / Very High) per module and overall —
  Morningstar Uncertainty Rating pattern — driven by evidence mix, coverage (% assessed), and rater
  agreement. Printed next to every headline number.

- **Sensitivity:** every report includes a tornado diagram (which inputs move V most) and weight
  stability intervals (which conclusions survive weight movement). If "fix Back Office first" only
  holds for a narrow α band, the report says so.

---

## Sections unchanged from v1.1

§1 (Purpose & Status), §2 (Framework & triad), §4 (Rubric Anchors), §5 (Aggregation — including
§5.2a gate, §5.3 group-weighted B, §5.4), §6 (Coefficient Provenance), §8 (Seven Powers), §9
(Certification & Calibration), §10 (Value Bridge), §11 (Validation Loop), §12 (Method Sources) are
carried forward verbatim from `docs/ATLAS-Methodology-v1.1.md`.
