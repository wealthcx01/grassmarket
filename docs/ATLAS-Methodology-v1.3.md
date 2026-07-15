# ATLAS Methodology v1.3 — DRAFT (not normative until ADR-0023 is accepted)

**Bruntsfield Capital — CONFIDENTIAL — July 2026**

**Status: DRAFT.** This document becomes normative only when **ADR-0023** is accepted (it carries two
open founder decisions: the C module set and staged entry into V). Until then, **v1.2 remains the
normative methodology** and nothing here changes engine behaviour.

v1.3 introduces a **fourth lens — C (Customer Proposition)** — as an **additive, reported** index.
It **adds §13** and amends **§2 (framework)** only. **§5.1 (the composite) is deliberately
UNCHANGED**: `V` remains the three-index composite in v1.3. All other sections (§1, §3.3, §4, §5.2–
§5.4, §6, §7–§12) are unchanged from v1.2/v1.1 and are incorporated by reference.

---

## 1.1 Changelog: v1.2 → v1.3

v1.3 promotes the C-index from the v2 agenda (`METHODOLOGY-V2-SCOPE.md` §1, deferred by the founder
at the GRS-0003 golden-master review) into the methodology — **staged**, so that the ratified
numbers are not disturbed.

| Amendment | Section | ADR |
|---|---|---|
| Framework gains a fourth lens **C (Customer Proposition)**, **reported alongside V, not inside it** | §2 | ADR-0023 |
| **§13 Customer Proposition (new):** 10 Phase-E modules, scored on the L aggregation family, with the 93-widget checklist as Level-1 data and rarity as the differentiation weight | §13 | ADR-0023 |
| Presence states extend with `PRESENT_PAYWALLED` / `PRESENT_DEFECTIVE` | §13.3 | ADR-0023 |
| **Composite unchanged** — `V = θ_B·B + θ_P·P + θ_L·L`. C enters V in **v1.4**, after θ re-elicitation | §5.1 (untouched) | ADR-0023 |

### Version-stamping convention (v1.3)

**§5 is unchanged, so the deterministic engine, the CoefficientSet and the ratified golden master
retain the `1.1` stamp** — John's ratified numbers are untouched, exactly as in v1.2. C carries the
`1.3` stamp as its own reported index. A run that scores C is a **B/P/L/V + C** run: V is the
three-index composite and C is reported beside it, never silently folded in.

**Stage 2 (v1.4, future):** once θ is re-elicited across four lenses (Σθ = 1), §5.1 becomes
`V = θ_B·B + θ_P·P + θ_L·L + θ_C·C`. That **is** a deterministic change and requires **golden-master
v2**. An engine without an elicited `θ_C` **MUST refuse** to emit a four-index V (fail-loud,
ADR-0001) — it must never default `θ_C = 0`.

---

## 2. Framework & triad (amended)

ATLAS assesses a platform on **four lenses**, each 0–1:

- **B — Business.** Economic performance from 10 grouped metrics (§5.3).
- **P — Strategic Power.** Helmer's 7 Powers, Benefit/Barrier + evidence (§8).
- **L — Infrastructure.** 9 technology modules / 51 subcomponents, maturity-rated (§5.2).
- **C — Customer Proposition.** 10 modules over the customer-facing product, maturity-rated with per-widget Level-1 evidence (§13). **Reported alongside V in v1.3; enters V at v1.4.**

**Platform Value (V)** remains `θ_B·B + θ_P·P + θ_L·L` in v1.3.

The **Platform Power triad** (Economic / Perceived / Defence Value) is derived as in §8 — unchanged.
C **strengthens the Perceived-Value narrative** by supplying observed customer experience as its
evidence base (rather than claimed NPS), but does **not** alter the triad's derivation.

The reported **bottleneck** is stated per lens: L's weakest module (the plumbing constraint) and C's
weakest module (the proposition constraint). They are **not** merged into one ranking while C sits
outside V.

## 13. Customer Proposition (C) — new

### 13.1 Purpose
C scores the front-of-house proposition — the quality, completeness and differentiation of what the
customer actually experiences. It is the dimension carrying 80–100% of the weight in every published
brokerage methodology, and the lens that makes the B/P/L diagnosis legible to a client
("weak charting → single-sourced market data → high cost-to-serve").

