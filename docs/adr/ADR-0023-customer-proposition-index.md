# ADR-0023 — Customer Proposition Index (C): promote from v2 agenda to a scheduled build

- **Status:** **Proposed** (2026-07-15). This ADR promotes `docs/METHODOLOGY-V2-SCOPE.md` §1 (agreed direction, non-normative) into a decision record. **Two founder decisions remain open** (§Decisions required) — until they are taken, `docs/ATLAS-Methodology-v1.3.md` is **draft, not normative**.
- **Date:** 2026-07-15
- **Deciders:** Founder (decisions below) + engineering
- **Normative source (once accepted):** `docs/ATLAS-Methodology-v1.3.md` §13.
- **Supersedes/absorbs:** `METHODOLOGY-V2-SCOPE.md` §1 (C-index) and §3 (the "widgets" aspiration). §2 (operating-model profiles) stays in that note and gets its own ADR.
- **Raised by:** delivery review `docs/reviews/ATLAS-Delivery-Review-2026-07-15.md`; founder feedback that widget assessment and a Customer Proposition Index are missing from the product.

## Context

ATLAS v1.x scores the **producer**: economics (B), moat (P), infrastructure (L) → `V = θ_B·B + θ_P·P + θ_L·L`. It does not score what the customer experiences. This is **not an oversight**: the C-index was proposed and **deliberately deferred by the founder at the GRS-0003 golden-master review** ("deferred to Methodology v2 / a new loop"), and captured in `METHODOLOGY-V2-SCOPE.md` so it survived as an agenda rather than fragments. The 2026-07-15 delivery review re-raised it as the P0 product gap. This ADR schedules it.

