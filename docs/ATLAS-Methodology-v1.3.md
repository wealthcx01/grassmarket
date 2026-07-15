# ATLAS Methodology v1.3

**Bruntsfield Capital — CONFIDENTIAL — July 2026**

The Bruntsfield Platform Power assessment method. This document is **normative** for the Grassmarket
scoring engine and **supersedes v1.2**. It adds a **fourth index — C (Customer Proposition)** — to
the composite. It **amends §2 (framework) and §5.1 (composite)** and adds **§13 (Customer
Proposition)**, restated in full below. The uncertainty machinery (§3.3, §7) is carried forward from
v1.2 and applies to C unchanged. **All other sections (§1, §4, §5.2–§5.4, §6, §8–§12) are unchanged
from v1.2/v1.1** and are incorporated by reference.

---

## 1.1 Changelog: v1.2 → v1.3

v1.3 ratifies the strategic addition proposed in `ATLAS Golden Master — Suggested Changes` §C1–C2:
ATLAS now scores the **customer proposition** (fees, safety, range/wrappers, execution, experience,
research) alongside the producer indices. This is the differentiator every commercial methodology
weights most heavily, and the unique product is B/P/L **connected to C**.

| Amendment | Section | ADR |
|---|---|---|
| Framework is now **four indices — B, P, L, C** — composing into V | §2 | ADR-0023 |
| Composite gains a **C term**: `V = θ_B·B + θ_P·P + θ_L·L + θ_C·C` | §5.1 | ADR-0023 |
| **C (Customer Proposition):** 6 modules, scored on the L machinery, with the 93-widget taxonomy as structured E4 evidence and dual-layer presence states | §13 (new) | ADR-0023 |

### Version-stamping convention (v1.3)

Unlike v1.2 (which touched only §7 uncertainty), **v1.3 changes §5.1 — the deterministic composite
moves**. Therefore:
- the **deterministic engine and CoefficientSet advance to the `1.3` stamp**, and a **golden-master
  v2** (Meridian + a customer-proposition profile) must be ratified before v1.3 scores are client-usable;
- the **v1.1 golden master remains valid for the three-index sub-result** (B/P/L and the pre-C V are
  byte-identical); v1.3 adds the C term on top rather than altering B/P/L;
- **C ships `draft-pending-ratification` behind a flag until θ_C and the C-internal weights are
  elicited** with provenance (§6) — exactly the gate B/P/L passed through. An engine that has no
  elicited `θ_C` MUST refuse to emit a client-usable four-index V (fail-loud, ADR-0001), not default
  `θ_C = 0`.

---

## 2. Framework & triad (amended)

ATLAS assesses a platform on **four indices**, each on a 0–1 scale, composed into **Platform Value (V)**:

- **B — Business.** Economic performance from 10 grouped metrics (§5.3).
- **P — Strategic Power.** Helmer's 7 Powers, Benefit/Barrier + evidence (§8).
- **L — Infrastructure.** 9 technology modules / 51 subcomponents, maturity-rated (§5.2).
- **C — Customer Proposition.** 6 customer-facing modules, maturity-rated with in-app widget evidence (§13).

The **client-facing interpretation** remains the **Platform Power triad** — Economic / Perceived /
Defence Value, ordinal (None → Emerging → Established → Wide), derived per §8. C **enriches** the
triad's Perceived-Value narrative (the customer surface is direct evidence of perceived value) but
does **not** change the triad's derivation, which stays Benefit/Barrier-based. The headline **bottleneck**
is now taken across **all assessed modules of L *and* C** — the single weakest module a client feels,
whether it is plumbing or proposition.

## 5.1 Composite (amended)

```
V = θ_B·B + θ_P·P + θ_L·L + θ_C·C,   with θ_B + θ_P + θ_L + θ_C = 1
```

- The four θ are **elicited together** (swing weighting, §6) so they sum to 1; the v1.1/v1.2 three-way
  θ (0.25 / 0.35 / 0.40) are **superseded** — they may not simply be reused with a bolted-on θ_C.