### 13.2 Modules (Phase E)
Ten modules, from the Brokerage App World Cup Phase E criteria — the categories the existing review
corpus is already scored against. Each rolls up to `q_c,m` and thence to C **by the L aggregation
path (§5.2)**: bottleneck-aware, rating-gated, with `NOT_APPLICABLE`/`NOT_ASSESSED` renormalisation.

| Module | Scope |
|---|---|
| `CUST_ONBOARDING` | ease, speed, clarity, KYC burden, time-to-funded |
| `CUST_UI_NAVIGATION` | layout logic, visual design, accessibility, customisation |
| `CUST_TRADING_EXPERIENCE` | order types, execution flow, fee transparency, real-time feedback |
| `CUST_PRODUCT_RANGE` | asset classes, fractional, global vs local access, wrappers (GIA/ISA/LISA/JISA/SIPP) |
| `CUST_RESEARCH_EDUCATION` | market-data depth, education quality, interactive tools |
| `CUST_AI_PERSONALISATION` | AI recommendations, chatbots, personalised content |
| `CUST_SECURITY_REGULATION` | investor protection (FSCS/SIPC/ICF), authentication, compliance |
| `CUST_SUPPORT_COMMUNITY` | support availability/quality, social features |
| `CUST_FEES_PRICING` | commissions, spreads, **FX fees**, subscriptions, inactivity fees, TCO bands |
| `CUST_INNOVATION_DIFFERENTIATORS` | social trading, gamification, referrals, direct custody |

### 13.3 Level-1 data: the widget checklist
- The **93-widget × 15-category** checklist is C's Level-1 evidence, mapped into the 10 modules.
  Per widget: **Present (Y/N)** · **Ease-to-find (1–5)** · **Usability (1–5)** · **Depth (1–5)** ·
  Notes. Captured in-app, so C evidence is **E3/E4 by construction**.
- **Rarity is the differentiation weight.** Each widget carries **Common / Uncommon / Rare** from the
  brief's annex: a **missing Common** widget is a proposition bottleneck; a **Rare** widget done well
  scores differentiation. A flat coverage-% is **not** a valid C score.
- **Scope ≠ execution.** A capability the firm deliberately does not offer is `NOT_APPLICABLE` and
  renormalises out — a deliberately focused app is not penalised for positioning. Absence is noted,
  not automatically punished.
- **Presence states.** Beyond Present / `NOT_APPLICABLE` / `NOT_ASSESSED`, a capability may be
  **`PRESENT_PAYWALLED`** (exists but gated) or **`PRESENT_DEFECTIVE`** (exists but broken). These are
  first-class states, never defaulted to Present (ADR-0001 fail-loud).
- The subcomponent's **maturity level (Basic→Frontier) remains the assessor's rating**, informed by
  the rarity-weighted, scope-adjusted widget roll-up — the roll-up does not replace the rating.

### 13.4 Uncertainty, governance, profiles
- **Uncertainty (§7) applies unchanged:** C and each C-module carry P10/P50/P90 ranges and an
  Assessment Uncertainty Rating, driven by evidence grades and coverage.
- **Governance:** C ratings are subject to §4 rubric anchors, §9 dual-rating and rating-committee
  gates, identically to L. **Frontier is not the target** — each C anchor states which firm
  archetypes rationally need it.
- **Profiles:** this widget taxonomy is the **retail-brokerage** profile's C instrument. Other
  operating models (exchange, wealth, infrastructure vendor — `METHODOLOGY-V2-SCOPE` §2) require
  their own C instrument; an exchange's customers are members and issuers, not retail investors.

---

## Sections unchanged from v1.2 / v1.1

§1 (Purpose & Status), §3.3 & §7 (Uncertainty — as amended in v1.2, applied to C), §4 (Rubric
Anchors — extended with C anchors, same §4 template), **§5.1 (Composite — untouched in v1.3)**, §5.2
(L aggregation & gate — reused by C), §5.3 (group-weighted B), §5.4, §6 (Coefficient Provenance —
gains C-internal weights and, at v1.4, θ_C), §8 (Seven Powers), §9 (Certification & Calibration),
§10 (Value Bridge — extends to C upgrades), §11 (Validation Loop), §12 (Method Sources) are carried
forward from `docs/ATLAS-Methodology-v1.2.md` and `-v1.1.md`.