**The evidence corpus already exists and is larger than the scope note assumes.** `OneDrive\…\Briefing\Content-Bank\Projects\Brokerage-App-Reviews\`:
- **16 app folders**; **7 fully scored** with completed `_Claude` checklists (Saxo, IBKR, Lightyear, Revolut, Trading212, WeBull, Hargreaves Lansdown); 9 more (Capital, Charles Schwab, EFG Hermes, EasyEquities, Futu, Hapi, Robinhood, Trii, eToro) have captured evidence but no scoring.
- The instrument is **93 widgets × 15 categories** (Present Y/N · Ease-to-find 1–5 · Usability 1–5 · Depth 1–5 · Notes), each widget tagged **Common / Uncommon / Rare** in the brief's annex. Worked results: IBKR 76/93 (82%), Saxo 61/93 (65.6%), Revolut 54/93 (58%), WeBull 47/93 (50.5%), Lightyear 39/93 (41.9%).
- **Correction to `METHODOLOGY-V2-SCOPE.md`:** it records "~70-widget checklist" and 7 platforms — the live instrument is **93 widgets** and the corpus is **16 platforms (7 scored)**. That note should be amended.
- The brief's **Phase E** defines the scoring categories and states *"Final weightings and scores will be determined collaboratively later"* — i.e. the weights were always intended to be elicited, exactly as ATLAS does for θ/λ/δ.

**Why it matters:** every published brokerage methodology weights the customer proposition at 80–100%. The unique Bruntsfield product is B/P/L **connected to C** ("weak charting → single-sourced market-data vendor → high cost-to-serve"). And per the scope note's flywheel: the Briefing reviews *are* the benchmark corpus, so **C can launch with peer-relative benchmarking already populated** — 7 scored platforms before the first paid C engagement.

## Decision

**1. Adopt C as a fourth ATLAS lens, built on the L aggregation family.** Subcomponents → modules → C, with the bottleneck blend, rating gates, `NOT_APPLICABLE`/`NOT_ASSESSED` renormalisation and E1–E4 evidence grades already proven for L. No new scoring machinery.

**2. Module set = the World Cup Phase E categories (10), not the 6-module industry synthesis.** The `ATLAS Golden Master — Suggested Changes` §C1 proposed 6 modules (Costs & Value / Safety & Protection / Range & Wrappers / Trading & Execution / Experience & Support / Research & Education). **Rejected in favour of Phase E** because the 7-app corpus is *already scored against Phase E*, making the benchmark usable on day one; the 6-set would require re-scoring every review. Phase E also preserves two modules the 6-set drops (AI & personalisation; Innovation & differentiators) that are central to the Bruntsfield thesis.

| # | C module (Phase E) | Covers | 6-set equivalent |
|---|---|---|---|
| 1 | `CUST_ONBOARDING` | ease, speed, clarity, KYC burden | Experience & Support |
| 2 | `CUST_UI_NAVIGATION` | layout logic, visual design, accessibility, customisation | Experience & Support |
| 3 | `CUST_TRADING_EXPERIENCE` | order types, execution flow, fee transparency, real-time feedback | Trading & Execution |
| 4 | `CUST_PRODUCT_RANGE` | asset classes, fractional, global vs local market access, wrappers | Range & Wrappers |
| 5 | `CUST_RESEARCH_EDUCATION` | market-data depth, educational quality, interactive tools | Research & Education |
| 6 | `CUST_AI_PERSONALISATION` | AI recommendations, chatbots, personalised content | *(dropped by 6-set)* |
| 7 | `CUST_SECURITY_REGULATION` | investor protection (FSCS/SIPC), authentication, compliance | Safety & Protection |
| 8 | `CUST_SUPPORT_COMMUNITY` | support availability/quality, social features | Experience & Support |
| 9 | `CUST_FEES_PRICING` | commissions, spreads, **FX fees**, subscriptions, inactivity fees | Costs & Value |
| 10 | `CUST_INNOVATION_DIFFERENTIATORS` | social trading, gamification, referrals, direct custody | *(dropped by 6-set)* |

Wrapper/TCO depth from the 6-set (GIA/ISA/LISA/JISA/SIPP, TCO at £5k/£50k/£250k) folds into `CUST_PRODUCT_RANGE` and `CUST_FEES_PRICING` as subcomponents — nothing is lost.

**3. The widget checklist is the Level-1 data for C, not a parallel score.** The 93 widgets map into the 10 modules by their category. Per-widget capture: **Present (Y/N)** + **Ease / Usability / Depth (1–5)**, with **rarity as the differentiation weight** — a missing **Common** widget is a proposition bottleneck; a **Rare** widget done well scores differentiation. **Scope ≠ execution:** a capability the firm deliberately doesn't offer is `NOT_APPLICABLE` and renormalises out, so a focused app (Lightyear 41.9%) is not punished for positioning. This resolves `METHODOLOGY-V2-SCOPE` §3: the "assess all the widgets" aspiration **is** C's Level-1 layer; the lone L subcomponent `MARKET_DATA_VALUE_ADD_SERVICES` **stays** (it assesses the *infrastructure to deliver* value-add services; C assesses the services *as experienced*).

**4. Staged entry into V (the scope note's lower-risk option — adopted).**
- **Stage 1 (Methodology v1.3):** C is defined, scored, gated and **reported alongside V — not inside it**. `V` stays the three-index composite, so **§5.1 is unchanged, the deterministic engine keeps its `1.1` stamp, and the ratified golden master remains valid**. This is additive and reversible.
- **Stage 2 (Methodology v1.4, after 2–3 engagements + θ re-elicitation):** C enters the composite — `V = θ_B·B + θ_P·P + θ_L·L + θ_C·C`, Σθ = 1 **re-elicited together** (the v1.1 θ of 0.25/0.35/0.40 may not simply be reused with a bolted-on θ_C). That is a deterministic change requiring **golden-master v2**.
- An engine with no elicited `θ_C` **must refuse** to emit a four-index V (fail-loud, ADR-0001) — never default `θ_C = 0`.

**5. Presence states extend, not default.** Adds `PRESENT_PAYWALLED` and `PRESENT_DEFECTIVE` alongside Present / `NOT_APPLICABLE` / `NOT_ASSESSED` — a paywalled order book or a broken feed is captured honestly.

**6. Profiles interaction (deferred, but binding).** C inherits the operating-model profile mechanism (`METHODOLOGY-V2-SCOPE` §2): an exchange's customers are members and issuers, not retail investors — **a different widget set entirely**. The retail-brokerage widget taxonomy is the *retail* profile's C instrument only. Given the active book is exchange-side (ASX, NSE — see `ESTATE-RECONCILIATION` §3), the profile ADR should land close behind this one.

## Decisions required from the founder (blocking normative status)

1. **Ratify the Phase E 10-module set** (recommended above) — or select the 6-module synthesis and accept re-scoring the corpus.
2. **Confirm staged entry** (Stage 1 report-alongside → Stage 2 into V) vs. going straight to a fourth θ.
3. *(Related, not blocking)* Confirm the θ_C elicitation panel shares a session with the v1 annual re-elicitation (`BACKLOG` founder track), and whether the **exchange profile** is promoted ahead of C (`ESTATE-RECONCILIATION` §3 argues revenue reality says exchange-first).

## Consequences

- **Methodology v1.3** (draft until accepted) adds §13; **§5.1 composite unchanged** — the golden master and `1.1` deterministic stamp survive Stage 1.
- **New loop (Loop 7 / GRS-01xx)** — the `METHODOLOGY-V2-SCOPE` sequencing stands: C registry (10 modules + 93 widget subcomponents + rarity tags), C rubric anchors seeded from the 7 completed checklists, wizard C-step, benchmark ingestion of the review corpus (approval-gated, per ADR-0009), deliverable sections (proposition heatmap, differentiation-vs-rarity map).
- **Benchmark flywheel:** the 7 scored apps become benchmark rows at launch; the 9 unscored folders are the next content batch — Briefing's cadence feeds the index, and each review is dual-use (thought leadership + benchmark), like calibration vignettes doubling as Practice Arena content.
- **Contracts:** `bcap_contracts` gains a C registry, `CustomerResult`, the `PRESENT_*` states; `theta_c` only at Stage 2.
- **Amend `METHODOLOGY-V2-SCOPE.md`** for the corpus corrections (93 widgets, 16 apps / 7 scored).
- **Deferred to their own ADRs:** operating-model profiles (§2 of the scope note), Consumer Duty & Behavioural Design, knockout gates, persona-weighted views.

## Alternatives considered

- **Leave ATLAS producer-only.** Rejected: forfeits 80–100% of every buyer's frame and the B/P/L↔C connection that is the moat.
- **Score the widget checklist as a standalone coverage-%** (as the World Cup project did). Rejected: flat coverage treats a Rare yield-curve chart like a Common price alert and conflates scope with execution — hence rarity weighting + N/A renormalisation under maturity-rated modules instead.
- **Fold customer items into L-FRONTEND.** Rejected: fees/safety/wrappers/support are not infrastructure; burying them distorts both indices.
- **Go straight to a fourth θ in V.** Rejected for Stage 1: it is a deterministic change that invalidates the ratified golden master before we have a single C engagement's evidence — the scope note's staged option is strictly lower-risk.
