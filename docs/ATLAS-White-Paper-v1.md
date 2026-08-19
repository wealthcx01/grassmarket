# The ATLAS Platform Assessment Framework

**Bruntsfield Capital — Technical White Paper v1 — August 2026**

*Normative reference: `ATLAS-Methodology-v1.6.md`. Where this paper and the methodology disagree,
the methodology wins. Intended readers: a client's CTO, an acquirer's diligence team, a prospective
panel expert, and any advisor who will be asked "how does this actually work?" across a table.*

*This document supersedes `ATLAS-Methodology-Guide.md`, which is retired (see §12).*

---

## Abstract

ATLAS is a structured expert-judgment instrument for assessing platform businesses in
wealth-management and brokerage infrastructure. It combines a 51-item, 9-module infrastructure
maturity model (index **L**) with a normalised business-performance index (**B**) and an
operationalisation of Helmer's 7 Powers (**P**), aggregated into a composite Platform Value (**V**)
and interpreted through three ordinal Platform Power ratings.

Its distinguishing commitments are: declared, auditable rating semantics in the tradition of ISO/IEC
33020 and DOE C2M2; explicit provenance for every coefficient; quantitative uncertainty propagation
from evidence quality to output ranges; strict separation of the score domain from the currency
domain; and a pre-registered validation programme that upgrades the instrument's epistemic claims
only as evidence accumulates.

**This paper is written to be checkable.** Every claim about what the engine does is backed by a
named file or test. §10 states what is *not* yet proven, including the fact that most coefficients
in production today are provisional values that no expert panel has ratified. A white paper that
hid that would fail its own purpose.

---

## 1. Epistemic stance

### 1.1 The problem class

Assessments of technology estates for commercial decisions face a dual demand: they must be
*repeatable* (two competent assessors reach materially the same conclusion) and *decision-relevant*
(outputs connect to value, not merely to compliance). Established maturity frameworks (CMMI, C2M2)
achieve repeatability through written practice-level rubrics and rule-based roll-ups but stop short
of valuation; due-diligence practice connects findings to deal value but typically without a
published, versioned method. ATLAS occupies the intersection.

### 1.2 What kind of claim an ATLAS score is

An ATLAS score is a **structured, calibrated expert judgment**, not a statistical estimate. The
honesty architecture has three stages:

| Stage | Precondition | What the instrument may claim |
|---|---|---|
| **1 — current** | — | Coefficients carry documented provenance; outputs carry uncertainty ranges; currency claims are confined to a value bridge grounded in client-supplied baselines |
| **2** | ≥ ~10 engagements | Normalisation and module scores become peer-relative against the accumulated anonymised benchmark population |
| **3** | ≥ 30 engagements with outcomes | Statistical re-fitting of coefficients becomes admissible; predicted-versus-realised records become publishable evidence |

**We are in Stage 1, near its beginning.** The instrument never claims more than its stage licenses.

### 1.3 Measurement-theoretic position

Subcomponent ratings are **ordinal** judgments against behaviourally anchored rubric statements. The
numeric mapping (Basic 0.2, Developing 0.5, Advanced 0.8, Frontier 1.0) is an **index convention**,
not an interval-scale measurement.

Aggregates of ordinal indices are meaningful for *ranking and prioritisation* within the convention,
which is precisely how ATLAS uses them. Wherever a client-facing claim requires band-level meaning,
ATLAS switches to **rule-based ordinal logic** (§3.4), avoiding the classic abuse of treating rubric
arithmetic as measurement. This two-track design is the framework's answer to the ordinality
objection.

---

## 2. Notation

| Symbol | Meaning | Domain |
|---|---|---|
| m ∈ M | module (9 total) | registry keys |
| c ∈ C_m | subcomponent of module m (51 total) | registry keys |
| s_{m,c} | subcomponent rating index | {0.2, 0.5, 0.8, 1.0} |
| e_{m,c} | evidence grade | {E1, E2, E3, E4} |
| A_m ⊆ C_m | subcomponents applicable *and* assessed | — |
| λ_{m,c} | subcomponent loading | > 0 |
| α | breadth/bottleneck blend for modules | [0,1] |
| q_m | module quality (continuous) | [0.2, 1] |
| δ_m | module weight in L | > 0 |
| α_L | breadth/bottleneck blend for L | [0,1] |
| K ⊆ M | critical modules | registry |
| L | infrastructure index | [0.2, 1] |
| w_k, W_g | metric and group weights | > 0 |
| B | business index | [0.2, 1] |
| σ(·) | strength encoding (ADR-0004) | None 0.0 … Wide 1.0 |
| strength_j | power strength | σ(min(Benefit_j, Barrier_j)) |
| P | strategic power index | [0, 1] |
| C | customer-proposition index (ADR-0023) | [0.2, 1] |
| κ | critical-control cap floor (ADR-0038) | [0,1] or absent |
| θ | composite weights | Σθ = 1 |
| V | platform value composite | (0, 1] |

