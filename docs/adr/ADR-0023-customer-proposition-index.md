# ADR-0023 — Customer Proposition Index (C) as ATLAS's fourth index

- **Status:** Accepted (2026-07-15). Ratifies the strategic addition proposed in `ATLAS Golden Master — Suggested Changes` §C1–C2. **θ_C and the C-internal weights remain draft-pending-elicitation** (swing-weighted by the panel, as with B/P/L); the C golden-master fixture (v2) and rubric anchors are follow-on build work.
- **Date:** 2026-07-15
- **Deciders:** Founder + engineering (post-delivery review)
- **Normative source:** `docs/ATLAS-Methodology-v1.3.md` §2 (amended), §5.1 (amended composite), §13 (new).
- **Raised by:** delivery review `docs/reviews/ATLAS-Delivery-Review-2026-07-15.md`; `Suggested Changes` §C1–C3.

## Context

ATLAS as ratified through v1.2 scores the **producer**: economics (B), moat (P), infrastructure (L), composed as `V = θ_B·B + θ_P·P + θ_L·L`. Every published retail-brokerage methodology (StockBrokers 309 variables, BrokerChooser 1,200+ points, Which?, NerdWallet, Finder, Boring Money, …) instead weights the **customer proposition** — fees, safety, range/wrappers, execution, experience, research — at **80–100%** of the score (Which? puts 60% on customer experience; UK frameworks put 27–35% on fees alone). ATLAS is therefore complete as an *infrastructure diligence* tool but silent on the surface a retail client actually experiences.

Two facts make closing this gap low-risk:
1. Bruntsfield already owns a **field-tested evidence instrument** — the "Brokerage App World Cup" **93-widget × 15-category** checklist (Present / Ease-to-find / Usability / Depth 1–5, rarity Common/Uncommon/Rare), with **seven** apps already scored (the March 2026 `_Claude` set is canonical). This is the natural evidence layer for a customer-proposition index and partly for L-FRONTEND.
2. The unique product is B/P/L **connected to C**: "weak charting → single-sourced market-data vendor → high cost-to-serve." No competitor connects the customer surface to the producing infrastructure.

Per CLAUDE.md non-negotiable #2 ("the methodology is settled: implement it, don't re-invent; changes to scoring are ADRs + new methodology versions"), adding a fourth index is a **deterministic methodology change** and must be ratified here, not added silently.

## Decision

**Add C — Customer Proposition — as ATLAS's fourth index**, composed alongside B/P/L:

```
V = θ_B·B + θ_P·P + θ_L·L + θ_C·C        (θ_B + θ_P + θ_L + θ_C = 1)
```

**Structure of C** — 6 modules mirroring industry consensus, each observable largely in-app:

| C module | Indicative subcomponents |
|---|---|
| `CUST_COSTS_VALUE` | dealing commissions; platform fee by wrapper; **FX fee**; spreads; cash interest paid vs retained; subscription-tier value; TCO at £5k/£50k/£250k bands |
| `CUST_SAFETY` | legal entity; FSCS £85k vs EU €20k mapping; CASS/nominee disclosure; 2FA/biometrics/device mgmt; outage history |
| `CUST_RANGE_WRAPPERS` | asset classes; markets; fractional; funds/bonds/options; GIA / ISA (flexible?) / LISA / JISA / SIPP; ISA-allowance tooling |
| `CUST_TRADING_EXECUTION` | order types (trailing/OCO/bracket); extended hours; margin rates; paper trading; execution-disclosure quality; sampled fills / FX markup |
| `CUST_EXPERIENCE_SUPPORT` | onboarding minutes-to-funded; taps-to-trade; UX rubric; notification granularity; timed support mystery-contacts |
| `CUST_RESEARCH_EDUCATION` | data latency (real-time vs 15-min); charting/screeners; third-party research; portfolio analytics & tax reporting; education depth |

