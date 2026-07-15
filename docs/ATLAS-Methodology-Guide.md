# The ATLAS Assessment Framework: Methodological Foundations

**Bruntsfield Capital — Technical Guide — July 2026**

*Status: informative companion to `ATLAS-Methodology-v1.1.md`. The v1.1 specification is normative; this guide explains, formalises, and defends it. On any conflict, v1.1 wins. Intended readers: technical clients, due-diligence reviewers, prospective panel experts, and advisors pursuing Certified Lead status.*

---

## Abstract

ATLAS is a structured expert-judgment instrument for assessing platform businesses in wealth-management and brokerage infrastructure. It combines a 51-item, 9-module infrastructure maturity model (index **L**) with a normalised business-performance index (**B**) and an operationalisation of Helmer's 7 Powers (**P**), aggregated into a composite Platform Value (**V**) and interpreted through three ordinal Platform Power ratings (Economic, Perceived, Defence Value). The framework's distinguishing commitments are: (i) declared, auditable rating semantics in the tradition of ISO/IEC 33020 and DOE C2M2; (ii) explicit provenance for every coefficient, elicited by structured methods (swing weighting, AHP, Delphi) rather than asserted; (iii) quantitative uncertainty propagation from evidence quality to output ranges, which maturity models conventionally omit; (iv) strict separation of the score domain from the currency domain in valuing modernisation; and (v) a pre-registered validation programme that upgrades the instrument's epistemic claims only as evidence accumulates. This guide states the model formally, proves its key behavioural properties, positions each design choice against the methodological literature, and sets out the framework's reliability and validity programme, including its known limitations.

## 1. Motivation and Epistemic Stance

### 1.1 The problem class

Assessments of technology estates for commercial decisions face a dual demand: they must be *repeatable* (two competent assessors reach materially the same conclusion) and *decision-relevant* (outputs connect to value, not merely to compliance). Established maturity frameworks (CMMI, C2M2) achieve repeatability through written practice-level rubrics and rule-based roll-ups but stop short of valuation; due-diligence practice connects findings to deal value but typically without a published, versioned method. ATLAS occupies the intersection: a published method with maturity-model discipline whose outputs feed an explicitly separated valuation layer.

### 1.2 What kind of claim an ATLAS score is

An ATLAS score is a **structured, calibrated expert judgment**, not a statistical estimate. This is stated openly (v1.1 §1). The framework's honesty architecture has three stages, pre-registered in v1.1 §11:

- **Stage 1 (current):** coefficients are expert-elicited with documented provenance; outputs carry uncertainty ranges; currency claims are confined to a value bridge grounded in client-supplied baselines.
- **Stage 2 (≥ ~10 engagements):** normalisation and module scores become peer-relative against the accumulated anonymised benchmark population.
- **Stage 3 (≥ 30 engagements with outcomes):** statistical re-fitting of coefficients becomes admissible; predicted-versus-realised records become publishable evidence.

