# ATLAS Methodology v1.0

**Bruntsfield Capital — CONFIDENTIAL — July 2026**

The Bruntsfield Platform Power assessment method: scales, rubrics, aggregation, coefficient provenance, uncertainty, and the value bridge. This document is **normative** for the Grassmarket scoring engine.

---

## 1. Purpose & Status

This document is the single source of truth for how ATLAS turns evidence about a platform business into scores, ratings, and value statements. It is the technical appendix behind every client deliverable, the textbook for advisor certification, and the specification the software implements. Nothing in the scoring engine may diverge from this document; changes require an ADR and a new methodology version.

**Status: v1.0 — expert-calibrated.** ATLAS v1 coefficients derive from structured expert elicitation (§6), not statistical fitting. This is stated openly in client materials. The methodology follows the design standards used by CMMI/SCAMPI appraisals, DOE C2M2, and ISO/IEC 33020 process assessment, the qualitative-rating governance used by Morningstar's Economic Moat methodology, and MCDA weighting science (swing weighting, AHP, Delphi, Cooke's method). A pre-registered validation loop (§11) upgrades the calibration as engagement data accumulates.

## 2. The Framework

ATLAS assesses a platform business through three lenses combined into one composite, interpreted through the Platform Power triad:

| Index | What it measures | Primary inputs |
|---|---|---|
| **B — Business** | What the business achieves economically | Scale/activity, financials, unit economics (normalised per §5.3) |
| **P — Strategic Power** | Why those achievements are defensible | 7 Powers evidence: Benefit + Barrier per power (§8) |
| **L — Infrastructure** | Whether the plumbing can carry the ambition | 51 subcomponents across 9 modules, maturity-rated (§3–5) |
| **V — Platform Value** | Composite: V = θ_B·B + θ_P·P + θ_L·L | Elicited θ weights with provenance (§6) |

**The Platform Power triad** is the interpretive layer reported to clients, computed from the same inputs:

- **Economic Value** — does the platform create value that compounds with scale? Scored from B's unit-economics group plus demand-side scale and take-rate durability evidence (constructs from Parker/Van Alstyne and Gawer/Cusumano platform economics).
- **Perceived Value** — do the customer segments that matter perceive that value, and is perception strengthening? Scored from the Benefit-side evidence of Branding and Switching Costs plus retention/NPS/pricing-power inputs.
- **Defence Value** — what realistically prevents competitive parity? The Barrier-side aggregate across all seven powers: the moat proper.

Each triad dimension is reported as an ordinal rating with falsifiable duration semantics (§8), Morningstar-style, never as a decimal.

## 3. Scales & Rating Semantics

### 3.1 The maturity scale

Subcomponents are rated on four levels. The numeric mapping is an index for computation, not a measurement; clients see the labels.

| Level | Index | Declared semantics (ISO 33020-style) |
|---|---|---|
| Basic | 0.2 | Capability absent or ad-hoc. The function is achieved manually, unreliably, or not at all. Evidence of repeated operational pain. |
| Developing | 0.5 | Capability exists but incomplete: partial coverage, manual workarounds, known single points of failure. Does not reliably achieve the outcome under load or change. |
| Advanced | 0.8 | Capability achieves its outcome reliably: automated, monitored, documented, covering the material scope. Recognised opportunities for improvement remain. |
| Frontier | 1.0 | Capability is a source of advantage, not just adequacy: differentiating performance, extensibility, or economics. **Frontier is not the universal target** — each rubric states for which operating models Frontier is economically rational (DORA capability principle). |

### 3.2 Non-score states (first-class, never imputed)

- **Not Applicable:** the subcomponent is out of scope for this platform's operating model. Requires documented rationale. Removed from the denominator; module weights renormalise. (C2M2 scope-exclusion pattern.)
- **Not Assessed:** in scope but not evidenced. Never scored as zero, never averaged around. Blocks a module rating gate (§5.2) or forces the module's uncertainty band to widen, and is flagged in every output. "Not assessed" ≠ "bad" — conflating them was a defect in the prototype.

### 3.3 Evidence-strength scale

Every rating carries an evidence-strength grade, which drives uncertainty (§7):

| Grade | Meaning |
|---|---|
| E1 Self-reported | Client statement only, no corroboration |
| E2 Interview | Corroborated in structured interview with the accountable owner |
| E3 Artifact | Verified against documents, dashboards, configs, metrics |
| E4 Observed | Directly demonstrated / inspected by the assessor |

## 4. Rubric Anchors

The rubric library — one anchor set per subcomponent × level, 51 × 4 = 204 anchors — is ATLAS's core IP and the single highest-leverage artifact for repeatability (SCAMPI/C2M2 pattern). Template per anchor:

- **Anchor statement:** observable and behavioural (BARS-style). Not "good order routing" but "router selects venue per order using static rules reviewed at least quarterly; no real-time cost model".
- **Required evidence:** 2–4 artifacts that must exist to award the level (documents, demos, metrics, configs).
- **Differentiator questions:** 1–2 questions that separate this level from its neighbours.
- **Misgrading notes:** the known ways assessors over/under-rate this item, updated after every calibration session (§9).

### Worked example — OEMS / Smart Order Routing

| Level | Anchor (abridged) |
|---|---|
| Basic | Orders route to a single default venue or manual venue choice. Evidence: order-flow config; venue fill reports. Differentiator: "Can any order reach more than one venue without a human deciding?" |
| Developing | Static rule-based routing (e.g. by instrument/size); rules changed by release, not data. Evidence: routing rule set; change log. Misgrading note: vendors often demo dynamic routing that is disabled in production — verify the prod config (E3+). |
| Advanced | Data-driven routing with venue cost/fill models, monitored fill-quality KPIs, quarterly recalibration. Evidence: SOR model docs; fill-quality dashboard; recalibration records. |
| Frontier | Adaptive routing with real-time venue analytics and measurable execution-quality advantage vs benchmark. Rational for flow-heavy multi-venue brokers; NOT economically rational for a single-market wealth platform — do not treat as target there. |

## 5. Aggregation

### 5.1 Module quality (continuous track)

```
q_m = α · ( Σ_c λ_{m,c} · s_{m,c} / Σ_c λ_{m,c} )  +  (1 − α) · min_c s_{m,c}
```

The weighted-average term rewards breadth; the min term encodes the bottleneck principle (a module performs like its weakest part). α ∈ [0,1] is an elicited parameter with a published stability interval (§6). Denominators include only Applicable, Assessed subcomponents.

### 5.2 Module rating gate (headline track)

Following C2M2's cumulative logic, the client-facing module rating is rule-based, not arithmetic: a module cannot be reported **Advanced** if any critical subcomponent is Basic, and cannot be reported **Frontier** unless all critical subcomponents are Advanced+ with evidence E3+. The continuous q_m drives prioritisation and benchmarking; the gate drives the words on the page. Scores never contradict ratings because they answer different questions (how much vs which band).

### 5.3 Business index

```
B = Σ_k w_k · n_k(x_k) / Σ_k w_k
```

Each metric has an explicit normalisation spec n_k: declared unit (captured in the UI, never inferred), direction, and anchor points documented in the metric register. From Stage 2 (≥10 engagements), n_k becomes percentile-vs-benchmark-population. The prototype's unit-sensitive log heuristic is retired.

### 5.4 Power index and Platform Value

```
P = Σ_j w_j · strength_j / Σ_j w_j
V = θ_B·B + θ_P·P + θ_L·L,   Σθ = 1 (enforced)
```

L aggregates module qualities with the same blend structure as q_m (weights δ_m, critical-module min term). All key sets (modules, subcomponents, powers, metrics) are validated against a single registry at load time; **an unknown key is a refusal to score, not a default** — the class of silent-fallback defects found in the prototype is structurally impossible.

## 6. Coefficient Provenance

Every number that is not a client input — λ, δ, w, α, α_L, θ, critical-module sets — has a **Weight Provenance Record**: who set it, when, by what method, with what dispersion, and when it is next reviewed. The v1 elicitation protocol:

- **Panel:** 4–8 domain experts (founder + senior advisors + invited practitioners).
- **Primary method — swing weighting** per module and for θ: rank the swings (worst→best on each criterion), then ratio-scale them. Swing weighting reflects range sensitivity, which direct "importance" voting gets wrong (MCDA good practice).
- **Cross-check — AHP** pairwise comparisons with consistency ratio ≤ 0.10; group aggregation by geometric mean.
- **Convergence — two-round Delphi** with anonymised feedback; residual disagreement resolved by performance-weighting experts on calibration questions with known answers (Cooke's Classical Method).
- **Publication:** each report's methods appendix states "weights expert-elicited [date], review due [date]"; sensitivity analysis (§7) shows which conclusions are robust to weight movement (weight stability intervals).

## 7. Uncertainty

ATLAS captures confidence and uses it — the differentiator most maturity assessments lack. Three mechanisms:

- **Input distributions:** each subcomponent rating becomes a distribution whose spread is set by its evidence grade (E4 → tight; E1 → wide, spanning the adjacent level). Monte Carlo over all inputs yields V, L, B, P as P10/P50/P90 ranges. Reports state "V = 61 (range 55–68)", never a bare point.
- **Assessment Uncertainty Rating** (Low / Medium / High / Very High) per module and overall — Morningstar Uncertainty Rating pattern — driven by evidence mix, coverage (% assessed), and rater agreement. Printed next to every headline number.
- **Sensitivity:** every report includes a tornado diagram (which inputs move V most) and weight stability intervals (which conclusions survive weight movement). If "fix Back Office first" only holds for a narrow α band, the report says so.

## 8. Seven Powers & the Platform Power Ratings

Helmer's own test is dual and binary: a power exists only where there is both a **Benefit** (material economic advantage) and a **Barrier** (the reason competitors cannot arbitrage it away). No published Helmer scoring template exists; ATLAS's contribution is a structured evidence protocol:

- **Per power, capture:** Benefit evidence, Barrier evidence, strength rating, trend (improving / stable / eroding), and a lifecycle plausibility flag — Helmer's Power Progression says powers are acquirable in specific windows (Origination: Cornered Resource, Counter-Positioning; Takeoff: Network Economies, Scale, Switching Costs; Stability: Branding, Process Power). A claimed power inconsistent with the firm's stage is challenged automatically.
- **Strength scale with falsifiable duration semantics:** None / Emerging / Established ("more likely than not to persist 5+ years") / Wide ("near-certain 5, likely 10+"). Duration language makes ratings testable in retrospect — the Morningstar moat discipline.
- **Committee sign-off:** any power rated Established or above, any triad rating above None, and any module rated Frontier requires Rating Committee approval with recorded rationale and dissent. Judgment disciplined by peer challenge, not formula.

The triad ratings (Economic / Perceived / Defence Value) are then derived as defined in §2, each with its own committee-approved rationale paragraph in the deliverable.

## 9. Assessor Certification & Calibration

- **Certification ladder (CMMI appraiser pattern):** Trained (coursework + rubric exam) → Shadow (participates in 2 assessments) → Observed Lead (leads one under review) → Certified Lead. High-stakes ratings (Frontier, Wide) require a Certified Lead plus committee.
- **Dual rating:** minimum two raters per module; consensus characterisation with documented dissent. Solo ratings are drafts, never deliverables.
- **Quarterly calibration:** all assessors rate 3–5 shared case vignettes; weighted kappa computed per anchor (target κ_w ≥ 0.75; Gwet's AC1 reported alongside while n is small). Anchors scoring κ < 0.6 are rewritten. Vignettes double as Practice Arena training content in the Workbench.

## 10. The Value Bridge (Latent Value, done honestly)

Score-points and currency never mix in one equation. The prototype's `LV = κ·Δq/(1+r) − cost` subtracted pounds from score-points and is retired. Scenario value is reported as a three-layer bridge:

| Layer | Content | Denomination |
|---|---|---|
| 1. Cost (hard) | Remediation/upgrade cost: effort × rate, vendor quotes, CAST-style sizing | Currency |
| 2. Cash-flow levers (evidenced) | Each upgrade mapped to named levers with client-supplied baselines: cost-to-serve (Stripe: ~42% of developer time on maintenance/debt), project drag (McKinsey: 10–20% surcharge from tech debt), incident/outage expected loss, capacity & time-to-market revenue enablement. Risk-adjusted NPV per lever under an explicit assumption register; staged programmes valued as compound real options where value is contingent. | Currency, with stated assumptions |
| 3. Strategic (qualitative) | Moat and durability implications in ordinal duration language ("more likely than not to sustain X for 5+ years"). Multiple-expansion claims are never made in currency. | Ordinal rating |

**Prioritisation** uses the score domain only: scenarios are evaluated by full re-scoring (ΔV from raising the chosen subcomponents), producing an **Upgrade Priority Index**. The index ranks; the bridge prices; the report keeps them side by side and never divides one by the other.

## 11. Validation Loop

- Every engagement logs predicted lever outcomes with horizons ("incident rate −30% within 18 months of the Back Office upgrade") in a prediction register.
- Clients are re-contacted at 12 and 24 months (retainer clients continuously); realised values are recorded and prediction hit-rates scored.
- Anonymised scores accumulate into the benchmark population (Crosslake TechIndicators model): from ~10 engagements, B normalisation and module benchmarks go peer-relative (Stage 2).
- **Pre-registered:** coefficients are re-fitted statistically only at n ≥ 30 engagements with outcome data (Stage 3). Until then, annual Delphi re-elicitation with drift tracking. The predicted-vs-realised record is published to clients once favourable — the methodology's long-term marketing asset.

## 12. Method Sources

SCAMPI MDD v1.3 (CMMI Institute); DOE C2M2 v2.1 and Self-Evaluation Guide; ISO/IEC 33020:2019; NIST CSF 2.0 (SP 1302); DORA capabilities research; UK Government Analysis Function MCDA guide; Parnell & Trainor swing-weight matrix; Saaty AHP (CR ≤ 0.10); Cooke's Classical Method; ISPOR structured expert elicitation task force; Morningstar Equity Research Methodology (Economic Moat, Uncertainty Rating); Helmer, *7 Powers* and the Power Progression; Parker, Van Alstyne & Choudary, *Platform Revolution*; Gawer & Cusumano; Bain/BCG/Crosslake/AKF technology due-diligence practice; McKinsey tech-debt research; Stripe Developer Coefficient; CAST technical-debt sizing; real-options valuation literature; Landis-Koch kappa conventions; Gwet's AC1.
