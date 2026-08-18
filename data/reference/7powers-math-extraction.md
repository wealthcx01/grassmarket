# 7 Powers — Mathematics Extraction Memo

**Purpose.** Faithful extraction of the mathematics in Hamilton Helmer's *7 Powers* (the "Notes/Supplement" edition, 87 pp.) as the grounding document for adapting it into the Bruntsfield ATLAS methodology for the *wealth platforms* domain. Helmer will review the resulting adaptation, so every equation below is transcribed from the source page as printed; symbols are defined exactly as Helmer defines them; and every point where the source is ambiguous or a reading was reconstructed is flagged explicitly.

**Rights.** Used under Hamilton Helmer's personal permission to embed and adapt the mathematics of *7 Powers* for Bruntsfield's wealth-platforms use case (ADR-0046). This memo is the analytical extraction. **The source PDF was committed to this repository on 2026-07-31** (`2d81f56`, `data/reference/7powers-audiobook-supplement.pdf`) under the same permission grant; this line previously said it was not, which was true when the memo was written on 2026-07-24 and false afterwards. The memo has since been verified against it — see `docs/reviews/ADR-0046-extraction-verification.md`. Attribution to carry on every embedding surface: *"Adapted from Hamilton Helmer, 7 Powers: The Foundations of Business Strategy, with the author's permission."*

**Source note.** All page numbers are the printed page numbers of the supplement (matching the PNG file numbers). Equations are transcribed in LaTeX-ish plain text. Where Helmer uses a left-subscript convention (e.g. a small `s` or `w` written to the *left* of a symbol to denote the Strong or Weak firm), this memo writes it as `_s X` / `_w X` (so `_sQ` = "S's quantity", `_wP` = "W's price"). Superscript-left `N`/`O` (New/Old business model) are written `^N X` / `^O X`.

