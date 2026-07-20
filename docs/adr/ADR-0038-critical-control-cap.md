# ADR-0038 — Critical-control cap on V (operational-maturity guardrail)

- **Status:** Accepted (2026-07-20). Founder-directed after the GRS-0150 scored effect surfaced the θ_L tension.
- **Date:** 2026-07-20
- **Deciders:** Founder (product), engineering.
- **Normative source:** `docs/ATLAS-Methodology-v1.1.md` §5.1 (composite V), ADR-0002 (two-track scoring), ADR-0006 (weights in the CoefficientSet), non-negotiable #3 (fail loud) and #2 (scoring changes are ADRs, never silent).
- **Couples with:** ADR-0037 (segment elicitation — the θ_L trim that created the need), ADR-0034 (Not-Assessed exclusion — the cap follows the same D9 discipline).

## Context

The GRS-0150 research validation of the wealth & exchange starter weights recommended **lowering θ_L**
(wealth 0.40→0.25, exchange 0.40→0.33): for *enterprise value*, infrastructure is hygiene already
priced into B's cost/income, so a firm weak only on infra is worth almost as much. Correct for a
pricing lens — but the scored effect exposed the cost: a firm strong everywhere **except a critical
infrastructure control** (a CASS/custody failure for wealth, a clearing/settlement failure for an
exchange) scored **higher** under the trimmed θ_L (wealth 75.1→81.2, +6.1; exchange 79.2→81.7, +2.5).

That inverts the product's job. ATLAS is "Platform **Power**", and advisors use V to judge whether a
platform is **sound**, not to price an acquisition. A broken critical control is existential — it must
show in the headline, and it must not be out-weighted by a low θ_L. The critical-module gate + high
α_L already drag **L** down correctly; but with θ_L low, a low L barely moves V.

Two ways to reconcile: (a) keep θ_L high (reject the research), or (b) keep the research θ_L for the
*value* signal and add an explicit cap so a broken critical control ceilings V regardless of θ_L. We
take **(b)** — it keeps the moat/economics-lead-value evidence *and* the "a failed critical control
must show" product guarantee, without forcing one to pay for the other.

## Decision

Add an **optional** `critical_control_cap_floor` (κ ∈ [0,1]) to `CoefficientSet`. When present, after
the weighted V is formed the engine applies:

```
cap  = κ + (1 − κ) · min(q_m over critical-for-L modules)
V    = min(V_weighted, cap)
```

- **κ is the floor** the ceiling descends to when a critical control is fully broken. All critical
  controls Frontier ⇒ `min q_m = 1.0` ⇒ `cap = 1.0` (never binds). A fully-Basic critical module ⇒
  `min q_m = 0.2` ⇒ `cap = κ + 0.16` (≈0.6 at κ=0.5). The cap is **smooth and monotone** in the
  control's maturity — it is a guardrail, not a cliff.
- **The same critical-for-L module set** the L min-term uses. A fully-unassessed critical module is
  **excluded** (q_m None), exactly like ADR-0034 — the cap never descends on a control that was never
  looked at (D9). At least one critical must be assessed (the engine already raises otherwise).
- **The cap only ever LOWERS V** (`min`), never raises it, and is monotone in every subcomponent
  (raising a critical sub raises q_m raises the cap), so the §monotonicity property survives.
- It is **recorded, not silent**: the run carries a `CriticalControlCapResult` (floor, min critical
  q_m, cap, uncapped V, whether it bound, and the binding module) — reported even when it does not
  bind, so the guardrail is legible (non-negotiable #3, the AI-honesty ethos).
- **κ carries provenance** like any weight family (`critical_control_cap` provenance key), and a cap
  floor with no critical modules refuses to construct (fail-loud).

**Opt-in and fail-safe:** κ absent ⇒ no cap, V byte-identical. The retail golden master, the retail
elicited set, and every three-index set are **untouched**. The cap is set only on the two segment
starter sets (`elicited_{wealth,exchange}_coefficient_set`), at **κ = 0.5** — a broken critical
control caps V at ≈60/100. Those sets remain gated off (ADR-0022) until founder + panel ratify.

## Scored effect (κ = 0.5)

| Firm | Wealth: elicited (no cap → cap) | Exchange: elicited (no cap → cap) |
|---|---|---|
| Strong all-round | 96.3 → 96.3 (slack) | 100.0 → 100.0 (slack) |
| **Weak only on a critical control** | 81.2 → **60.0** (capped) | 81.7 → **60.0** (capped) |
| Weak everywhere | ~13 → ~13 (already below the cap) | ~8 → ~8 (already below) |

The anomaly is resolved: a broken CASS/clearing control now ceilings the score, while strong firms and
already-weak firms are unaffected.

## Consequences

- **Positive:** the research θ_L (value signal) and the product's soundness guarantee coexist. A
  critical-control failure can never be out-weighted. Fully recorded and legible.
- **Cost:** V is no longer a pure weighted sum for capped sets — it is `min(weighted, cap)`. This is a
  deliberate, provenanced non-linearity, documented here and stamped on the result. Methodology text
  updated to note the optional cap term (does not change §5 deterministic scores for un-capped sets).
- **κ is a governance parameter**, elicited and ratified with the rest of the segment weights
  (ADR-0037), not an engineering constant. 0.5 is the engineering starter pending that ratification.

## Alternatives considered

- **Keep θ_L high (reject the research).** Rejected: throws away the moat/economics-lead-value
  evidence and mis-prices strong-franchise firms that happen to run lean infra.
- **A hard band cap (e.g. any Basic critical ⇒ V ≤ 50).** Rejected: a cliff is not honest about
  partial weakness and interacts badly with the two-track headline; the smooth κ-blend expresses "how
  broken" proportionately.
- **Fold it into the gate bands only (headline word, not the number).** Rejected: the number is what
  ranks the pipeline and prices the value bridge; a broken critical must move the number too.
