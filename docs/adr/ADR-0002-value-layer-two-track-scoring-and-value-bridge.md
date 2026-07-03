# ADR-0002 — The value layer: two-track scoring and the three-layer value bridge

- **Status:** Accepted
- **Date:** 2026-07-03
- **Deciders:** Founder + engineering (Loop 0)
- **Normative source:** `docs/ATLAS-Methodology-v1.md` §5 (aggregation), §8 (powers & triad),
  §10 (the value bridge). Where this ADR and the Methodology disagree, the Methodology wins.
- **Supersedes:** the prototype's `LV = κ·Δq/(1+r) − cost` latent-value layer — feasibility
  defects **D2** and methodology gaps **§5.2, §5.3, §5.4**.

## Context

The prototype tried to express scenario value as a single currency number derived from a score
delta: `κ_m = θ_B·β_B·φ_m + …`, then `LV = κ·Δq/(1+r) − cost`, `ROI = LV/cost`, with module
LVs summed. This was wrong in four independent ways, each fatal on its own:

1. **Dimensional inconsistency** (gap §5.2): `κ·Δq` is score-points; `cost` is pounds. The
   subtraction `score_points − £` is meaningless. It looked like a valuation and was a
   category error.
2. **Fake NPV** (gap §5.3): `/(1+r)` is a single-period discount masquerading as a
   present-value calculation over a multi-year lever.
3. **Bottleneck contradiction** (gap §5.4): summing module-level LVs assumes additive,
   independent value, directly contradicting the `min`-term bottleneck aggregation used to
   compute the scores in the first place.
4. **Silent-zero wiring** (defect **D2**): the `module_effects` key mismatch made
   `φ = ψ = δ = 0`, so `κ_m = 0` and *every* scenario returned `LV = −cost`, `ROI < 0`.

The methodology's resolution is not to debug this formula but to delete it and separate the
two questions it conflated: **"which upgrade matters most?"** (a score-domain question) and
**"what is it worth?"** (a currency-and-qualitative question). This ADR ratifies that split
as an architectural boundary the code enforces.

## Decision

### 1. Two-track scoring (Methodology §5.1–§5.2)

Every module produces **two** outputs from the same inputs, answering two different questions:

- **Continuous track — `q_m`** (`[0,1]`): the blend
  `q_m = α · (Σ_c λ_{m,c}·s_{m,c} / Σ_c λ_{m,c}) + (1−α) · min_c s_{m,c}`. The weighted term
  rewards breadth; the `min` term is the bottleneck (a module performs like its weakest
  assessed part). Denominators include only **Applicable, Assessed** subcomponents. This track
  drives **prioritisation and benchmarking** — *how much*.
- **Headline track — the rating gate:** a rule-based band (C2M2 cumulative logic), *not* an
  arithmetic bucket of `q_m`. A module cannot be reported **Advanced** if any critical
  subcomponent is Basic, and cannot be **Frontier** unless all critical subcomponents are
  Advanced+ at evidence E3+. This track drives **the words on the page** — *which band*.

Scores never contradict ratings because they answer different questions. The same structure
lifts to `L` (blend of `q_m` with weights `δ`, critical-module `min` term), and `V = θ_B·B +
θ_P·P + θ_L·L` sits above with `Σθ = 1` enforced (ADR-0001).

The Powers triad (Economic / Perceived / Defence Value, §2, §8) is reported as an **ordinal
rating with falsifiable duration semantics** (None / Emerging / Established / Wide), never as a
decimal, and high ratings require committee sign-off. Ordinal in, ordinal out — no decimal
leaks into a triad figure.

### 2. The three-layer value bridge (Methodology §10) — currency and score never mix

Scenario value is reported as **three separated layers**, each in its own denomination. **No
equation in the codebase multiplies, divides, adds or subtracts a score-point and a currency
amount.** This is the invariant ADR-0002 exists to guarantee.

| Layer | Content | Denomination |
|---|---|---|
| **1. Cost (hard)** | Remediation/upgrade cost: effort × rate, vendor quotes, CAST-style sizing. | Currency `£` |
| **2. Cash-flow levers (evidenced)** | Each upgrade mapped to named levers (cost-to-serve, project drag, incident/outage expected loss, capacity & time-to-market enablement) with client-supplied baselines; risk-adjusted **NPV per lever** under an explicit **assumption register**; staged programmes as compound real options. | Currency `£`, with stated assumptions |
| **3. Strategic (qualitative)** | Moat & durability implications in ordinal duration language ("more likely than not to sustain X for 5+ years"). Multiple-expansion claims are **never** made in currency. | Ordinal rating |

### 3. Prioritisation lives in the score domain only (Methodology §10)

- Scenarios are evaluated by **full re-scoring**: raise the chosen subcomponents, recompute
  `V`, take `ΔV`. Module-level value is **never** summed — full re-scoring respects the
  bottleneck, unlike the prototype's additive `Σ LV_m`.
- `ΔV` produces an **Upgrade Priority Index** that *ranks* scenarios. The bridge *prices* them.
  The report keeps rank and price **side by side and never divides one by the other**. There
  is no `ROI = value/cost` that crosses the domains.

### 4. The boundary is enforced in types, not just prose

- Score-domain quantities (`q_m`, `B`, `P`, `L`, `V`, `ΔV`, Upgrade Priority Index) are typed
  as dimensionless `[0,1]` (or a rank) — a distinct contract type from currency.
- Currency quantities (cost, lever NPV) are a `Money` contract type carrying an explicit
  currency code and an attached assumption-register reference.
- Strategic quantities are the ordinal duration enum.
- There is **no constructor, operator, or function** in `bcap_contracts` or the engine that
  takes a score-domain value and a `Money` value and returns a number. The category error is
  unrepresentable, not merely discouraged.

## Consequences

- **Positive:** the dimensional inconsistency (gap §5.2) cannot recur because the types will
  not permit the arithmetic. The D2 silent-zero cannot recur because there is no `κ` to zero
  out — prioritisation is full re-scoring against the registry-validated coefficients. NPV is
  honest per-lever with an assumption register (gap §5.3). Bottleneck integrity holds because
  scenarios re-score rather than sum (gap §5.4).
- **Cost:** three artefacts where the prototype had one number. This is the honest cost of not
  fabricating a valuation. Clients get a cost, a set of assumption-tagged lever NPVs, and a
  qualitative moat statement — and can see exactly which is which.
- **Staging (Methodology §11):** currency levers are Stage-1 expert-assumption-driven now,
  benchmarked at ≥10 engagements, econometric at ≥30. The value bridge is honest at every
  stage precisely because it never claims the score *is* the money.
- **Scope note:** Loop 0 ships the *type boundary* (dimensionless score types vs `Money` type
  vs strategic ordinal, with no cross-domain operator) and this ADR. The re-scoring engine,
  Monte Carlo ranges, and the priced bridge are **Loop 1+**.

## Compliance tests

- No function signature in `bcap_contracts`/`atlas` accepts both a score type and `Money`
  (structural test + review).
- `Money` requires an explicit currency and an assumption-register reference to construct.
- Triad and strategic outputs are ordinal enums, not floats (type test).
- (Loop 1) Scenario `ΔV` comes from full re-scoring; no `Σ LV_m` path exists.