All keys are validated at load time against a single registry; an unrecognised or missing key is a
**refusal to score**. Coefficients without a provenance record do not load —
`CoefficientSet.validate_against`, exercised by
`tests/test_elicited_coefficients.py::test_dropping_any_provenance_family_refuses_construction`.

---

## 3. The model, formally

### 3.1 Module quality (continuous track)

For each module m with A_m ≠ ∅:

> q_m = α · ( Σ_{c∈A_m} λ_{m,c} s_{m,c} / Σ_{c∈A_m} λ_{m,c} ) + (1 − α) · min_{c∈A_m} s_{m,c}

The convex blend of a weighted mean and a minimum is an ordered weighted averaging (OWA) operator
with orness controlled by α. The mean term rewards breadth; the min term encodes the engineering
claim that *a module performs like its weakest part under load*. α = 1 recovers pure compensatory
averaging; α = 0 recovers strict weakest-link aggregation.

Not Applicable items are excluded with rationale and weights renormalise over A_m — scope exclusion,
not imputation. Not Assessed items are excluded from A_m entirely and handled by the gate and
uncertainty machinery, **never by a default value**.

### 3.2 Infrastructure index

> L = α_L · ( Σ_m δ_m q_m / Σ_m δ_m ) + (1 − α_L) · min_{m∈K} q_m

The same operator one level up, with the min over the critical set K.

### 3.3 Business index (group-weighted, ADR-0006)

> B = Σ_g W_g · B_g / Σ_g W_g,  where B_g = Σ_{k∈g} w_k n_k(x_k) / Σ_{k∈g} w_k

Metrics are partitioned into three groups — scale, unit economics, momentum — and averaged within
groups before group weights combine them. This responds to a real multicollinearity problem: scale
metrics (AUA, client count, revenue) are strongly correlated, and a flat weighted mean triple-counts
the same latent size factor. Group weighting is the standard hierarchical remedy. Every n_k declares
its unit, direction and anchors; units are captured, never inferred.

### 3.4 Module rating gate (headline track, ADR-0003)

The client-facing band is rule-based: **band_m = min( ceiling_m, floor_m )**.

**ceiling_m** — necessary conditions on critical subcomponents: Frontier requires all critical
Advanced+ at E3+; Advanced requires no critical Basic; a critical Not Assessed caps at Developing;
all-critical-Basic yields Basic.

**floor_m** — bottleneck over *all* assessed subcomponents: all Advanced+ permits Frontier; a
Developing minimum caps at Advanced; any Basic caps at Developing.

The two-sided rule makes the headline obey the same weakest-link principle as the continuous score
and prevents a module with a rotten non-critical part from earning the top band. An assessed
subcomponent without an evidence grade refuses to score rather than defaulting to E1.

### 3.5 Powers and the composite

> strength_j = σ( min(Benefit_j, Barrier_j) ),  P = Σ_j w_j strength_j / Σ_j w_j

> V = θ_B B + θ_P P + θ_L L   (three-index, Stage 1)

The min implements Helmer's conjunctive test — a power exists only where benefit *and* barrier both
exist — as an aggregation rule rather than a narrative aspiration. All seven powers are always in
scope: a structurally weak power scores a real low level, never N/A, keeping P's denominator fixed
at 7 and P comparable across firms.

**Range comparability (ADR-0005).** L and B have effective range [0.2, 1] while P has [0, 1]. ATLAS
does not rescale; instead θ is elicited by **swing weighting**, in which each weight prices the swing
from an index's worst to best value — so the elicitation internalises the differing ranges by
construction. Post-hoc rescaling would silently alter the meaning of elicited judgments.

### 3.6 The fourth index, and the cap

Two later amendments are implemented and **both are conditional by construction**, so the v1.1
golden master survives untouched:

- **C, the Customer-Proposition index (ADR-0023, Methodology v1.4).** When θ_C is present, V becomes
  a four-index composite with Σθ over all four = 1. A four-index V with θ_C absent is *impossible*:
  the engine never defaults θ_C to zero. A set carrying θ_C must also score C — you cannot weight a
  C you do not compute. **Today C is reported alongside V, never summed into it** (Stage 1).