**Convention used throughout (Helmer's calibration question).** For every Power, the intensity is calibrated by the *Surplus Leader Margin* (SLM), defined by the question: *"What governs profitability of the company with Power (S) when prices are set such that the company with no Power (W) makes no profit at all?"* S = the strong firm (Power holder); W = the weak firm (no Power).

---

## Table of Contents

- §1 — The Fundamental Equation of Strategy (p.5) + derivation (pp.6–8)
- §2 — The seven Powers (definition, Benefit, Barrier, SLM formula, intensity determinants, Power-Progression time window)
  - §2.0 The 7 Powers map (Benefit × Barrier grid) and how to read it
  - §2.1 Scale Economies
  - §2.2 Network Economies
  - §2.3 Counter-Positioning
  - §2.4 Switching Costs
  - §2.5 Branding
  - §2.6 Cornered Resource
  - §2.7 Process Power
- §3 — Power Dynamics (toolkit, graphical representation, glossary) (pp.78–87)
- §4 — Mapping notes to ATLAS (per-power: SLM input requirements; intensity determinants → rubric anchors for retail brokerage / wealth-advisory / exchange-market-infrastructure)
- §5 — Illegible-page flags and reading reconstructions

---

## §1 The Fundamental Equation of Strategy

### 1.1 Statement (p.5)

Helmer starts from the standard NPV of free cash flow:

```
NPV = Σ ( CF_i / (1+d)^i )
```
where
- `CF_i` = expected free cash flow in period i
- `d` = discount rate

He then states a "mathematically equivalent but more felicitous" form:

```
NPV = M_0 · g · s̄ · m̄
```
where
- `M_0` = current market size
- `g` = discounted market growth factor
- `s̄` = long-term (average) market share
- `m̄` = long-term differential margin (net profit margin **in excess of that needed to cover the cost of capital**)

Hence the boxed **Fundamental Equation of Strategy**:

```
Value = M_0 · g · s̄ · m̄
```

Interpretation given later (p.8, and toolkit p.80):

```
NPV = Market Scale · Power
```
- **Market Scale** = `M_0 · g` (current market size × discounted growth)
- **Power** = `s̄ · m̄` (long-term share × long-term differential margin)

Helmer's definition of (lower-case) strategy is tied to this: *"strategy: a route to continuing Power in significant markets."*

### 1.2 Derivation (Appendix to Introduction, pp.6–8)

**Definitions (p.6):**
- `π_i` ≡ Profits in period i (after taxes, before interest)
- `I_i` ≡ Net investment in period i = ΔWorking Capital + Gross fixed investment − Depreciation
- `K_i` ≡ Capital at end of period i; `K_0` ≡ Initial capital
- `P` ≡ Terminal Sale Price
- `c` ≡ Cost of capital
- `r` ≡ Rate of return
- `γ` ≡ Differential return = `r − c`
- `η` ≡ Top-line growth
- `CF_i` ≡ Cash flow in period i = `π_i − I_i`

**Step 1 — write NPV with terminal value (p.6):**
```
NPV = −K_0 + Σ_{i=1..n} [ (π_i − I_i) / (1+c)^i ] + P/(1+c)^n
```
Substitute `I_i = K_i − K_{i−1}` (net investment = change in capital):
```
NPV = −K_0 + Σ_{i=1..n} [ (π_i − (K_i − K_{i−1})) / (1+c)^i ] + P/(1+c)^n
    = −(Initial investment) + (Discounted cash flows) + (Discounted terminal value)
```
Regroup:
```
NPV = Σ_{i=1..n} [ π_i /(1+c)^i ] − [ K_0 + Σ_{i=1..n} (K_i − K_{i−1})/(1+c)^i ] + P/(1+c)^n
```

**Step 2 — simplify the middle (capital) term (p.7).** By telescoping the term `K_0 + Σ (K_i − K_{i−1})/(1+c)^i`, Helmer reduces it to:
```
K_0 + Σ_{i=1..n} (K_i − K_{i−1})/(1+c)^i  =  Σ_{i=1..n} [ c · K_{i−1} / (1+c)^i ] + K_n/(1+c)^n
```
Substituting back:
```
NPV = Σ_{i=1..n} [ π_i/(1+c)^i ] − [ Σ_{i=1..n} c·K_{i−1}/(1+c)^i + K_n/(1+c)^n ] + P/(1+c)^n
    = Σ_{i=1..n} [ (π_i − c·K_{i−1}) / (1+c)^i ] + (P − K_n)/(1+c)^n
```

**Step 3 — drop the terminal term (finite-life assumption, p.7).** Assume the business has finite life `L`; at `t = L`, `P = 0`. So there exists an `n* < L` such that `|(P − K_n)/(1+c)^n| < ε` for an `ε` immaterial to NPV. At `n*` the second term is ignored:
```
NPV = Σ_{i=1..n*} [ (π_i − c·K_{i−1}) / (1+c)^i ]
```

**Step 4 — express profits via rate of return (p.7).** Use `π_{i} = r·K_{i−1}` (profits = rate of return on prior-period capital), and `γ = r − c`:
```
NPV = Σ_{i=1..n*} [ (r·K_{i−1} − c·K_{i−1}) / (1+c)^i ]
    = Σ_{i=1..n*} [ K_{i−1}(r − c) / (1+c)^i ]
    = Σ_{i=1..n*} [ K_{i−1}·γ / (1+c)^i ]
```
Use constant top-line growth `η` so that `K_{i−1} = K_0(1+η)^{i}` ... written by Helmer as `K_0 (1+η)^{i+1}` inside the sum (see flag §5.1):
```
NPV = Σ_{i=1..n*} [ K_0 (1+η)^{i+1} / (1+c)^i ] · γ
    = K_0 · γ · Σ_{i=1..n*} [ (1+η)^{i+1} / (1+c)^i ]
```

**Step 5 — collapse to the growth factor (p.8):**
```
NPV = K_0 · g · γ      where  g ≡ discounted growth factor = Σ_{i=1..n*} [ (1+η)^{i+1} / (1+c)^i ]
```
`K_0·γ` = "first-period profits in excess of their capital cost."

**Step 6 — re-express in market terms (p.8).** Helmer asserts the equivalence:
```
K_0·γ = M_0 · s̄ · m̄     (both are first-period profits in excess of the cost of capital)
```
with
- `M_0` ≡ initial market size
- `s̄` ≡ average market share
- `m̄` ≡ average profit margin above that needed to return the cost of capital

Therefore:
```
NPV = M_0 · g · s̄ · m̄        ⇒   NPV = Market Scale · Power
```

**The five simplifying assumptions Helmer explicitly lists (p.8):**
1. `n = n*`
2. market growth is constant over `n*`
3. market share is constant over `n*`
4. differential returns are constant over `n*`
5. the business has a finite life

Helmer notes (p.8): to reconcile with actual market cap one would additionally have to add back initial capital, adjust for overall market price levels, and add back excess balance-sheet assets (e.g. accumulated cash).

---

## §2 The Seven Powers

### §2.0 The 7 Powers map — how every power is placed (the Benefit × Barrier grid)

Every per-power figure ("[Power] in the 7 Powers") plots the power onto a single grid. This grid **is** Helmer's operational definition of Benefit and Barrier, so it is reproduced here once.

**Rows = Benefit (to the Power holder).** Two super-groups:
- **ΔCost** (benefit shows up as lower cost):
  1. Input
  2. Scale of Production/Distribution
  3. Production/Distribution Approach
- **ΔValue (⇒ P↑)** (benefit shows up as higher value / ability to raise price):
  4. Superior Deliverables
  5. Affective Valence
  6. Uncertainty (reduction)
  7. Benefits from Other Users

**Columns = Barrier (to the Challenger).** Grouped as "Unwilling to Challenge" vs "Unable to Challenge", with the whole bar annotated **"plus uncertainty"**:
- **Collateral Damage** (unwilling)
- **Share Gain Cost/Benefit** (unwilling ↔ unable boundary)
- **Hysteresis** (unable)
- **Fiat** (unable)

Each power occupies a specific Benefit-row × Barrier-column cell. The complete map (Fig 7.6 / Fig 9.6):

| Power | Benefit row(s) | Barrier column |
|---|---|---|
| Scale Economies | Input, Scale of Prodn/Distn (ΔCost) | Share Gain Cost/Benefit |
| Network Economies | Benefits from Other Users (ΔValue) | Share Gain Cost/Benefit |
| Counter-Positioning | Prodn/Distn Approach + Superior Deliverables | Collateral Damage |
| Switching Costs | Affective Valence + Uncertainty (ΔValue) | Share Gain Cost/Benefit |
| Branding | Affective Valence + Uncertainty (ΔValue) | Hysteresis |
| Cornered Resource | spans ΔCost **and** ΔValue (any benefit) | Fiat |
| Process Power | Prodn/Distn Approach + Superior Deliverables | Hysteresis |

**Power Intensity Determinants** are given in a cumulative table (final complete version = Fig 7.5, p.58). Every power has exactly two determinants:
- one **Industry Economics** determinant (the *magnitude/sustainability* of the leverage — sets how big the margin can be), and
- one **Competitive Position** determinant (the *relative* standing of S vs W — sets whether *this* firm captures it).

The complete determinants table is reproduced per-power below and consolidated in §4.

---

### §2.1 Scale Economies

**Definition (Helmer).** A business in which per-unit cost declines as volume increases (over the relevant range of output).

**Benefit:** reduced cost per unit (ΔCost; rows "Input" and "Scale of Production/Distribution").
**Barrier:** *Share Gain Cost/Benefit* — a challenger would have to gain share to match S's unit cost, but the cost/benefit of gaining that share is unattractive, so the challenger is unwilling/unable.

**Surplus Leader Margin (Appendix 1.1, p.15).** Explores scale from a fixed cost (Helmer notes other sources exist; fixed cost is the common one).

Cost model:
```
Total cost = c·Q + C
  c = variable cost per unit
  Q = units produced
  C = fixed cost (per production period, not start-up)
⇒ Profit  π = (P − c)·Q − C
  P = price faced by all sellers
```
Two firms: S (strong, large `_sQ`) and W (weak, small `_wQ`). Set price so W breaks even:
```
_wπ = 0  ⇒  0 = (P − c)·_wQ − C   ⇒   P = c + C/_wQ
```
S's profit at that price:
```
_sπ = (P − c)·_sQ − C
    = ([c + C/_wQ] − c)·_sQ − C
    = [C/_wQ]·_sQ − C
    = C·(_sQ − _wQ)/_wQ
```
Divide by S's revenue `P·_sQ` to get margin, giving the **boxed SLM**:

```
Surplus Leader Margin = [ C / (P·_sQ) ] · [ _sQ/_wQ − 1 ]
```

Decomposition Helmer gives:
- `[ _sQ/_wQ − 1 ]` = **Competitive Position** — relative market share beyond parity.
- `[ C / (P·_sQ) ]` = **Industry Economics** — the relative importance of the fixed cost.

**Intensity determinants (Fig 7.5).**
- Industry Economics: **Scale economy intensity** (how steeply unit cost falls with volume / how large the fixed cost is relative to the business).
- Competitive Position: **Relative scale** (S's scale vs the largest competitor).

**Power-Progression window:** **Takeoff** (Fig 9.7 / p.84 — Scale Economies is established almost entirely during Takeoff).

---

### §2.2 Network Economies

**Definition (Helmer).** A business in which the value delivered to each customer increases as the installed base (number of users) grows.

**Benefit:** value to the customer rises with the installed base ("Benefits from Other Users", ΔValue ⇒ price premium).
**Barrier:** *Share Gain Cost/Benefit* — a challenger cannot match S's value without matching S's installed base, which is prohibitively costly to build.

**Surplus Leader Margin (Appendix 2.1, p.19).**
```
Total network size (#users)  N = _sN + _wN     (S strong, W weak)
```
Assume homogeneous network effects; S can charge a price premium:
```
_sP − _wP = δ·[_sN − _wN]      δ = marginal benefit to all users from one additional joiner (one joiner)
```
No scale economies, so per-period profit:
```
π = [P − c]·Q     (P price, c variable cost/unit, Q units/period)
```
Set W to break even: `_wπ = 0 ⇒ _wP = c`. Since S can charge the premium `_sP = δ·[_sN − _wN] + c`:
```
_sπ = ([δ(_sN − _wN) + c] − c)·_sQ = [δ(_sN − _wN)]·_sQ
_sMargin = δ(_sN − _wN) / ([δ(_sN − _wN)] + c)
```
Boxed **SLM**:

```
Surplus Leader Margin = 1 − 1 / [ (δ/c)·(_sN − _wN) + 1 ]
```

Decomposition:
- Competitive Position: `[_sN − _wN]` = **absolute difference in installed base**.
- Industry Economics: `δ/c` = value added per additional user per dollar of variable cost.
- Boundary behaviour: if `_sN = _wN`, SLM = 0; as `_sN >> _wN`, SLM → 100% (with δ>0).

Helmer's cautions (pp.20–21): positive network effects need not create Power — if `N·δ < c`, no firm can even reach profitability; sizing `N` and `δ` ex ante is hard (Twitter example). Indirect (demand-side) network effects via exclusive complements are a common twist and are *non-linear*.

**Intensity determinants (Fig 7.5).**
- Industry Economics: **Network effect intensity** (`δ/c`).
- Competitive Position: **Absolute difference in installed base** (`_sN − _wN`).

**Power-Progression window:** **Takeoff**.

---

### §2.3 Counter-Positioning

**Definition (Helmer).** A newcomer (S = challenger) adopts a new, superior business model that the incumbent (W) does not mimic because doing so would damage its existing business.

> **Notation note for CP only:** here the *challenger* is S and the *incumbent* is W (the reverse of the Scale/Network cases). Old model = `^O`, New model = `^N`. `^Nc < ^Oc` (new model has lower cost); the new model cannibalises the old via `^NP < ^OP` (new price below old price).

**Benefit:** superior new business model → lower cost and/or superior deliverables (rows "Prodn/Distn Approach", "Superior Deliverables").
**Barrier:** *Collateral Damage* — the incumbent is **unwilling** to adopt the new model because entering it would inflict loss on its existing (Old) business.

**Surplus Leader Margin (Appendix 3.1, pp.27–28).** Single-period, strictly variable cost: `π = (P − c)·Q`. SLM in CP is the challenger's (S's) margin at the point where the incumbent's (W's) *incremental* profitability from deciding to enter the New business is exactly zero. Dropping the S/W left-subscripts (collateral damage refers only to W's economics):
```
SLM  ⇒  ^Nπ + Δ^Oπ = 0
     ( Δ^Oπ = change in W's Old-business profits induced by W entering New )
```
Writing profit = margin × revenue:
```
^Nm·[^NP·^NQ] + ^Om·[^OP·Δ^OQ] = 0
^Nm·[^NP·^NQ] = − ^Om·[^OP·Δ^OQ]
^Nm = ^Om · [^OP/^NP] · [ −Δ^OQ / ^NQ ]
```
Define the **induced cannibalization ratio** `δ = −Δ^OQ / ^NQ` (W's induced loss of Old volume per unit of New volume). Boxed **SLM**:

```
SLM = ^Om · [ ^OP / ^NP ] · δ
```
where
- `^Om` = incumbent's Old-business margin
- `^OP / ^NP` = ratio of Old price to New price (>1, since New is cheaper)
- `δ` = induced cannibalization ratio

**Key structural implications Helmer draws (pp.28–31):**
- If `Δ^OQ = 0` then `δ = 0`, so SLM = 0 and there is **no CP** (no collateral damage). Counter-positioned incumbents therefore often seek customer segments where entering New induces no incremental Old-customer loss.
- If `δ < 1` (unit gains in New more than offset by Old losses), CP is unlikely unless New margins are attractive enough.
- **Irony:** the *higher* the incumbent's margin `^Om`, the *higher* the SLM — an entrenched, highly profitable incumbent is more vulnerable to CP.
- The three "don't invest" incumbent failure modes (decision tree, p.25): **Milk** (rational: negative joint NPV of entering), **History's Slave** (cognitive bias raising expected δ), **Job Security** (agency: `^NQ` credited to a different division ⇒ δ→∞ for the decision-maker). These are additive, not exclusive.
- **Dynamics:** over time δ tends to decline (as New is proven, `^NQ` rises and `|Δ^OQ|` falls) ⇒ SLM declines ⇒ eventually the "capitulation point" where collateral damage no longer deters the incumbent.

**Intensity determinants (Fig 7.5).**
- Industry Economics: **New business-model superiority + collateral damage to old** (magnitude of `^Om·[^OP/^NP]·δ`).
- Competitive Position: **Binary** — entrant has the new model; incumbent has the old model.

**Power-Progression window:** **Origination**.

---

### §2.4 Switching Costs

**Definition (Helmer).** The value loss a customer would incur by switching to an alternative supplier for a *subsequent* purchase; it lets the incumbent (S = the firm that already has the customer) charge a premium.

**Benefit:** ability to charge existing customers a premium on follow-on products (ΔValue; rows "Affective Valence" + "Uncertainty").
**Barrier:** *Share Gain Cost/Benefit* — a challenger must compensate the customer for the switching cost to win the sale, which is unattractive.

**Surplus Leader Margin (Appendix 4.1, p.37).** Here W = "the company **not** having the customer." `_sQ` customers have already adopted S; examine the benefit on subsequent products. Utility of the subsequent product assumed equal for both firms; S charges a premium equal to the switching cost `Δ`:
```
_sP = Δ + _wP     (Δ = switching cost per unit)
```
No fixed costs: `π = [P − c]·Q`. Set W to break even: `_wπ = 0 ⇒ _wP = c`. Then `_sP = Δ + c`, so:
```
_sπ = [(Δ + c) − c]·_sQ = Δ·_sQ
```
Boxed **SLM**:

```
SLM = Δ
```
(i.e. the SLM per unit of revenue reduces to the switching cost Δ expressed as a margin.)

Decomposition:
- Industry Economics: `Δ` (magnitude of the switching cost).
- Competitive Position: `_sQ` (number of current customers already held by S).

**Intensity determinants (Fig 7.5).**
- Industry Economics: **Magnitude (intensity) of switching costs**.
- Competitive Position: **Number of current customers**.

**Power-Progression window:** **Takeoff**.

---

### §2.5 Branding

**Definition (Helmer).** The durable attribution of higher value to an objectively identical offering, arising from the historical information the buyer holds about the brand. Delivers value two ways: **affective valence** (feeling/identity) and **uncertainty reduction** (confidence in quality).

**Benefit:** ability to charge a price premium (ΔValue; "Affective Valence" + "Uncertainty").
**Barrier:** *Hysteresis* — brand strength is built only slowly over time; a challenger *cannot* replicate it quickly at any price.

**Surplus Leader Margin (Appendix 5.1, pp.44–45).** First specify the price-premium envelope as a function of time. The **branding price multiple** `B(t)`:

```
B(t) = [ Z / (1 + (Z−1)·e^(−F·t) ) ] · D_t · U_t
```
where
- `B(t)` = branding price multiple at time t (= `_sP / _wP`, the ratio of strong to weak firm price)
- `Z` = maximum potential branding multiple for this good type, `Z > 2`
- `F` = brand cycle-time **compression factor**, `F > 0` (larger F ⇒ steeper logistic ⇒ shorter brand cycle time; smaller F ⇒ shallower ⇒ longer)
- `D_t` = brand **dilution** at time t, `0 ≤ D ≤ 1` (`D = 1` = no dilution)
- `U_t` = brand **underinvestment** at time t, `0 ≤ U ≤ 1` (`U = 1` = no underinvestment)
- `t` = time (competitive-position axis: how long S has been building brand vs a challenger starting at t=0)

The logistic form is chosen so that `B(0) = 1` (the location parameter is adjusted as a function of F and Z). *Flag: the source prints the coefficient as lowercase `(z−1)`; it is `(Z−1)` — see §5.2.*

Profit (no fixed costs): `π = [P − c]·Q`, `c = marginal cost/unit`. Set W to break even: `_wπ = 0 ⇒ _wP = c`. S charges a multiple of W's price: `_sP = B(t)·c`. Then:
```
_sπ = [B(t)·c − c]·_sQ = [(B(t)−1)·c]·_sQ = (B(t)−1)·c·_sQ
_sMargin = (B(t)−1)·c·_sQ / (B(t)·c·_sQ) = 1 − 1/B(t)
```
Boxed **SLM**:

```
SLM = 1 − 1/B(t)
```

Reading Helmer gives (p.45): `B()` (through `Z` and `F`) represents **industry economics** — the magnitude and sustainability of the leverage; `t` represents **competitive position** — how far S is ahead of W in developing Branding Power.

**Compression-factor picture (Fig 5.6, p.46).** Plots `B(t) = _sP/_wP` against time for two compression factors: `F = 1` (solid, steeper — brand matures fast) and `F' = 1/2` (dashed, shallower — matures slowly). The asymptote height is `Z = significance`. The horizontal extent is **Sustainability (F)**. So the two economic dials are: **Z = significance/magnitude** (how large the ceiling premium is) and **F = sustainability** (how compressed the build cycle is; smaller F ⇒ longer, harder-to-catch cycle).

**Intensity determinants (Fig 7.5).**
- Industry Economics: **Time constant and potential magnitude of the Branding effect** (F and Z).
- Competitive Position: **Duration of brand investing** (t — how long S has been building vs the challenger).

**Power-Progression window:** **Stability**.

---

### §2.6 Cornered Resource

**Definition (Helmer).** Preferential access, at attractive terms, to a coveted resource that independently produces a superior outcome (e.g. Pixar's core creative group). Deliberately restricted (Appendix 6.1) to resources that qualify as *Power* — i.e. that are superior, significant, and sustained by fiat rather than merely notable.

**Benefit:** the resource yields either a price premium (superior deliverables) or a cost reduction — Helmer's SLM below lumps both into a single per-unit profit increment `Δ`. (In the grid, Cornered Resource spans **both** ΔCost and ΔValue.)
**Barrier:** *Fiat* — S controls the resource by fiat (contract/ownership/exclusive relationship); the challenger simply *cannot* obtain it.

**Surplus Leader Margin (Appendix 6.2, pp.53–54).** Suppose the CR gives S a per-unit profit increase `Δ` (from a price increase due to superior deliverables, or a cost decrease). Assume no fixed production costs; but the CR carries an incremental fixed cost `k` per period (e.g. the extra compensation to retain the core group above replacement cost; `k` need not be positive).
```
S's profit:  _sπ = [_wP + Δ − c]·_sQ − k
```
Set W to break even: `_wπ = 0 ⇒ _wP = c`. Substitute:
```
_sπ = [(Δ + _wP) − c]·_sQ − k = [(Δ + c) − c]·_sQ − k = Δ·_sQ − k
```
Margin = `_sπ / [ (Δ + _wP)·_sQ ]`. Boxed **SLM**:

```
SLM = Δ / (Δ + _wP)  −  k / [ (Δ + _wP) · _sQ ]
    = [Margin increase due to CR]  −  [CR cost per dollar of sales]
```

Decomposition:
- Industry Economics: `Δ, k` (the per-unit profit increment and the incremental fixed cost of holding the CR).
- Competitive Position: **control of CR by fiat or not** (binary).

*(Appendix 6.1 situates this against the Resource-Based View: Helmer restricts "resource" to the statics of Power; the broader RBV notion of resources/capabilities returns in the Dynamics half of the book, where "invention is the first cause of Power.")*

**Intensity determinants (Fig 7.5).**
- Industry Economics: **Price and/or cost increment due to CR** (`Δ`, net of `k`).
- Competitive Position: **Preferred access at a non-arbitraging price** (control of the CR by fiat).

**Power-Progression window:** **Origination**.

---

### §2.7 Process Power

**Definition (Helmer).** Embedded company organisation and activity sets that enable lower costs and/or a superior product, and which can be matched only by an extended commitment (experience-curve / accumulated-process advancement — Toyota Production System archetype).

**Benefit:** lower cost and/or superior deliverables from the accumulated process (rows "Prodn/Distn Approach" + "Superior Deliverables").
**Barrier:** *Hysteresis* — process advancement is achieved only slowly and sequentially; a challenger *cannot* catch up quickly even if the process is visible.

**Surplus Leader Margin (Appendix 7.1, p.60).** All costs marginal; zero-challenger-profit price = marginal cost. Focus on the case where the leader's costs are lower due to Process Power (symmetrically it could charge a higher price, or both).
```
π = [P − c]·Q     (c = marginal cost/unit)
```
Set W to break even: `_wπ = 0 ⇒ P = _wc`. Suppose:
- `D(t)` = W's cost multiple at time t (W's cost as a multiple of S's cost)
- `Z` = maximum potential cost multiple
- `F` = cycle-time compression factor

W's cost is a multiple of S's cost: `_wc = D(t)·_sc`. Then:
```
_sπ = [P − _sc]·_sQ = [D(t)·_sc − _sc]·_sQ = (D(t)−1)·_sc·_sQ
_sMargin = (D(t)−1)·_sc·_sQ / (D(t)·_sc·_sQ) = 1 − 1/D(t)
```
Boxed **SLM**:

```
SLM = 1 − 1/D(t)      with   D(t) = Z / (1 + (Z−1)·e^(−F·t))
```

This is the exact structural twin of the Branding SLM (`1 − 1/B(t)`), with the same logistic and the same `B(0)=D(0)=1` normalisation — confirming the Branding coefficient is `(Z−1)` (§5.2). Here `D()` (via Z, F) is the industry-economics term (magnitude and sustainability of leverage) and `t` is the competitive-position term. Fig 7.6 (p.61) plots S's cost discount `1/D(t)` falling over years from a baseline `_wc`, with `Z` the significance and `F` the sustainability.

**Intensity determinants (Fig 7.5).**
- Industry Economics: **Time constant and potential magnitude of the Process Power effect** (F and Z).
- Competitive Position: **Relative duration of Process Power advances** (t).

**Power-Progression window:** **Stability**.

---

### §2.8 Consolidated Power Intensity Determinants (Fig 7.5, p.58)

| Power | Industry Economics determinant | Competitive Position determinant |
|---|---|---|
| Scale Economies | Scale economy intensity | Relative scale |
| Network Economies | Network effect intensity | Absolute difference in installed base |
| Counter-Positioning | New business-model superiority + collateral damage to old | Binary: entrant=new model; incumbent=old model |
| Switching Costs | Magnitude (intensity) of switching costs | Number of current customers |
| Branding | Time constant + potential magnitude of Branding effect (F, Z) | Duration of brand investing (t) |
| Cornered Resource | Price and/or cost increment due to CR (Δ, k) | Preferred access at a non-arbitraging price (fiat) |
| Process Power | Time constant + potential magnitude of Process Power effect (F, Z) | Relative duration of Process Power advances (t) |

### §2.9 Consolidated SLM formulas

| Power | SLM | Industry-economics term | Competitive-position term |
|---|---|---|---|
| Scale Economies | `[C/(P·_sQ)]·[_sQ/_wQ − 1]` | `C/(P·_sQ)` (fixed-cost weight) | `_sQ/_wQ − 1` (relative share) |
| Network Economies | `1 − 1/[(δ/c)(_sN − _wN) + 1]` | `δ/c` | `_sN − _wN` |
| Counter-Positioning | `^Om · (^OP/^NP) · δ` | `^Om·(^OP/^NP)` | δ (induced cannibalization) [binary who-holds] |
| Switching Costs | `Δ` | `Δ` | `_sQ` |
| Branding | `1 − 1/B(t)`, `B(t)=Z/(1+(Z−1)e^{−Ft})·D_t·U_t` | `Z, F` (via B) | `t` |
| Cornered Resource | `Δ/(Δ+_wP) − k/[(Δ+_wP)_sQ]` | `Δ, k` | fiat control (binary) |
| Process Power | `1 − 1/D(t)`, `D(t)=Z/(1+(Z−1)e^{−Ft})` | `Z, F` (via D) | `t` |

### §2.10 Power Progression time windows (Figs 9.6/9.7 p.78–79; Fig p.84)

The Power Progression has three business-stage phases — **Origination → Takeoff → Stability** — where the break between Takeoff and Stability is when unit growth falls below ~30–40%/yr. Each Power's *establishment window* (when its Barrier can first be erected):

- **Origination:** Cornered Resource, Counter-Positioning
- **Takeoff:** Network Economies, Scale Economies, Switching Costs
- **Stability:** Branding, Process Power

(Helmer stresses this is a *business-stage* framework, distinct from the product life-cycle Introduction/Growth/Maturity/Decline.)

---

## §3 Power Dynamics

### §3.1 The Power Dynamics Toolkit (Appendix 9.1, pp.80–84) — seven perspectives

1. **The Value Axiom.** Strategy has one and only one objective: maximizing potential fundamental business value. (An assumption, not a proof; fundamental *not* speculative; *potential* value — realizing it requires operational excellence.)

2. **The 3 S's.** Power = the potential to realize persistent differential returns. A business attribute creates Power if it is simultaneously:
   - **Superior** — improves free cash flow
   - **Significant** — the cash-flow improvement is material
   - **Sustainable** — largely immune to competitive arbitrage
   Mapping to the book's Benefit/Barrier: **Superior + Significant = Benefit**, **Sustainable = Barrier**. The 3-S form adds value because it calls out *Significant* (materiality) explicitly — many businesses claim network effects that are not material and so are not Power.

3. **The Fundamental Equation of Strategy.** `Value = M_0 · g · s̄ · m̄` (= Market Size × Power). Ties strategy concepts to the exact NPV determinants; `s̄` and `m̄` are long-term equilibrium values (short-term moves don't change fundamental value).

4. **The Mantra.** "*A route to continuing Power in significant markets*" — the complete statement of a strategy; maps directly to the Fundamental Equation and is inclusive of Dynamics. "Continuing" is included to encourage ongoing layering of different Power sources as a business progresses.

5. **The 7 Powers.** The seven Power types on the Benefit×Barrier chart are (Helmer claims) the *only* strategies available. If you cannot see a route to at least one of these for each competitor (current & potential, direct & functional), you lack a viable strategy. Two extra virtues: **(a) Small set** — only 7 possibilities to check; the Power Progression caps the number of *new* Powers explorable at any growth stage at 3. **(b) Observable ex ante** — the potential for a Power type is usually evident well before detailed forecasting is possible.

6. **"Me Too" Won't Do (Invention is the first cause of Power).** Diagram: **"Resources" [Company & Individual]** + **External Conditions** → **Invention** {Product / Business model / Brand / Process} → then two questions: **Market?** and **Power?**. Every one of the 7 Powers requires an invention (of product, business model, process, or brand). Sufficiency marker of the resulting Benefit = "compelling value" ("gotta have" response). Three paths to compelling value: **Capabilities-led, Customer-led, Competitor-led**. Welfare note: the *possibility* of Power is a critical motivator of invention (a Dynamics view, versus the static "zero-sum" view).

7. **The Power Progression.** `Origination → Takeoff → Stability` on a Business-Size(\$) vs time S-curve; Takeoff/Stability break at ~30–40% unit growth. Tells you *when* each Power's establishment window opens and closes (see §2.10).

### §3.2 Graphical representation (Appendix 9.2, p.85)

A single relationship diagram tying the tools together:

- **One objective: `Value = M_0 · g · s̄ · m̄`** at the top; the arrow into Value is annotated **"The Mantra: a route to continuing Power in significant markets."**
- **Value** decomposes into **Market Size** and **Power**; **Power** is reached via the **3 S's: Benefit + Barrier**.
- **Statics — "Being There"**: the **7 Powers** Benefit×Barrier grid (the static positions).
- **Dynamics — "Getting There"**: **Resources + External Conditions → Invention → { Market?, Power? }**; the **Power?** branch flows into the **Power Progression** ("When?"); the **Market?** branch flows into **Compelling Value** (a Venn of *Customer Needs*, *Competitor Offerings*, *Your Capabilities* with the star at the intersection) driving **Market Share**.

So: Statics answers *what* Power you hold; Dynamics answers *how/when* you get it; both feed the single Value objective.

### §3.3 Power Dynamics Glossary (Appendix 9.3, pp.86–87) — verbatim terms

- **Strategy** (capital S): the intellectual discipline (a.k.a. Strategic Management) — "the study of the fundamental determinants of potential business value."
- **Power:** the set of conditions needed for persistent differential returns. Power requires **both** a **Benefit** (something that materially increases cash flow) **and** a **Barrier** (conditions such that all the value to the firm of the Benefit is not arbitraged out by competition).
- **strategy** (lower-case s): the path to potential value for a strategically separate business — "a route to continuing Power in significant markets."
- **value:** the fundamental enterprise value of an activity; reflected *ex post* as generation of accessible returns to an owner (free cash flow); *ex ante* it is investors' discounted expectation of that return stream.
- **Strategy Dynamics:** the study of strategy development over time.
- **Strategy Statics:** the study of strategic position at a single point in time.
- **industry:** the group of businesses whose products have a high degree of substitutability.
- **business:** a strategically separate economic activity — "strategically separate" meaning its Power position is largely orthogonal to that of the firm's other activities.
- **market:** the revenue attributable to all firms in an industry.
- **industry economics:** the economic structure of a particular industry (e.g. with fixed-cost-driven Scale Economies, measured by the magnitude of the fixed cost relative to the company's overall financials).
- **competitive position:** a characterization of a company's position in the metric relevant to Power (e.g. with Scale Economies, relative scale vs the largest competitor).
- **Surplus Leader Margin:** the profit margin a Power holder achieves if pricing is such that a competing firm with no Power has zero profits. Not necessarily an expected equilibrium — a *marker of leverage*. Equals `m̄` in the Fundamental Equation **iff** the no-Power firm experiences competitive arbitrage down to earning just its cost of capital *and* the Power firm's cost of capital equals the no-Power firm's.

---

## §4 Mapping notes to ATLAS

**How ATLAS uses this.** ATLAS scores each Power as **strength = min(Benefit, Barrier)** on an ordinal scale **{None, Emerging, Established, Wide}**, with a separate Benefit rating and Barrier rating per power. The `min()` is directly faithful to Helmer's glossary: *Power requires **both** a Benefit **and** a Barrier* — a strong Benefit with no Barrier is arbitraged away; a strong Barrier around no Benefit protects nothing. B (business metrics), L (infrastructure) and C (customer proposition) are ATLAS's own lenses and have **no** Helmer analogue — they must not be represented as part of the 7 Powers math.

For each power below:
- **(a) SLM input requirements** — the exact quantities ATLAS would have to source if it ever wanted to compute the SLM quantitatively (rather than rate ordinally). Useful as the "evidence checklist" behind each ordinal anchor.
- **(b) Determinant → rubric anchors** for the three wealth-platform segments: **RB** = retail brokerage, **WA** = wealth/advisory, **EX** = exchange / market-infrastructure. One concrete example per segment.

General note on the two-determinant structure: for **every** power, the **Industry Economics** determinant should drive the **Benefit/None→Wide magnitude anchors** (how big the prize is in that industry), and the **Competitive Position** determinant should drive **this-firm's Barrier/relative anchors** (whether this specific firm holds the leading position). This maps cleanly onto ATLAS's split Benefit-rating vs Barrier-rating.

---

### §4.1 Scale Economies
**(a) SLM inputs:** fixed cost per period `C`; market price `P`; strong-firm volume `_sQ`; weak-firm (relevant competitor) volume `_wQ`. Compute `[C/(P·_sQ)]·[_sQ/_wQ − 1]`.
**(b) Determinants → anchors:**
- Industry Economics = *scale-economy intensity* (fixed-cost weight). Anchors on how large fixed/near-fixed cost is relative to revenue.
  - **RB:** technology/clearing/compliance platform cost is a large fixed base spread over trade/account volume — high intensity (a discount broker's per-trade cost falls sharply with order flow). Wide-anchor: platform+regulatory fixed cost > ~X% of revenue and top-1 order-flow scale.
  - **WA:** advice delivery is more people-variable; scale economy is *moderate* (fixed cost = planning tooling, research, compliance overhead per adviser). Established only when a shared research/planning/tech stack is amortised across many advisers.
  - **EX:** matching-engine + surveillance + connectivity are almost pure fixed cost; marginal cost per additional message ≈ 0 — very high intensity. Wide-anchor: exchange runs the dominant venue's fixed tech base at negligible marginal cost per trade.
- Competitive Position = *relative scale*. Anchor `_sQ/_wQ` (this firm's volume vs the largest rival).
  - RB: ratio of this broker's annual trades/AUC to the #1 rival's. WA: ratio of adviser count / AUA to the largest peer. EX: ratio of matched volume / notional to the next venue.

### §4.2 Network Economies
**(a) SLM inputs:** marginal benefit per additional user `δ`; variable cost per unit `c`; installed bases `_sN`, `_wN`. Compute `1 − 1/[(δ/c)(_sN − _wN)+1]`.
**(b) Determinants → anchors:**
- Industry Economics = *network-effect intensity* (`δ/c`): how much each extra participant raises value for all.
  - **RB:** weak-to-moderate direct network effects (a retail brokerage account isn't more valuable because others hold one); may exist via social/copy-trading or fractional-share liquidity features. None/Emerging for a plain broker; Emerging where a social-investing layer exists.
  - **WA:** generally low direct network effect (advice is bilateral); possible *indirect* effect via marketplace of third-party managers/complements. Rate None unless a genuine two-sided adviser↔product marketplace exists.
  - **EX:** the archetypal strong network effect — liquidity begets liquidity; each additional order improves fills for all. Wide-anchor: the venue whose `_sN − _wN` (liquidity lead) is large and self-reinforcing. This is usually an exchange's dominant Power.
- Competitive Position = *absolute difference in installed base* `_sN − _wN`.
  - RB: active-account or connected-user lead over rival. WA: participant count on the marketplace vs next platform. EX: displayed-liquidity / member-connection lead over the next venue (note: absolute gap, not ratio — Helmer is explicit).

### §4.3 Counter-Positioning
**(a) SLM inputs:** incumbent Old-business margin `^Om`; Old vs New price ratio `^OP/^NP`; induced cannibalization ratio `δ = −Δ^OQ/^NQ`. Compute `^Om·(^OP/^NP)·δ`. Also test the three failure modes (Milk / History's Slave / Job Security).
**(b) Determinants → anchors:**
- Industry Economics = *new-model superiority + collateral damage to old*.
  - **RB:** zero-commission / payment-for-order-flow model counter-positioned against full-commission incumbents (incumbents unwilling to zero out their commission line — high `^Om`, high collateral damage). Strong CP example; Established/Wide for the challenger during Origination.
  - **WA:** flat-fee / fiduciary RIA model counter-positioned against commission-and-trailer incumbents; the incumbent's high-margin trailer book is exactly the collateral damage that deters imitation. Classic CP wedge for a fee-only challenger.
  - **EX:** maker-taker / all-to-all or exchange-cleared model counter-positioned against incumbent dealer/OTC intermediation whose spread income would be cannibalised. Rate CP by how much dealer margin (`^Om`) the incumbent must destroy to match.
- Competitive Position = *binary* (challenger = new model; incumbent = old). ATLAS Barrier anchor is essentially present/absent + durability of the incumbent's unwillingness (δ trend over time — CP decays as δ→0).

### §4.4 Switching Costs
**(a) SLM inputs:** switching cost per unit `Δ`; number of current customers held `_sQ`. SLM = `Δ`.
**(b) Determinants → anchors:**
- Industry Economics = *magnitude of switching costs*.
  - **RB:** account-transfer friction (ACATS delays, tax-lot re-basing, re-linking direct deposits/bill-pay, learning a new app) — moderate `Δ`; higher where tax-lot history and margin/options approvals are embedded. Established where re-papering + tax friction is real.
  - **WA:** high `Δ` — moving an advisory relationship means re-onboarding, re-doing financial plans, re-establishing trust, potential tax realization, and relationship-manager loss. Often the dominant Power for advisory. Wide-anchor: multi-account households with embedded plans and held-away integrations.
  - **EX:** switching cost sits with *members/vendors* — recoded FIX connections, re-certified gateways, colocation, and back-office mappings; plus regulatory best-execution retooling. High `Δ` per connected participant.
- Competitive Position = *number of current customers* `_sQ`.
  - RB: funded accounts held. WA: advisory households/relationships held. EX: certified member/vendor connections held.

### §4.5 Branding
**(a) SLM inputs:** to compute `1 − 1/B(t)` you need `B(t)=Z/(1+(Z−1)e^{−Ft})·D_t·U_t`: potential multiple `Z (>2)`; compression factor `F`; time-in-brand `t`; dilution `D_t∈[0,1]`; underinvestment `U_t∈[0,1]`. In practice the observable proxy is the realized price/fee premium ratio `_sP/_wP`.
**(b) Determinants → anchors:**
- Industry Economics = *time constant + potential magnitude* (F, Z): how large a trust/prestige premium the category permits and how slowly it builds.
  - **RB:** brand as *safety/trust* signal (custody of my money) — moderate-to-high Z for a century-old name; premium shows as lower acquisition cost and stickier deposits rather than headline fees. Established for heritage custodians.
  - **WA:** very high Z — advisory is an uncertainty-and-affective-valence purchase (private-bank cachet, "trusted with my family's wealth"). Long build (`F` small ⇒ sustainable). Wide-anchor: a multi-generational private-bank brand commanding a fee premium peers cannot match.
  - **EX:** brand = *integrity/reference-price authority* (the "official" price, index/benchmark trust). Z shows as listings prestige and data-licensing premium. Established where the venue is the reference market.
- Competitive Position = *duration of brand investing* `t`. Anchor on years of consistent, non-diluted, non-underinvested brand building (D≈U≈1) vs a challenger starting at t=0.

### §4.6 Cornered Resource
**(a) SLM inputs:** per-unit profit increment from the resource `Δ`; incremental fixed cost of holding it `k`; strong-firm volume `_sQ`; weak price `_wP`. Compute `Δ/(Δ+_wP) − k/[(Δ+_wP)_sQ]`.
**(b) Determinants → anchors:**
- Industry Economics = *price/cost increment due to CR* (`Δ`, net `k`).
  - **RB:** exclusive order-flow / data feeds, or an exclusive distribution channel (e.g. a captive employer-plan or banking-app funnel) delivering cheaper acquisition. Rate by the acquisition-cost or spread advantage vs `k` (cost to keep the arrangement).
  - **WA:** a cornered talent group (a star CIO/team) or exclusive access to a scarce product (e.g. sole distribution of a coveted fund/allocation). Δ = fee/retention premium the talent or product commands; `k` = the extra comp to retain them (directly Helmer's Pixar analogy).
  - **EX:** exclusive rights — a proprietary index/benchmark, a regulatory licence/monopoly on a contract, or sole listing rights. Δ = licensing/listing rent; barrier is pure *fiat* (contract/regulation).
- Competitive Position = *preferred access at a non-arbitraging price* (fiat, binary). ATLAS Barrier anchor: is the access legally/contractually locked (Wide) or merely favourable (Emerging)?

### §4.7 Process Power
**(a) SLM inputs:** to compute `1 − 1/D(t)` you need `D(t)=Z/(1+(Z−1)e^{−Ft})`: potential cost/quality multiple `Z`; compression factor `F`; accumulated time `t`. Observable proxy: realized relative cost `_wc/_sc`.
**(b) Determinants → anchors:**
- Industry Economics = *time constant + potential magnitude of the process effect* (F, Z): how much embedded operational process can lower cost / raise quality, and how slowly it accrues.
  - **RB:** straight-through-processing / automated onboarding / risk-and-margin engines refined over many release cycles — hard to copy quickly. Established where per-account operating cost is structurally below peers via accumulated automation.
  - **WA:** a proprietary, deeply-embedded advice-and-servicing operating model (planning workflows, compliance automation, next-best-action) that raises adviser productivity; matched only by years of iteration. Rate by relative cost-to-serve per household.
  - **EX:** ultra-low-latency matching + surveillance + resilience engineering accumulated over years (an "experience-curve" of the trading stack). Wide-anchor: a venue whose latency/throughput/uptime advantage a rival cannot replicate within a short horizon.
- Competitive Position = *relative duration of process advances* `t`. Anchor on lead-time (years of accumulated process advancement) over the nearest challenger.

### §4.8 Cross-cutting ATLAS guidance
- **`min(Benefit, Barrier)` is Helmer-faithful**: keep both ratings independent and take the min; do not average.
- **Benefit magnitude ← Industry Economics; Barrier/relative ← Competitive Position.** This gives a principled, per-power rule for which evidence feeds which of ATLAS's two sub-ratings.
- **The Power Progression (Origination/Takeoff/Stability) gates *availability*.** ATLAS should not rate (or should cap) a Power whose establishment window is not open for the firm's stage: CP/CR only originate early; Scale/Network/Switching in Takeoff; Branding/Process in Stability. Only ~3 new Powers are ever "in play" at a given stage.
- **Binary vs continuous determinants differ by power.** CP and CR have *binary* competitive-position determinants (who holds the new model / who holds the resource by fiat) — their Barrier rating is closer to present/absent + durability, not a smooth scale. Scale/Network/Switching/Branding/Process have *continuous* competitive-position metrics (ratio, gap, count, or time) that map naturally to the four-point ordinal.
- **SLM as `m̄` caveat (glossary):** SLM only equals the Fundamental-Equation `m̄` under the stated arbitrage + equal-cost-of-capital conditions. If ATLAS ever prices a Power from an SLM estimate, it must not silently treat SLM as the realized long-term differential margin.

---

## §5 Illegible-page flags and reading reconstructions

**§5.1 — p.7, the `K_{i−1}` growth substitution (reading reconstruction, not illegible).** In Step 4, Helmer writes the substitution inside the sum as `K_0 (1+η)^{i+1}` (superscript `i+1`), i.e.
`NPV = Σ_{i=1..n*} [ K_0(1+η)^{i+1}/(1+c)^i ]·γ`, then factors to `NPV = K_0·Σ[(1+η)^{i+1}/(1+c)^i]·γ`. The `i+1` exponent is exactly as printed. Dimensionally one would expect `K_{i−1}=K_0(1+η)^{i-1}` from "capital at end of period i−1"; Helmer's `i+1` reflects his own indexing/timing convention (and is immaterial to the final collapsed form `NPV=K_0·g·γ`). Transcribed as printed; flag raised so Helmer can confirm the exponent convention.

**§5.2 — p.44, Branding `B(t)` coefficient (resolved reading).** The Branding formula prints the logistic coefficient as lowercase `(z−1)`:
`B(t) = Z/(1 + (z−1)e^{−Ft})·D_t·U_t`, while the ceiling parameter is uppercase `Z (>2)`. This lowercase `z` is read as `Z`, on two independent grounds: (i) the text states the form is chosen so `B(0)=1`, which requires the constant to be `(Z−1)` (giving `Z/(1+(Z−1)) = Z/Z = 1`); (ii) the structurally identical Process Power formula on **p.60** prints the same logistic explicitly as `D(t) = Z/(1 + (Z−1)e^{−Ft})` with uppercase `Z` in both places. Treated as a typo in the source; memo uses `(Z−1)`. **No unreadable content** — flagged only because a lone lowercased symbol in a formula shown to the author warrants a note.

**§5.3 — No pages were illegible.** All 87 pages rendered clearly at the provided resolution; the one 4× re-render (p.44 formula band) was precautionary and confirmed the surrounding text, not needed for legibility. No equation in this memo is a guess; the only two judgement calls are the two flags above, both resolved with explicit reasoning.