- **Index comparability (ADR-0005) extends to C:** C must be placed on the same effective range as
  B/P/L before composition (C is built on the maturity scale like L, so it shares L's range by
  construction). The composite is only client-usable once all four indices are on comparable ranges
  and all four θ carry provenance.
- If C is **not assessed** for an engagement (e.g. an infrastructure-only diligence), the run is a
  **three-index run** stamped `1.1`/`1.2`; it does not silently set C or θ_C to zero. Four-index and
  three-index runs are distinct, explicitly-versioned outputs.

## 13. Customer Proposition (C) — new

### 13.1 Purpose
C scores the surface a retail client actually experiences — cost, safety, range, execution,
experience, research — the dimension that carries 80–100% of the weight in every published
brokerage methodology and that ATLAS previously omitted.

### 13.2 Modules
Six modules (registry keys indicative), each rolling up to a module quality `q_c,m` and thence to C
**by the L aggregation path (§5.2)** — bottleneck-aware, with `NOT_APPLICABLE`/`NOT_ASSESSED`
renormalisation:

| Module | Focus |
|---|---|
| `CUST_COSTS_VALUE` | commissions, wrapper/platform fees, **FX fee**, spreads, cash-interest treatment, TCO bands |
| `CUST_SAFETY` | legal entity, FSCS/EU protection mapping, CASS/nominee disclosure, 2FA/biometrics, outage history |
| `CUST_RANGE_WRAPPERS` | asset classes, markets, fractional, funds/bonds/options, GIA/ISA/LISA/JISA/SIPP |
| `CUST_TRADING_EXECUTION` | order types, extended hours, margin, paper trading, execution-disclosure quality |
| `CUST_EXPERIENCE_SUPPORT` | onboarding time, taps-to-trade, UX rubric, notifications, timed support contacts |
| `CUST_RESEARCH_EDUCATION` | data latency, charting/screeners, third-party research, portfolio analytics & tax, education |

### 13.3 Rating & the widget taxonomy as evidence
- Each C subcomponent carries a **Basic→Frontier maturity level + E1–E4 evidence grade** (§3.3),
  identical in shape to L. **Scope is separated from execution:** a capability the firm deliberately
  does not offer is `NOT_APPLICABLE` and renormalises out — a focused app is not penalised for
  positioning.
- The **"World Cup" widget taxonomy** — **93 widgets × 15 categories**, each scored **Present / Ease-
  to-find / Usability / Depth (1–5)** with **Common/Uncommon/Rare** rarity — is the **structured E4
  evidence layer** for C (and corroborates L-FRONTEND). Its rarity-weighted, scope-adjusted roll-up
  **informs** the assessor's maturity rating of the relevant C subcomponents; it does not replace the
  maturity rating with a flat coverage-%. Canonical instrument: the March 2026 `_Claude` checklists.
- **Presence states (extends ADR-0001):** in addition to Present / `NOT_APPLICABLE` / `NOT_ASSESSED`,
  a capability may be **`PRESENT_PAYWALLED`** (exists but gated) or **`PRESENT_DEFECTIVE`** (exists but
  broken). These are first-class, never defaulted to Present.

### 13.4 Uncertainty & governance
C is modelled for uncertainty exactly as L (§7): each C-module and C carry P10/P50/P90 ranges and an
Assessment Uncertainty Rating. C ratings are subject to the same rubric anchors (§4), dual-rating
(§9), and rating-committee gates (§9) as L. **Frontier is not the target for C either** — each C
rubric anchor states which firm archetypes rationally need it.

---

## Sections unchanged from v1.2 / v1.1

§1 (Purpose & Status), §3.3 & §7 (Uncertainty — as amended in v1.2, applied to C), §4 (Rubric
Anchors — extended with C anchors, same template), §5.2 (L aggregation & gate — reused by C), §5.3
(group-weighted B), §5.4, §6 (Coefficient Provenance — now also θ_C and C weights), §8 (Seven Powers),
§9 (Certification & Calibration — applies to C ratings), §10 (Value Bridge — extends to C upgrades),
§11 (Validation Loop), §12 (Method Sources) are carried forward from `docs/ATLAS-Methodology-v1.2.md`
and `-v1.1.md`.