- **The critical-control cap κ (ADR-0038).** When set, V is capped at κ + (1−κ)·min(q_m over
  critical modules) — a hard guardrail so a broken critical control cannot be out-weighted by a low
  θ_L. Absent ⇒ no cap. The cap only ever *lowers* V and is monotone in every subcomponent, so §4's
  properties hold.

### 3.7 The one-number rule (ADR-0040)

Every surface quotes the same deterministic composite. This exists because two different estimators
were once quoting two different scores for the same assessment. The rule extends to *displayed
precision*: a reader cannot distinguish rounding from disagreement, so V is shown at one decimal
everywhere.

---

## 4. Behavioural properties

Engineered into the model and enforced as executable property tests
(`tests/test_atlas_engine_properties.py`, 16 tests). Sketch arguments below; the suite is the
operative proof.

**P1 — Monotonicity.** Raising any s_{m,c} never decreases q_m, L, or V. Both terms of the OWA blend
are non-decreasing in each argument; composition with positive weights preserves the property. This
forbids "improving something made the score worse".

**P2 — Bottleneck dominance.** Raising the *minimum* subcomponent moves q_m at least as much as
raising any other by the same step, for any α < 1. This is the formal content of "fix the bottleneck
first".

**P3 — N/A invariance.** Marking a subcomponent Not Applicable and renormalising is equivalent to
evaluating on the reduced item set. Contrast zero-imputation, under which "not looked at" behaves as
"catastrophic" — the prototype's defect D9.

**P4 — Gate consistency.** band_m never exceeds either the critical ceiling or the overall floor; a
critical Not Assessed caps the band at Developing regardless of the continuous score.

**P5 — Conjunctive power scoring.** strength_j equals the weaker side exactly. A one-sided power
(Benefit Wide, Barrier None) scores None.

**P6 — Fixed-denominator comparability.** P aggregates over the same seven-element index set for
every firm, so cross-firm comparison is well-defined.

**P7 — Domain separation.** No computation combines a score-domain quantity with a currency-domain
quantity in one expression (ADR-0002), enforced structurally by an AST-level test over the codebase.

---

## 5. Uncertainty

Each rating's evidence grade parameterises an input distribution: E4 concentrates mass on the
assigned level; E1 spreads mass to adjacent levels. Monte Carlo over all inputs yields P10/P50/P90
ranges for q_m, L, B, P and V.

The methodological point: most maturity assessments *collect* confidence judgments and report point
scores anyway, implying precision they do not possess. ATLAS treats the confidence data as model
input — capturing uncertainty and then discarding it is worse than not capturing it at all.

**Not Assessed is excluded from the simulation, not imputed** (ADR-0034). A module with nothing
assessed yields `q_m = None`, never 0.0.

---

## 6. Coefficient provenance

Every non-client-input number carries a Weight Provenance Record: who, when, method, dispersion,
review date. The v1 protocol specifies a 4–8 expert panel; **swing weighting** as the primary method;
**AHP** as the consistency cross-check (CR ≤ 0.10); **two-round Delphi** for convergence;
**Cooke-style performance weighting** where disagreement persists.

**What is actually in production today is stated in §10.1, and it is not that.** The protocol above
is the design; the records now say which parts of it have been executed, which is none of them.

---

## 7. Reliability and validity programme

**Reliability.** Behaviourally anchored rubrics (204 anchors); a certification ladder (Trained →
Shadow → Observed Lead → Certified Lead); weighted κ machinery per anchor (target κ_w ≥ 0.75), with
Gwet's AC1 reported alongside while samples are small and ratings skewed. The implementations are
real and unit-tested (`src/grassmarket/workbench/calibration.py`). **They have produced no
measurements** — see §10.3.

**Content validity.** The 9×51 taxonomy derives from domain practice and is ratified through the
registry process; every subcomponent carries a declared description; anchors specify observable
evidence. Frontier is explicitly *not* the universal target, guarding against the maturity-model
failure of prescribing maximalism regardless of operating model.

**Construct validity.** B, P and L are deliberately separated constructs (achievement,
defensibility, capability) with distinct input sets; B's group structure controls indicator
collinearity; the conjunctive rule ties P to Helmer's construct definition rather than to a generic
"strategy score".

**Criterion validity.** Deferred honestly. The prediction register logs falsifiable lever-level
forecasts with horizons; 12/24-month follow-ups score hit-rates. Until then the framework claims
structured judgment, **not predictive power**.