The instrument never claims more than its stage licenses. This staging follows the standard scientific posture for instruments that must operate before large-sample validation is possible (cf. structured expert judgment in health-economic modelling, ISPOR task force; Cooke's performance-weighted elicitation).

### 1.3 Measurement-theoretic position

Subcomponent ratings are **ordinal** judgments against behaviourally anchored rubric statements (BARS tradition). The numeric mapping (Basic 0.2, Developing 0.5, Advanced 0.8, Frontier 1.0) is an **index convention**, not an interval-scale measurement; v1.1 §3.1 states this explicitly. Aggregates of ordinal indices are meaningful for *ranking and prioritisation* within the convention, which is precisely how ATLAS uses them (the continuous track). Wherever a client-facing claim requires band-level meaning, ATLAS switches to **rule-based ordinal logic** (the rating gates, §3.4 below), avoiding the classic abuse of treating rubric arithmetic as measurement. This two-track design is the framework's answer to the ordinality objection.

## 2. Notation

| Symbol | Meaning | Domain |
|---|---|---|
| m ∈ M | module (9 total) | registry keys |
| c ∈ C_m | subcomponent of module m (51 total) | registry keys |
| s_{m,c} | subcomponent rating index | {0.2, 0.5, 0.8, 1.0} |
| e_{m,c} | evidence grade | {E1, E2, E3, E4} |
| A_m ⊆ C_m | subcomponents applicable *and* assessed | — |
| λ_{m,c} | subcomponent loading | elicited, > 0 |
| α | breadth/bottleneck blend for modules | elicited, [0,1] |
| q_m | module quality (continuous) | [0.2, 1] |
| δ_m | module weight in L | elicited, > 0 |
| α_L | breadth/bottleneck blend for L | elicited, [0,1] |
| K ⊆ M | critical modules | registry |
| L | infrastructure index | [0.2, 1] |
| g ∈ {scale, unit_economics, momentum} | metric group | — |
| n_k(·) | normalisation spec for metric k | → [0.2, 1] |
| w_k, W_g | metric and group weights | elicited, > 0 |
| B | business index | [0.2, 1] |
| Benefit_j, Barrier_j | per-power side ratings | {None, Emerging, Established, Wide} |
| σ(·) | strength encoding (ADR-0004) | None 0.0, Emerging 0.4, Established 0.7, Wide 1.0 |
| strength_j | power strength | σ(min(Benefit_j, Barrier_j)) |
| w_j | power weight | elicited, > 0 |
| P | strategic power index | [0, 1] |
| θ = (θ_B, θ_P, θ_L) | composite weights | elicited, Σθ = 1 |
| V | platform value composite | (0, 1] |

All keys (m, c, j, k) are validated at load time against a single registry; an unrecognised or missing key is a **refusal to score** (v1.1 §5.4). Coefficients without a provenance record do not load.

## 3. The Model, Formally

### 3.1 Module quality (continuous track)

For each module m with A_m ≠ ∅:

  q_m = α · ( Σ_{c∈A_m} λ_{m,c} s_{m,c} / Σ_{c∈A_m} λ_{m,c} ) + (1 − α) · min_{c∈A_m} s_{m,c}

The convex blend of a weighted mean and a minimum is an ordered weighted averaging (OWA)-family operator with orness controlled by α. The mean term rewards breadth; the min term encodes the engineering claim that *a module performs like its weakest part under load*. α = 1 recovers pure compensatory averaging; α = 0 recovers strict weakest-link aggregation (the C2M2/CMMI gate logic in continuous form). Not Applicable items are excluded with rationale and weights renormalise over A_m (scope-exclusion, not imputation); Not Assessed items are excluded from A_m and handled by the gate and uncertainty machinery, never by a default value.

### 3.2 Infrastructure index

  L = α_L · ( Σ_m δ_m q_m / Σ_m δ_m ) + (1 − α_L) · min_{m∈K} q_m

The same operator one level up, with the min taken over the elicited critical set K (draft: modules whose failure is an existential rather than experiential problem — back office, order management, connectivity).

### 3.3 Business index (group-weighted, ADR-0006)

  B = Σ_g W_g · B_g / Σ_g W_g,  where B_g = Σ_{k∈g} w_k n_k(x_k) / Σ_{k∈g} w_k

Metrics are partitioned into three groups — scale, unit economics, momentum — and averaged within groups before group weights combine them. The design responds to a multicollinearity problem in flat weighting: scale metrics (AUA, client count, revenue) are strongly correlated, and a flat weighted mean triple-counts the same latent size factor, swamping unit economics and momentum. Group-weighting is the standard hierarchical remedy (weight the constructs, not the correlated indicators). Every n_k declares its unit, direction, and anchor points in the metric register; units are captured in the UI and never inferred — the prototype's unit-sensitive heuristic is retired (feasibility defect D5).

### 3.4 Module rating gate (headline track, ADR-0003)

The client-facing band is rule-based:

  band_m = min( ceiling_m, floor_m )

**ceiling_m** (necessary conditions on critical subcomponents): Frontier requires all critical Advanced+ at evidence E3+; Advanced requires no critical Basic; a critical Not Assessed caps at Developing (an unexamined critical part is never presumed adequate); all-critical-Basic yields Basic; otherwise Developing.

**floor_m** (bottleneck over *all* assessed subcomponents): all Advanced+ permits Frontier; a Developing minimum caps at Advanced; any Basic caps at Developing; all Basic yields Basic.

The two-sided rule makes the headline obey the same weakest-link principle as the continuous score, guarantees "Basic" is reachable, and prevents a module with a rotten non-critical part from earning the top band. Evidence handling is fail-loud: an assessed subcomponent without an evidence grade refuses to score rather than defaulting to E1.

### 3.5 Powers and the composite

  strength_j = σ( min(Benefit_j, Barrier_j) ),  P = Σ_j w_j strength_j / Σ_j w_j,  V = θ_B B + θ_P P + θ_L L

The min operator implements Helmer's conjunctive test — a power exists only where benefit *and* barrier both exist — as an aggregation rule rather than a narrative aspiration (ADR-0007). All seven powers are always in scope: a structurally weak power scores a real low level, never N/A, keeping P's denominator fixed at 7 and P comparable across firms.

**Range comparability (ADR-0005).** L and B have effective range [0.2, 1] while P has [0, 1]. ATLAS does not rescale; instead θ is elicited by **swing weighting**, in which each weight prices the swing from the index's worst to best value — the elicitation therefore internalises the differing ranges by construction. This is the methodologically correct treatment (range-sensitive weights), whereas post-hoc rescaling would silently alter the meaning of elicited judgments.

### 3.6 The Platform Power triad

Economic, Perceived, and Defence Value are derived aggregates in [0,1] (v1.1 §2, §8): Economic from B's scale and unit-economics signal plus take-rate durability evidence; Perceived from the Benefit sides of Branding and Switching Costs plus retention/NPS/pricing-power inputs; Defence from the Barrier-side aggregate across all seven powers. Each is discretised to the nearest strength level under the ADR-0004 encoding using anchor-midpoint thresholds (Emerging ≥ 0.20, Established ≥ 0.55, Wide ≥ 0.85), and reported **only** as the ordinal rating with falsifiable duration language, each with a committee-approved rationale. The decimal never reaches the client.

## 4. Behavioural Properties

These properties are engineered into the model and enforced as executable property-based tests in the Grassmarket engine (the golden-master and property suite). Sketch arguments are given; the test suite is the operative proof.

**P1 — Monotonicity.** Raising any s_{m,c} (holding all else fixed) never decreases q_m, L, or V. *Sketch:* both terms of the OWA blend are non-decreasing in each argument; composition of non-decreasing maps with positive weights preserves the property; V is a positive combination of non-decreasing functions. This forbids the pathological "improving something made the score worse".

**P2 — Bottleneck dominance.** If c* = argmin s_{m,c}, then ∂q_m from raising s_{m,c*} by one level ≥ ∂q_m from raising any other subcomponent by the same step, for any α < 1 (strictly greater when the min is unique and loadings are equal). Fixing the weakest part is never a worse use of a level-step than polishing a strong one — the formal content of "fix the bottleneck first".

**P3 — N/A invariance.** Marking a subcomponent Not Applicable and renormalising is equivalent to evaluating the model on the reduced item set; it cannot raise or lower q_m by mere relabelling of an unassessed item (contrast with zero-imputation, under which the prototype's "not looked at" behaved as "catastrophic" — defect D9).

**P4 — Gate consistency.** band_m never exceeds either the critical ceiling or the overall floor; a module with any assessed Basic subcomponent is never Frontier; a critical Not Assessed caps the band at Developing regardless of the continuous score.

**P5 — Conjunctive power scoring.** strength_j is non-decreasing in each side and equals the weaker side exactly; a one-sided power (Benefit Wide, Barrier None) scores None. No amount of benefit compensates for the absence of a barrier, and vice versa.

**P6 — Fixed-denominator comparability.** P is invariant to which powers happen to be strong; two firms' P values aggregate over the same seven-element index set, so cross-firm comparison is well-defined.

**P7 — Domain separation.** No computation combines a score-domain quantity with a currency-domain quantity in one expression (ADR-0002; enforced structurally by an AST-level test over the codebase). Prioritisation is ΔV by full re-scoring; pricing is the value bridge; they meet only side-by-side on the page.

## 5. Uncertainty: From Evidence Quality to Output Ranges

Each rating's evidence grade parameterises an input distribution: E4 concentrates mass on the assigned level; E1 spreads mass to adjacent levels. Monte Carlo over all inputs yields P10/P50/P90 ranges for q_m, L, B, P, and V; headline numbers are always reported as ranges (v1.1 §7). Two second-order outputs accompany every report: a tornado ranking (which inputs move V most) and weight stability intervals (over what range each elicited weight can vary without changing the headline conclusion — the ISPOR-SMDM sensitivity-analysis norm). An ordinal Assessment Uncertainty Rating (Low/Medium/High/Very High), driven by evidence mix, coverage, and rater agreement, is printed beside every headline figure, following Morningstar's Uncertainty Rating discipline.

The methodological point: most maturity assessments *collect* confidence judgments and report point scores anyway, implying precision they do not possess. ATLAS treats the confidence data as model input — capturing uncertainty and then discarding it was classified as worse than not capturing it at all (feasibility review, §5.2).

## 6. Coefficient Provenance and Elicitation

Every non-client-input number (λ, δ, w, W_g, α, α_L, θ, the strength encoding, critical sets) carries a Weight Provenance Record: who, when, method, dispersion, review date. The v1 protocol (v1.1 §6): a 4–8 expert panel; **swing weighting** as the primary method (range-sensitive, the known corrective to naive importance voting); **AHP** pairwise comparison as the consistency cross-check (CR ≤ 0.10, geometric-mean group aggregation); **two-round Delphi** for convergence; **Cooke-style performance weighting** on calibration questions where disagreement persists. Draft coefficients shipped for engineering purposes are flagged `draft-pending-elicitation` and are not client-usable. Publication of the elicitation date and review date in every methods appendix makes the provenance claim checkable.

## 7. Reliability and Validity Programme

**Reliability (will two assessors agree?).** Instrumented, not assumed: behaviourally anchored rubrics (204 anchors, with misgrading notes updated from calibration data); mandatory dual rating with documented dissent; a CMMI-style certification ladder (Trained → Shadow → Observed Lead → Certified Lead); quarterly calibration on shared vignettes with weighted κ per anchor (target κ_w ≥ 0.75; Gwet's AC1 reported alongside while samples are small and ratings skewed); anchors below κ 0.6 are rewritten. Inter-rater reliability is thus a *measured, managed quantity* with a paper trail.

**Content validity.** The 9×51 taxonomy derives from domain practice in brokerage/wealth infrastructure and is ratified (not invented) through the registry process; every subcomponent carries a declared description; rubric anchors specify observable evidence. Frontier's "not the universal target" clause (DORA capability principle) guards against the maturity-model failure mode of prescribing maximalism regardless of operating model.

**Construct validity.** B, P, and L are deliberately separated constructs (achievement, defensibility, capability) with distinct input sets; the group structure of B controls indicator collinearity; the conjunctive power rule ties P to Helmer's construct definition rather than to a generic "strategy score". The triad ratings are derived views, not free-floating judgments — each is a function of recorded evidence.

**Criterion validity (does it predict anything?).** Deferred honestly: the prediction register logs falsifiable lever-level forecasts with horizons at every engagement; 12/24-month follow-ups score hit-rates (Brier-style for probabilistic claims); Stage 3 pre-registers coefficient re-fitting at n ≥ 30. Until then the framework claims structured judgment, not predictive power — and the duration semantics of every strength rating ("more likely than not to persist 5+ years") are written to be checkable in retrospect.

**Governance.** High-stakes ratings (any power Established+, any triad rating above None, any module Frontier) require Rating Committee approval with recorded rationale and dissent — Morningstar's moat-committee pattern: judgment disciplined by peer challenge rather than by formula.

## 8. The Value Bridge

Score-domain outputs prioritise; currency-domain outputs price; the domains never mix in one equation (ADR-0002). Scenario value is a three-layer bridge (v1.1 §10): (1) **cost**, hard currency from effort × rate or vendor quotes; (2) **cash-flow levers**, risk-adjusted NPV per named lever (cost-to-serve, project drag, incident expected loss, revenue enablement) computed from *client-supplied baselines* under an explicit assumption register, with staged programmes treated as compound real options where value is contingent; (3) **strategic implications**, stated only in ordinal duration language. The Upgrade Priority Index — ΔV from full re-scoring of the proposed scenario — ranks interventions; the bridge prices them. The predecessor formula (LV = κ·Δq/(1+r) − cost), which subtracted currency from score-points through unvalidated sensitivities, is retired and structurally unreproducible in the engine.

## 9. Threats to Validity and Known Limitations

Stated plainly, because a methodology that hides its limits invites the diligence findings it fears:

1. **Elicited weights are opinions with provenance, not estimates.** Mitigations: structured elicitation, dispersion reporting, stability intervals, pre-registered re-fitting. Residual risk: shared blind spots in a small panel drawn from one professional community.
2. **Ordinal-index arithmetic.** The continuous track's numbers depend on the 0.2/0.5/0.8/1.0 convention; a different convention would reorder little but rescale much. Mitigation: bands and rankings (which are convention-robust) carry the client-facing weight; decimals never appear without ranges.
3. **Small-n benchmarking.** Until Stage 2, "Strong/Weak" context is anchored to rubric semantics, not to a peer distribution. Mitigation: reports say so.
4. **Evidence-grade subjectivity.** E1–E4 is itself a judgment. Mitigation: written definitions, calibration sessions, and the fail-loud rule that ungraded evidence refuses to score.
5. **Path B extraction risk.** AI-extracted inputs from meetings inherit transcription and mapping error. Mitigation: per-field confidence, mandatory consultant review, and the invariant that confirmed Path B data scores identically to manual entry.
6. **Committee capture.** Peer challenge degrades if the committee is small and homogeneous. Mitigation: recorded dissent, quarterly κ reporting, external panel members as the network grows.

## 10. Relation to Prior Frameworks

| Framework | What ATLAS inherits | Where ATLAS departs |
|---|---|---|
| CMMI / SCAMPI | Practice-level characterisation; rule-based roll-up; appraiser certification ladder | Adds a continuous prioritisation track and value linkage |
| DOE C2M2 | Four-level scale semantics; scope exclusion; cumulative gate logic | Applies to commercial platform estates; adds uncertainty propagation |
| ISO/IEC 33020 | Declared rating semantics and documented measurement framework | Lighter-weight; single-firm scope |
| DORA | Capability-not-maturity stance; "top level is contextual" | Retains levels for repeatability, with the Frontier rationality clause |
| Morningstar moats | Ordinal ratings with falsifiable duration semantics; committee governance; uncertainty rating | Applies to private platform assessment; adds the infrastructure layer |
| Helmer, 7 Powers | Benefit ∧ Barrier test; Power Progression as plausibility filter | Adds a scored, evidence-captured protocol (no published Helmer template exists) |
| MCDA (swing/AHP/Delphi/Cooke) | Weight elicitation, consistency gates, performance weighting | Applied to an assessment instrument rather than a one-off decision |

## 11. Versioning and Change Control

The methodology is versioned; the engine records the methodology version in every scoring run. Changes to rules or coefficients require an ADR and a version increment — v1.1's changelog (six amendments, each ADR-referenced, zero coefficient changes) is the template. Scoring runs are append-only and content-hashed, so any historical score can be reproduced under the method that produced it. This is the audit property: an ATLAS number is never separable from the versioned method and evidence that generated it.

---

*References: see `ATLAS-Methodology-v1.1.md` §12 for the full source list (SCAMPI MDD v1.3; DOE C2M2 v2.1; ISO/IEC 33020:2019; NIST CSF 2.0; DORA; UK Government Analysis Function MCDA guidance; Parnell & Trainor; Saaty; Cooke; ISPOR task force; Morningstar Equity Research Methodology; Helmer; Parker, Van Alstyne & Choudary; Gawer & Cusumano; McKinsey tech-debt research; Stripe Developer Coefficient; CAST; Landis & Koch; Gwet).*