**Scoring** reuses the L machinery so the engine stays uniform and fail-loud:
- Each C subcomponent is rated on the **same Basic→Frontier maturity scale** with an **E1–E4 evidence grade** (§3.3), and rolls up to a module quality `q_c,m` and then to `C` exactly as L does (bottleneck-aware, `NOT_APPLICABLE`/`NOT_ASSESSED` renormalisation, ADR-0001/0003). **A firm that deliberately omits a capability marks it `NOT_APPLICABLE` — scope is separated from execution-within-scope**, so a focused low-coverage app (Lightyear) is not punished for positioning.
- The **widget taxonomy is the evidence layer, not a parallel score.** The 93×15 checklist (Present / Ease / Usability / Depth, rarity-weighted) is captured as **structured E4 evidence** attached to the relevant C subcomponents (and to L-FRONTEND where it corroborates); its rolled-up coverage/quality informs the assessor's maturity rating rather than replacing it. Rarity tags weight the roll-up (a Rare yield-curve chart ≠ a Common price alert).
- **Dual-layer presence states** extend the existing states: `PRESENT_PAYWALLED` and `PRESENT_DEFECTIVE` are distinct from Present and from Not-Applicable, so a paywalled order book or a broken data feed is captured honestly (ADR-0001 fail-loud extended, not defaulted).

**Uncertainty (§7) applies unchanged:** C is modelled from its subcomponents' evidence grades exactly like L; C and the C-modules carry P10/P50/P90 ranges and an Assessment Uncertainty Rating.

## Consequences

- **Methodology v1.3** (`docs/ATLAS-Methodology-v1.3.md`) supersedes v1.2: it amends §2 (framework is now B/P/L/**C**), §5.1 (four-term composite + weight renormalisation), and adds §13 (Customer Proposition). Unlike v1.2, **this is a deterministic change** — the composite formula moves, so the ratified golden master must advance to **v2** and re-stamp; v1.1/v1.2 fixtures remain valid for the three-index sub-result.
- **Coefficient elicitation:** the panel must elicit `θ_C` (and re-elicit θ_B/θ_P/θ_L to sum to 1), plus C-internal δ/λ/group weights and the widget rarity weights, with provenance (§6). Until then C ships `draft-pending-ratification` behind a flag, exactly as B/P/L did.
- **Registry + rubric:** add the 6 C modules and their subcomponents to `modules`-style registry data (or a parallel `customer_modules.yaml`), and author their §4 rubric anchors (the Brokerage-App-Reviews scorings are the first anchor mine, per `Suggested Changes` B9/C2).
- **Engine:** `engine.py` composite gains the C term and a C-index computation reusing the L aggregation path; contracts (`bcap_contracts`) gain `theta_c`, a `CustomerResult`, and the `PRESENT_*` states; Monte-Carlo and the value bridge extend to C.
- **Golden-master v2:** synthesise Meridian's customer-proposition profile from the seven real app reviews (validates the widget-taxonomy-as-evidence pipeline in the same step).
- **Deferred to their own ADRs:** Consumer Duty & Behavioural Design module (`Suggested Changes` C3), knockout gates (C4), persona-weighted views (C5), voice-of-customer proxies (C7). C6 (dual-layer presence) is folded in here.

## Alternatives considered

- **Leave ATLAS as a pure infrastructure tool.** Rejected: it omits 80–100% of what every buyer's frame weights, and forfeits the B/P/L↔C connection that is the product's moat.
- **Score the widget taxonomy as a standalone percentage** (as the World Cup project did). Rejected: a flat coverage-% treats rare and common widgets alike and conflates scope with execution — the reasons the `Suggested Changes` doc gives for wiring it in *as evidence under maturity-rated C subcomponents* instead.
- **Fold customer items into the existing L-FRONTEND module.** Rejected: fees/safety/wrappers/service are not infrastructure; burying them in L would distort both indices and hide the customer story the client came for.