**Governance — current mode (ADR-0041, Methodology v1.6).** A single named founder reviewer approves
every production assessment before finalisation, recorded against the **sha256 of the document as
approved**. Any edit after approval withdraws it by arithmetic rather than by state transition:
there is no path by which a document is released in a state the reviewer did not read. Only the
reviewer may approve — not the owning advisor, not an administrator.

Dual rating, the Rating Committee and calibration sessions are **specified, implemented and
dormant**. They are the intended mode when the network is large enough for genuine peer challenge;
in a group of this size they would produce a queue with the same few names in it. This is a recorded
decision, not an omission.

---

## 8. The value bridge

Score-domain outputs prioritise; currency-domain outputs price; the domains never mix in one
equation (ADR-0002). Scenario value is three layers: **cost** (hard currency from effort × rate or
vendor quotes); **cash-flow levers** (risk-adjusted NPV per named lever from *client-supplied*
baselines under an explicit assumption register); **strategic implications** (ordinal duration
language only).

The Upgrade Priority Index — ΔV from full re-scoring of the proposed scenario — ranks interventions;
the bridge prices them. The predecessor formula, which subtracted currency from score-points through
unvalidated sensitivities, is retired and structurally unreproducible in the engine.

---

## 9. Validation evidence

What exists today, with counts a reader can verify:

| Evidence | What it establishes | Where |
|---|---|---|
| **Golden master** | A full hand-computed assessment reproduces exactly: **V = 0.478565**, with every intermediate pinned — module bands, group means, L terms, B, P, the triad | `tests/test_atlas_engine_golden_master.py` |
| **Profile invariance** | The retail profile is byte-identical to the ungrouped original | `tests/test_profiles.py` |
| **Property suite** | P1–P7 above, as executable tests | `tests/test_atlas_engine_properties.py` (16) |
| **Coefficient/registry tests** | Unknown or missing keys refuse at load; every family carries provenance | `tests/test_coefficient_set.py` (13), `tests/test_elicited_coefficients.py` |
| **Monte Carlo** | Range machinery, Not-Assessed exclusion | `tests/test_atlas_montecarlo.py` (17) |
| **Dispersion analysis** | The engine is not compressing scores: fed extremes it produces extremes across **0.815** of the nominal range | `docs/analysis/score-dispersion-2026-07.md` |
| **Weight sensitivity** | Module ranking stable until λ moves **±110%**; worst V displacement **1.99 pts** at ±20%; firm ordering never changed in 160 runs | `docs/analysis/weight-sensitivity-2026-08.md` |
| **Whole suite** | **296 test functions** across 28 files touch the engine; **1,655** in the backend suite overall | `uv run pytest` |

**Every scoring run is immutable and versioned** — stored with its inputs, engine version,
methodology version, coefficient version and content hash. A historical score can always be
reproduced under the method that produced it.

---

## 10. Limitations register

Stated plainly, because a methodology that hides its limits invites the diligence findings it fears.

### 10.1 The coefficients in production are provisional — this is the most important limitation

| Profile | Set in production | Client-usable? | Who set the weights |
|---|---|---|---|
| **retail** (default) | `v1-draft-pending-elicitation` | **No** | Uniform placeholders |
| **wealth** | `wealth-v1-elicited-starter-2026` | Yes | Engineering starter values, research-validated, founder-activated 2026-07-20 (ADR-0037) |
| **exchange** | `exchange-v1-elicited-starter-2026` | Yes | As above |

Three consequences a reader should take seriously:

1. **No expert elicitation panel has met.** The 4–8 expert protocol in §6 is a design, not a
   history. Until 2026-08-19 the retail set's provenance records named
   `bruntsfield-elicitation-panel-2026` as the setter — a claim about evidence that does not exist.
   Those records now say what actually happened; the values are unchanged, because correcting a
   record and changing a number are different acts and only one of them was warranted.
2. **The default profile cannot produce a client deliverable at all.** Retail scores on uniform
   placeholder weights with `client_usable=False`, so the deliverable gate refuses it. This is the
   fail-loud design working as intended, but it means retail assessments are internal-only today.
3. **Two version strings still contain the word "elicited"** (`wealth-v1-elicited-starter-2026`,
   `exchange-v1-elicited-starter-2026`). They are **deliberately not renamed**: a coefficient version
   is stamped onto every immutable scoring run, and rewriting it would falsify the history of runs
   already recorded. The provenance record beside them is the authoritative statement.

Closing this is founder decision **D1** (`docs/FOUNDER-DECISIONS-2026-08.md`): run the elicitation,
or ratify the current values as a founder-directed interim with a scheduled panel.

