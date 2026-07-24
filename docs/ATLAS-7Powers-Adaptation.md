---
title: ATLAS 7 Powers Adaptation
status: Draft for Hamilton Helmer's review (2026-07-24)
rights:
  grantor: Hamilton Helmer
  grantee: John Gallagher (Bruntsfield Advisory)
  date: 2026-07-23
  scope: The mathematics of the 7 Powers supplement, adapted for wealth platforms (wealth advisory
    firms, brokerages, and exchanges).
  condition: Hamilton Helmer reviews the output produced under the grant.
attribution: >-
  Adapted from Hamilton Helmer, 7 Powers: The Foundations of Business Strategy, with the author's
  permission.
sources:
  - data/reference/7powers-math-extraction.md (the mathematics extraction memo; the supplement PDF
    itself is not committed, per the grant)
adr: ADR-0046
ticket: GRS-0180
---

# ATLAS 7 Powers Adaptation

*Adapted from Hamilton Helmer, 7 Powers: The Foundations of Business Strategy, with the author's
permission.*

## How to read this document

This is the single normative source for all Powers content in ATLAS: the wizard's per-power
guidance, the Guide's Seven Powers section, Academy course material, and report language all derive
from here. Drift between those surfaces and this document is a defect, not a style choice.

Two kinds of text appear, and they are always distinguished:

- **Embedded (Helmer's mathematics).** Transcribed faithfully from the extraction memo, which was
  taken from the supplement page by page. Symbols are defined exactly as Helmer defines them. These
  passages are Helmer's work.
- **Adaptation (ours).** Introduced in the text with the word **Adaptation** or **ATLAS reading**.
  This is Bruntsfield's application of the mathematics to wealth platforms. Where we extend beyond
  Helmer, we say so, so that the review can tell his mathematics from our use of it.

**Verification note for the reviewer.** Every equation here was checked against
`data/reference/7powers-math-extraction.md`, which records that all 87 pages of the supplement were
read with no illegibility gaps. The supplement PDF is not committed to the repository (the grant
covers adapting the mathematics, not redistributing the file), so the memo is the reference of
record. Two precision points are carried forward for Helmer to confirm; they are collected in the
[Precision notes](#precision-notes-for-the-reviewer) at the end and flagged inline where they arise.

**Scoring is unchanged by this document (ADR-0046 §4).** ATLAS already scores each Power as
strength = min(Benefit, Barrier), which is faithful to Helmer's dual condition. This document does
not move the P computation and the golden master stays byte-identical. Any future quantitative use
of the Surplus Leader Margin formulas is a separate ADR and Methodology version, taken only after
this review.

The three wealth-platform segments referenced throughout are: **RB** = retail brokerage, **WA** =
wealth advisory, **EX** = exchange / market infrastructure.

---

## §1 The Fundamental Equation of Strategy

### 1.1 The equation (embedded)

Helmer begins from the standard net present value of free cash flow,

```
NPV = Σ ( CF_i / (1 + d)^i )
```

where `CF_i` is expected free cash flow in period *i* and `d` is the discount rate, and restates it
in a mathematically equivalent but more useful form, the **Fundamental Equation of Strategy**:

```
Value = M_0 · g · s̄ · m̄
```

- `M_0` — current market size.
- `g` — the discounted market growth factor.
- `s̄` — long-term (average) market share.
- `m̄` — long-term differential margin, meaning the net profit margin in excess of what is needed to
  cover the cost of capital.

This factors into two groups, which Helmer names:

```
NPV = Market Scale · Power
```

where **Market Scale** = `M_0 · g` (current market size times discounted growth) and **Power** =
`s̄ · m̄` (long-term share times long-term differential margin). Strategy, in Helmer's lower-case
sense, is defined against this equation as *"a route to continuing Power in significant markets."*

### 1.2 The derivation (embedded, condensed)

The extraction memo carries the full six-step derivation (memo §1.2, supplement pp.6–8). In outline:
starting from NPV with a terminal value, substituting net investment `I_i = K_i − K_{i−1}`,
telescoping the capital term, dropping the terminal term under a finite-life assumption, and
expressing profits through the rate of return `π_i = r · K_{i−1}` with differential return
`γ = r − c`, the NPV collapses to

```
NPV = K_0 · g · γ,   where   g = Σ_{i=1..n*} (1 + η)^{i+1} / (1 + c)^i
```

with `η` the top-line growth rate and `c` the cost of capital. Helmer then asserts the equivalence
`K_0 · γ = M_0 · s̄ · m̄` (both are first-period profits in excess of the cost of capital), giving
`NPV = M_0 · g · s̄ · m̄`. The derivation rests on five simplifying assumptions Helmer lists
explicitly: `n = n*`; constant market growth, market share, and differential returns over `n*`; and
a finite business life. (The `(1 + η)^{i+1}` exponent is transcribed as printed; see
[Precision note 1](#precision-notes-for-the-reviewer).)

### 1.3 Adaptation: the equation read for a wealth platform

**ATLAS reading.** ATLAS does not compute this equation; it uses it as the frame that separates
*how big the opportunity is* (Market Scale) from *how much of it a firm can durably keep* (Power).
The four symbols read, per segment, as:

| Symbol | Retail brokerage (RB) | Wealth advisory (WA) | Exchange / infrastructure (EX) |
|---|---|---|---|
| `M_0` current market size | Addressable retail trading and cash/margin balances | Addressable advised wealth in the segment | Addressable traded notional and market-data spend |
| `g` discounted growth | Retail participation and deposit growth | Wealth accumulation and household formation | Volume and data-consumption growth of the venue's markets |
| `s̄` long-term share | Funded-account and order-flow share | Advised-assets (AUA) share | Matched-volume / listings / data share |
| `m̄` differential margin | Net take per account above cost of capital | Advisory fee margin above cost of capital | Fee-and-data margin above cost of capital |

ATLAS's B (business), L (infrastructure), and C (customer proposition) lenses are **not** part of
this equation; they are Bruntsfield's own and are covered in §4.

---

## §2 The Seven Powers

Every power is placed on a single Benefit × Barrier grid, which is Helmer's operational definition
of the two terms. The rows (Benefit) split into **ΔCost** benefits (Input; Scale of
Production/Distribution; Production/Distribution Approach) and **ΔValue** benefits (Superior
Deliverables; Affective Valence; Uncertainty reduction; Benefits from Other Users). The columns
(Barrier to a challenger) run from *unwilling to challenge* to *unable to challenge*: Collateral
Damage, Share Gain Cost/Benefit, Hysteresis, Fiat, all under a standing annotation of *plus
uncertainty*.

Each power has exactly two **intensity determinants**: one **Industry Economics** determinant (how
big the prize can be in that industry) and one **Competitive Position** determinant (whether this
particular firm holds the leading position). Each also has an **establishment window** on Helmer's
Power Progression (Origination → Takeoff → Stability), which says *when* its Barrier can first be
erected.

For every power below: Helmer's definition, Benefit, and Barrier (embedded); the Surplus Leader
Margin formula with its symbols (embedded); the two intensity determinants and the window
(embedded); and then the **ATLAS reading** — one concrete example in each of RB, WA, and EX, and how
the determinants translate into ATLAS's Benefit and Barrier rating anchors (adaptation).

The Surplus Leader Margin (SLM) throughout answers Helmer's calibration question: *what governs the
profitability of the firm with Power (S) when prices are set so that a firm with no Power (W) makes
no profit at all?* S is the strong firm, W the weak firm.

### 2.1 Scale Economies

**Definition (embedded).** A business in which per-unit cost declines as volume increases over the
relevant range of output.

**Benefit:** reduced cost per unit (ΔCost). **Barrier:** *Share Gain Cost/Benefit* — a challenger
would have to gain share to match S's unit cost, and the cost of gaining that share is unattractive.

**Surplus Leader Margin (embedded, supplement p.15).** From a fixed cost `C`, variable cost `c`,
price `P`, and volumes `_sQ` (strong) and `_wQ` (weak), setting W to break even (`P = c + C/_wQ`)
gives

```
Surplus Leader Margin = [ C / (P · _sQ) ] · [ _sQ/_wQ − 1 ]
```

The first bracket, `C / (P · _sQ)`, is the **Industry Economics** term (the weight of the fixed
cost). The second, `_sQ/_wQ − 1`, is the **Competitive Position** term (relative share beyond
parity).

**Intensity determinants (embedded).** Industry Economics: scale-economy intensity (how steeply
unit cost falls with volume). Competitive Position: relative scale (S's scale versus the largest
competitor). **Window:** Takeoff.

**ATLAS reading (adaptation).**
- **RB:** the technology, clearing, and compliance platform is a large fixed base spread over trade
  and account volume, so a discount broker's per-trade cost falls sharply with order flow — high
  intensity. Rate the Benefit toward Wide where the fixed platform and regulatory cost is a large
  share of revenue and the firm has leading order-flow scale.
- **WA:** advice is more people-variable, so the scale economy is moderate; the fixed cost is
  planning tooling, research, and compliance overhead per adviser. Rate Established only when a
  shared research, planning, and technology stack is amortised across many advisers.
- **EX:** the matching engine, surveillance, and connectivity are almost pure fixed cost with a
  marginal cost per additional message near zero — very high intensity, and usually a genuine Power.
- **Determinant → anchor mapping.** Industry Economics (scale-economy intensity) sets the **Benefit**
  magnitude anchors. Competitive Position (the ratio `_sQ/_wQ` of this firm's volume to the largest
  rival's) sets the **Barrier** anchors.

### 2.2 Network Economies

**Definition (embedded).** A business in which the value delivered to each customer increases as the
installed base of users grows.

**Benefit:** value to the customer rises with the installed base (Benefits from Other Users,
ΔValue). **Barrier:** *Share Gain Cost/Benefit* — a challenger cannot match S's value without
matching S's installed base, which is prohibitively costly to build.

**Surplus Leader Margin (embedded, supplement p.19).** With installed bases `_sN`, `_wN`, marginal
benefit per additional user `δ`, and variable cost `c`, setting W to break even gives

```
Surplus Leader Margin = 1 − 1 / [ (δ/c) · (_sN − _wN) + 1 ]
```

Industry Economics term: `δ/c` (value added per additional user per dollar of variable cost).
Competitive Position term: `_sN − _wN` (the **absolute** difference in installed base — Helmer is
explicit that it is the gap, not the ratio). If `_sN = _wN` the SLM is 0; as `_sN` far exceeds `_wN`
it approaches 100%.

**Intensity determinants (embedded).** Industry Economics: network-effect intensity (`δ/c`).
Competitive Position: absolute difference in installed base. **Window:** Takeoff.

**ATLAS reading (adaptation).**
- **RB:** direct network effects are weak to moderate — a brokerage account is not more valuable
  because others hold one. Rate None or Emerging for a plain broker, Emerging where a social or
  copy-trading layer or a fractional-share liquidity feature creates a real cross-user benefit.
- **WA:** advice is bilateral, so the direct network effect is generally low; an indirect effect can
  exist through a genuine two-sided marketplace of third-party managers or products. Rate None
  unless such a marketplace exists.
- **EX:** the archetypal strong network effect — liquidity begets liquidity, and each additional
  order improves fills for all. This is usually an exchange's dominant Power; rate toward Wide where
  the liquidity lead `_sN − _wN` is large and self-reinforcing.
- **Determinant → anchor mapping.** Network-effect intensity sets the **Benefit** anchors; the
  absolute installed-base gap sets the **Barrier** anchors.

### 2.3 Counter-Positioning

**Definition (embedded).** A newcomer (here S is the challenger, W the incumbent) adopts a new,
superior business model that the incumbent does not copy because doing so would damage its existing
business.

**Benefit:** a superior new business model — lower cost and/or superior deliverables. **Barrier:**
*Collateral Damage* — the incumbent is **unwilling** to adopt the new model because entering it
would inflict loss on its existing (Old) business.

**Surplus Leader Margin (embedded, supplement pp.27–28).** With the incumbent's Old-business margin
`^Om`, the Old-to-New price ratio `^OP/^NP` (greater than 1, since the new model is cheaper), and
the induced cannibalization ratio `δ = −Δ^OQ / ^NQ`,

```
SLM = ^Om · ( ^OP / ^NP ) · δ
```

Helmer's structural points: if the incumbent loses no Old volume (`δ = 0`) there is no
Counter-Positioning; the higher the incumbent's margin `^Om`, the higher the SLM (an entrenched,
highly profitable incumbent is *more* vulnerable); and the three incumbent failure modes are Milk
(rational), History's Slave (cognitive), and Job Security (agency). Over time `δ` tends to fall,
SLM declines, and the incumbent eventually reaches a capitulation point.

**Intensity determinants (embedded).** Industry Economics: new-model superiority plus collateral
damage to the old (the magnitude of `^Om · (^OP/^NP) · δ`). Competitive Position: binary — the
entrant holds the new model, the incumbent the old. **Window:** Origination.

**ATLAS reading (adaptation).**
- **RB:** the zero-commission / payment-for-order-flow model counter-positioned against
  full-commission incumbents who are unwilling to zero out their commission line. A strong example;
  rate the challenger Established or Wide during Origination.
- **WA:** the flat-fee fiduciary RIA model counter-positioned against commission-and-trailer
  incumbents, whose high-margin trailer book is exactly the collateral damage that deters imitation.
- **EX:** an all-to-all or exchange-cleared model counter-positioned against incumbent dealer or OTC
  intermediation whose spread income would be cannibalised; rate by how much dealer margin the
  incumbent must destroy to match.
- **Determinant → anchor mapping.** The magnitude of the new-model advantage and collateral damage
  sets the **Benefit** anchors. Because the Competitive Position determinant is binary, the
  **Barrier** anchor is closer to present-or-absent plus the durability of the incumbent's
  unwillingness (the trend in `δ`), not a smooth scale.

### 2.4 Switching Costs

**Definition (embedded).** The value a customer loses by switching supplier for a subsequent
purchase, which lets the firm that already holds the customer (S) charge a premium.

**Benefit:** a premium on follow-on products (ΔValue). **Barrier:** *Share Gain Cost/Benefit* — a
challenger must compensate the customer for the switching cost to win the sale, which is
unattractive.

**Surplus Leader Margin (embedded, supplement p.37).** With switching cost per unit `Δ`, setting the
firm without the customer (W) to break even gives, per unit of revenue,

```
SLM = Δ
```

Industry Economics term: `Δ` (the magnitude of the switching cost). Competitive Position term:
`_sQ` (the number of current customers S already holds).

**Intensity determinants (embedded).** Industry Economics: magnitude of switching costs.
Competitive Position: number of current customers. **Window:** Takeoff.

**ATLAS reading (adaptation).**
- **RB:** account-transfer friction — ACATS delays, tax-lot re-basing, re-linking direct deposits
  and bill-pay, learning a new app — is a moderate `Δ`, higher where tax-lot history and margin or
  options approvals are embedded. Rate Established where re-papering and tax friction are real.
- **WA:** `Δ` is high — moving an advisory relationship means re-onboarding, redoing financial
  plans, re-establishing trust, possible tax realization, and losing the relationship manager. This
  is often the dominant Power for advisory; rate toward Wide for multi-account households with
  embedded plans and held-away integrations.
- **EX:** the switching cost sits with members and vendors — recoded FIX connections, re-certified
  gateways, colocation, back-office mappings, and best-execution retooling — so `Δ` per connected
  participant is high.
- **Determinant → anchor mapping.** Switching-cost magnitude sets the **Benefit** anchors; the count
  of current customers or connections held sets the **Barrier** anchors.

### 2.5 Branding

**Definition (embedded).** The durable attribution of higher value to an objectively identical
offering, arising from the historical information the buyer holds. It delivers value through
affective valence (feeling and identity) and uncertainty reduction (confidence in quality).

**Benefit:** a price premium (ΔValue). **Barrier:** *Hysteresis* — brand strength builds only slowly,
so a challenger cannot replicate it quickly at any price.

**Surplus Leader Margin (embedded, supplement pp.44–45).** The branding price multiple `B(t)`, which
is the ratio of the strong firm's price to the weak firm's price, is

```
B(t) = [ Z / ( 1 + (Z − 1) · e^(−F·t) ) ] · D_t · U_t
```

- `Z` — the maximum potential branding multiple for the good type, `Z > 2`.
- `F` — the brand cycle-time compression factor, `F > 0` (larger `F` gives a steeper, shorter brand
  cycle; smaller `F` a shallower, longer one).
- `D_t` — brand dilution at time *t*, `0 ≤ D ≤ 1` (`D = 1` is no dilution).
- `U_t` — brand underinvestment at time *t*, `0 ≤ U ≤ 1` (`U = 1` is no underinvestment).
- `t` — time; how long S has been building brand versus a challenger starting at `t = 0`.

The logistic is chosen so `B(0) = 1`. The Surplus Leader Margin is then

```
SLM = 1 − 1 / B(t)
```

`B()` (through `Z` and `F`) is the Industry Economics term — the magnitude and sustainability of the
leverage — and `t` is the Competitive Position term. The coefficient is `(Z − 1)`; the supplement
prints it lowercase, which is resolved in [Precision note 2](#precision-notes-for-the-reviewer).

**Intensity determinants (embedded).** Industry Economics: the time constant and potential magnitude
of the branding effect (`F` and `Z`). Competitive Position: duration of brand investing (`t`).
**Window:** Stability.

**ATLAS reading (adaptation).**
- **RB:** brand as a safety and trust signal (custody of my money) — a moderate-to-high `Z` for a
  century-old name, showing up as lower acquisition cost and stickier deposits rather than headline
  fees. Rate Established for heritage custodians.
- **WA:** a very high `Z` — advisory is an uncertainty-and-affective-valence purchase (private-bank
  cachet, "trusted with my family's wealth") with a long build (small `F`, so highly sustainable).
  Rate toward Wide for a multi-generational private-bank brand commanding a fee premium peers cannot
  match.
- **EX:** brand as integrity and reference-price authority (the official price, index and benchmark
  trust), showing up as listings prestige and a data-licensing premium. Rate Established where the
  venue is the reference market.
- **Determinant → anchor mapping.** `Z` and `F` (how large the trust premium can be and how slowly
  it builds) set the **Benefit** anchors; the duration `t` of consistent, non-diluted,
  non-underinvested brand building (`D ≈ U ≈ 1`) sets the **Barrier** anchors.

### 2.6 Cornered Resource

**Definition (embedded).** Preferential access, on attractive terms, to a coveted resource that
independently produces a superior outcome (Helmer's example is Pixar's core creative group).

**Benefit:** the resource yields a price premium or a cost reduction, both captured as a single
per-unit profit increment `Δ` (in the grid, Cornered Resource spans both ΔCost and ΔValue).
**Barrier:** *Fiat* — S controls the resource by contract, ownership, or exclusive relationship, and
the challenger simply cannot obtain it.

**Surplus Leader Margin (embedded, supplement pp.53–54).** With per-unit profit increment `Δ`, an
incremental fixed cost `k` of holding the resource, strong-firm volume `_sQ`, and the weak price
`_wP`,

```
SLM = Δ / (Δ + _wP)  −  k / [ (Δ + _wP) · _sQ ]
    = [ margin increase from the resource ]  −  [ resource cost per dollar of sales ]
```

Industry Economics term: `Δ` and `k`. Competitive Position term: control of the resource by fiat
(binary).

**Intensity determinants (embedded).** Industry Economics: the price and/or cost increment due to
the resource (`Δ`, net of `k`). Competitive Position: preferred access at a non-arbitraging price
(fiat control). **Window:** Origination.

**ATLAS reading (adaptation).**
- **RB:** exclusive order-flow or data feeds, or a captive distribution channel (an employer-plan or
  banking-app funnel) delivering cheaper acquisition; rate by the acquisition-cost or spread
  advantage net of the cost `k` to keep the arrangement.
- **WA:** a cornered talent group (a star chief investment officer or team) or exclusive access to a
  scarce product (sole distribution of a coveted fund or allocation); `Δ` is the fee or retention
  premium the talent or product commands and `k` the extra compensation to retain it — directly
  Helmer's Pixar analogy.
- **EX:** exclusive rights — a proprietary index or benchmark, a regulatory licence or monopoly on a
  contract, or sole listing rights; `Δ` is the licensing or listing rent and the barrier is pure
  fiat.
- **Determinant → anchor mapping.** The increment `Δ` (net of `k`) sets the **Benefit** anchors. The
  Competitive Position determinant is binary, so the **Barrier** anchor asks whether access is
  legally or contractually locked (Wide) or merely favourable (Emerging).

### 2.7 Process Power

**Definition (embedded).** Embedded company organisation and activity sets that enable lower costs
and/or a superior product, and which can be matched only by an extended commitment (the experience
curve, with the Toyota Production System as the archetype).

**Benefit:** lower cost and/or superior deliverables from the accumulated process. **Barrier:**
*Hysteresis* — process advancement accrues only slowly and sequentially, so a challenger cannot
catch up quickly even when the process is visible.

**Surplus Leader Margin (embedded, supplement p.60).** With `D(t)` the weak firm's cost expressed as
a multiple of the strong firm's cost,

```
SLM = 1 − 1 / D(t),   with   D(t) = Z / ( 1 + (Z − 1) · e^(−F·t) )
```

This is the exact structural twin of the Branding SLM, with the same logistic and the same
`D(0) = B(0) = 1` normalisation. `D()` (via `Z`, `F`) is the Industry Economics term and `t` is the
Competitive Position term.

**Intensity determinants (embedded).** Industry Economics: the time constant and potential magnitude
of the process effect (`F` and `Z`). Competitive Position: the relative duration of process advances
(`t`). **Window:** Stability.

**ATLAS reading (adaptation).**
- **RB:** straight-through processing, automated onboarding, and risk-and-margin engines refined
  over many release cycles and hard to copy quickly; rate Established where per-account operating
  cost is structurally below peers through accumulated automation.
- **WA:** a proprietary, deeply embedded advice-and-servicing operating model (planning workflows,
  compliance automation, next-best-action) that raises adviser productivity and is matched only by
  years of iteration; rate by relative cost-to-serve per household.
- **EX:** ultra-low-latency matching, surveillance, and resilience engineering accumulated over
  years; rate toward Wide for a venue whose latency, throughput, and uptime advantage a rival cannot
  replicate within a short horizon.
- **Determinant → anchor mapping.** `Z` and `F` set the **Benefit** anchors; the lead time `t` of
  accumulated process advancement over the nearest challenger sets the **Barrier** anchors.

### 2.8 Consolidated tables (embedded)

**Surplus Leader Margin formulas.**

| Power | SLM | Industry Economics term | Competitive Position term |
|---|---|---|---|
| Scale Economies | `[C/(P·_sQ)] · [_sQ/_wQ − 1]` | `C/(P·_sQ)` | `_sQ/_wQ − 1` |
| Network Economies | `1 − 1/[(δ/c)(_sN − _wN) + 1]` | `δ/c` | `_sN − _wN` |
| Counter-Positioning | `^Om · (^OP/^NP) · δ` | `^Om · (^OP/^NP)` | `δ` (binary who-holds) |
| Switching Costs | `Δ` | `Δ` | `_sQ` |
| Branding | `1 − 1/B(t)`, `B(t) = Z/(1+(Z−1)e^{−Ft}) · D_t · U_t` | `Z, F` (via `B`) | `t` |
| Cornered Resource | `Δ/(Δ+_wP) − k/[(Δ+_wP)·_sQ]` | `Δ, k` | fiat control (binary) |
| Process Power | `1 − 1/D(t)`, `D(t) = Z/(1+(Z−1)e^{−Ft})` | `Z, F` (via `D`) | `t` |

**Intensity determinants and windows.**

| Power | Industry Economics determinant | Competitive Position determinant | Window |
|---|---|---|---|
| Scale Economies | Scale-economy intensity | Relative scale | Takeoff |
| Network Economies | Network-effect intensity | Absolute installed-base difference | Takeoff |
| Counter-Positioning | New-model superiority + collateral damage | Binary (new vs old model) | Origination |
| Switching Costs | Magnitude of switching costs | Number of current customers | Takeoff |
| Branding | Time constant + magnitude (`F`, `Z`) | Duration of brand investing (`t`) | Stability |
| Cornered Resource | Increment due to resource (`Δ`, `k`) | Preferred access by fiat | Origination |
| Process Power | Time constant + magnitude (`F`, `Z`) | Relative duration of advances (`t`) | Stability |

---

## §3 Power Dynamics and the ATLAS assessment moments

Helmer's Power Progression places every business on an **Origination → Takeoff → Stability** S-curve,
where the break between Takeoff and Stability is roughly when unit growth falls below 30–40% per
year. Each Power has an establishment window on this curve, the interval in which its Barrier can
first be erected: Cornered Resource and Counter-Positioning originate early; Scale, Network, and
Switching in Takeoff; Branding and Process in Stability. At most three *new* Powers are ever in play
at a given stage. (This is a business-stage framework, distinct from the product life cycle.)

**Adaptation: mapping the progression to the ATLAS assessment moments.**

- **Prospect / qualification.** The firm's stage on the progression tells the adviser which Powers
  are even available to assess. It is a mistake to mark a Branding or Process Power as a gap for an
  Origination-stage challenger whose window for them has not opened, or to expect a mature exchange
  to still be originating a Counter-Positioning wedge.
- **Assessment.** ATLAS rates the Powers whose windows are open for the firm's stage. Where a
  window is not yet open, the Power is left unrated rather than scored low, which keeps it distinct
  from a genuine weakness (the first-class *not assessed* state, never a zero).
- **Roadmap.** The progression orders which Powers a firm should be *building next*: an early-stage
  platform layers Cornered Resource and Counter-Positioning first; a scaling one turns to Scale,
  Network, and Switching; a mature one consolidates Branding and Process. The roadmap's sequencing
  follows the windows, so the advice matches the firm's stage.

This mapping is an ATLAS application of Helmer's progression; the progression itself is his.

---

## §4 The ATLAS correspondence table

| Supplement concept | ATLAS concept | Relationship |
|---|---|---|
| Power = Benefit **and** Barrier (glossary) | Power strength = **min(Benefit, Barrier)** | Faithful. `min()` encodes the dual condition exactly: a strong Benefit with no Barrier is arbitraged away, a Barrier around no Benefit protects nothing. |
| Benefit (Superior + Significant, in the 3 S's) | Per-power **Benefit rating** {None, Emerging, Established, Wide} | Faithful in structure; ATLAS renders it ordinal. |
| Barrier (Sustainable, in the 3 S's) | Per-power **Barrier rating** {None, Emerging, Established, Wide} | Faithful in structure; ATLAS renders it ordinal. |
| Industry Economics determinant | The **Benefit** magnitude anchors | Adaptation: ATLAS routes the industry-economics evidence to the Benefit sub-rating. |
| Competitive Position determinant | The **Barrier / relative** anchors | Adaptation: ATLAS routes the competitive-position evidence to the Barrier sub-rating. |
| Power Progression windows | Power **availability** by firm stage | Adaptation: ATLAS gates which Powers it rates by the open window. |
| Surplus Leader Margin | (not used to price a Power today) | ATLAS rates ordinally and does not compute the SLM. Any future SLM-informed input is a separate ADR and Methodology version (ADR-0046 §4). |
| Fundamental Equation `M_0·g·s̄·m̄` | The framing of Market Scale vs Power | Adaptation: used as narrative framing, not computed. |
| — | **B** (business metrics), **L** (infrastructure), **C** (customer proposition) | **Ours, with no Helmer analogue.** These lenses are Bruntsfield's and must never be presented as part of the 7 Powers mathematics. |

**P scoring is unchanged by this document.** The P computation — strength = min(Benefit, Barrier),
combined as a weighted mean per Methodology §5.4 — already implements Helmer's dual condition and is
not moved here. The golden master remains byte-identical (ADR-0046 §4).

Three cross-cutting rules follow from the mapping, and ATLAS already honours them:

- Keep the Benefit and Barrier ratings independent and take the minimum; never average them.
- Route industry-economics evidence to the Benefit rating and competitive-position evidence to the
  Barrier rating.
- Counter-Positioning and Cornered Resource have binary competitive-position determinants, so their
  Barrier ratings read closer to present-or-absent plus durability; the other five have continuous
  determinants (a ratio, gap, count, or time) that map naturally onto the four-point scale.

---

## Precision notes for the reviewer

Two points are carried forward from the extraction memo (§5) for Hamilton Helmer to confirm. Neither
affects the collapsed results used above; both are flagged because they concern a symbol shown to the
author.

1. **The `(1 + η)^{i+1}` exponent (supplement p.7).** In the derivation's Step 4, the capital growth
   substitution is transcribed as printed, `K_0 (1 + η)^{i+1}`. Dimensionally one might expect
   `(1 + η)^{i−1}` from "capital at the end of period *i−1*"; the printed `i+1` reflects Helmer's own
   indexing and timing convention and is immaterial to the collapsed form `NPV = K_0 · g · γ`.
   Transcribed as printed, flagged for confirmation of the convention.

2. **The Branding coefficient `(Z − 1)` (supplement p.44).** The Branding logistic prints its
   coefficient lowercase, `(z − 1)`, while the ceiling parameter is uppercase `Z`. It is read as
   `(Z − 1)` on two independent grounds: the text states the form is chosen so `B(0) = 1`, which
   requires `Z / (1 + (Z − 1)) = Z/Z = 1`; and the structurally identical Process Power logistic on
   p.60 prints the same coefficient explicitly as `(Z − 1)` with uppercase `Z`. Treated as a source
   typo and written `(Z − 1)`, flagged because it is a lone lowercased symbol in a formula.

The extraction memo records that all 87 pages were read with no illegibility gaps and that no
equation in it is a guess; these two are the only judgement calls, both resolved with explicit
reasoning.