### 10.2 Structural limitations

1. **Elicited weights are opinions with provenance, not estimates.** Mitigated by structured
   elicitation, dispersion reporting and stability intervals; residual risk is shared blind spots in
   a small panel from one professional community.
2. **Ordinal-index arithmetic.** The continuous track depends on the 0.2/0.5/0.8/1.0 convention; a
   different convention would reorder little but rescale much. Bands and rankings carry the
   client-facing weight.
3. **Small-n benchmarking.** Until Stage 2, "Strong/Weak" is anchored to rubric semantics, not to a
   peer distribution. Reports say so.
4. **Evidence-grade subjectivity.** E1–E4 is itself a judgment, mitigated by written definitions and
   the fail-loud rule that ungraded evidence refuses to score.
5. **AI-extraction risk (Path B).** Extracted inputs inherit transcription and mapping error;
   mitigated by per-field confidence and mandatory consultant review, with the invariant that
   confirmed extracted data scores identically to manual entry.

### 10.3 What has been built but never measured

The reliability programme in §7 is machinery without data: **zero calibration sessions have been
run, and no κ has ever been computed on real ratings.** The implementations are tested against
hand-computed fixtures, so they are known to be arithmetically correct and unknown to be useful.
Under ADR-0041 the peer-governance path is dormant, which means this gap will not close on its own —
it closes when the network is large enough to reinstate it.

Likewise the **prediction register has no resolved forecasts**, because no engagement has reached a
12-month horizon.

### 10.4 What this paper does not establish

That an ATLAS score is *correct*. Everything above establishes that the engine computes what the
methodology specifies, does so reproducibly, and is not unduly sensitive to its un-elicited weights.
Whether a high V predicts a better outcome is a Stage 3 question and the register is empty.

---

## 11. Closure roadmap

| Gap | What closes it | Gated on |
|---|---|---|
| Provisional coefficients (§10.1) | Run the 4–8 expert panel per §6, or ratify an interim | **D1** — founder |
| Retail not client-usable | Follows from D1 | **D1** |
| No κ measurements (§10.3) | Reinstate calibration when the network supports peer challenge | network size, ADR-0041 |
| No outcome evidence (§10.4) | 12/24-month follow-ups on the prediction register | time |
| Peer-relative normalisation | Stage 2 at ~10 engagements | engagement count |
| 7 Powers adaptation unratified | Helmer review (ADR-0046 is *Proposed*, not Accepted) | **D7** — founder |
| θ/α sensitivity beyond the variant grid | Extend the sweep to θ, α and κ | engineering |

---

## 12. Document map

| Document | Audience | Status |
|---|---|---|
| `ATLAS-Methodology-v1.6.md` | the engine | **Normative** |
| **This white paper** | external technical reader | Informative, current |
| `ATLAS-Scoring-Explained.md` | advisors | Informative |
| `Advisor-Guide-to-ATLAS.md` | advisors | Informative |
| `ATLAS-7Powers-Adaptation.md` | Helmer's office | Normative for the P derivation; ADR-0046 *Proposed* |
| `ATLAS-Methodology-Guide.md` | — | **RETIRED** — folded into this paper |

**On retiring the Guide (GRS-0237 scope 2).** The Guide was an informative companion pinned to
Methodology **v1.1**, and had drifted: it predated v1.4–v1.6, described the retired Rating Committee
as current governance, and did not mention C, the critical-control cap or the one-number rule. Its
audience was the same as this paper's.

The choice was to re-baseline it to v1.6 or fold it in. **Folded and retired**, because two
documents addressing one audience is two things to keep current and the Guide is the proof of what
happens when one of them slips. Its formal content survives here in §§2–8, corrected.

---

## 13. Versioning

The methodology is versioned and the engine records the methodology version on every scoring run.
Changes to rules or coefficients require an ADR and a version increment. Scoring runs are append-only
and content-hashed.

Note the v1.6 convention: because v1.6 changed no computation, a run stamped v1.6 is numerically
identical to the same document scored under v1.1. **The version tells you which approval regime
applied, not which arithmetic did.**

---

*References: SCAMPI MDD v1.3; DOE C2M2 v2.1; ISO/IEC 33020:2019; NIST CSF 2.0; DORA; UK Government
Analysis Function MCDA guidance; Parnell & Trainor; Saaty; Cooke; ISPOR task force; Morningstar
Equity Research Methodology; Helmer, 7 Powers; Parker, Van Alstyne & Choudary; Gawer & Cusumano;
Landis & Koch; Gwet.*
