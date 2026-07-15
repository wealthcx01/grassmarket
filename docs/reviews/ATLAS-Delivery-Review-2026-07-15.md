# ATLAS / Advisor Studio — Delivery Review vs. Product Briefs

**Date:** 2026-07-15
**Reviewer:** Claude — audit of live production + repo, cross-examined against the OneDrive product briefs and the ratified PRD/Methodology.
**Questions asked:** Is the delivered product faithful to what we laid out? Why can't we assess the brokerage's *widgets* or a *Customer Proposition Index*? What's required before we onboard advisors?

## Verdict in one paragraph
Two different things are true at once. **(1) Against the *ratified* spec, the build is faithful and clean.** The PRD (v2), Methodology (v1.2) and "How It Works" define exactly **B / P / L / V** — 10 business metrics, 7 Helmer powers, 9 infrastructure modules / 51 subcomponents — and that is what shipped, with the fail-loud discipline intact and (now) a complete 204-anchor rubric. **Nothing in the ratified scope is missing.** **(2) But the product you *want* — one that also assesses the customer-facing proposition and the app's widgets — was written down as a P1 proposal and never ratified, so it was never built.** The Customer Proposition Index (C) and the 93-widget taxonomy are **not** in the PRD or Methodology; they live in the `ATLAS Golden Master — Suggested Changes` doc (a proposal) and in a *separate* "Brokerage App World Cup" review project. So the honest answer is: this isn't a build failure — it's a **scope decision that was never taken**. Combined with a wizard that delivers the *mechanics* but not the *guided consulting experience* the UX brief calls for, my recommendation is: **don't onboard advisors yet** — take the C/widget scope decision and close the UX gaps first.

---

## 1. What I audited, and against what
**Delivered:** live site (dashboard, onboarding tour, `/guide`, login; wizard walked end-to-end to a live score in a prior session); engine (`src/grassmarket/atlas/engine.py`); registry (`packages/bcap_contracts/.../registry_data/{modules,metrics,powers}.yaml`).
**Ratified spec:** `docs/Grassmarket-PRD-v2.md`, `docs/ATLAS-Methodology-v1.2.md`, `…/Technology/ATLAS Assessment - How It Works.md`.
**Proposals & prior work:** `…/Technology/ATLAS Golden Master — Suggested Changes.md`; `atlas_wizard_user_experience.md` + `atlas_wizard_wireframes.md`; the "Brokerage App World Cup" reviews under `…/Briefing/Content-Bank/Projects/Brokerage-App-Reviews/`.

---

## 2. Delivered scope (precise) — and it matches the ratified spec
**V = θ_B·B + θ_P·P + θ_L·L** (`engine.py:76–78`; θ = 0.25/0.35/0.40; **no θ_C**).

| Index | Delivered | Ratified spec says |
|---|---|---|
| **B** | 10 metrics, grouped scale / unit-economics / momentum | ✅ same |
| **P** | 7 Helmer powers, Benefit+Barrier (None→Wide) + evidence grade | ✅ same |
| **L** | 9 modules, 51 subcomponents, Basic→Frontier + E1–E4 | ✅ same |
| **Outputs** | V/L/B/P **ranges**, Platform-Power triad (words), bottleneck, coverage, uncertainty rating, UPI scenario ranking | ✅ same |

**This is a correct, disciplined implementation of the ratified methodology.** Several `Suggested Changes` items were even folded in (B grouped into scale/unit-economics/momentum; `TAKE_RATE_LEVEL` renamed; the 204-anchor rubric completed). Do not read the rest of this review as "the engine is wrong" — it isn't.

---

## 3. The customer-proposition layer you want is a **proposed expansion, never ratified** (so never built)

You're right that it's missing — and right that it *should* exist. But it is missing from the *ratified* scope on purpose-by-omission, not by build error. The distinction matters for how we fix it (a **methodology amendment + ADR**, per CLAUDE.md non-negotiable #2 — not a silent code add).

### 3.1 Customer Proposition Index (C)  — `Suggested Changes §C1 (P1)`; **not in PRD/Methodology**
The proposal is **V = θ_B·B + θ_P·P + θ_L·L + θ_C·C**, with **C = 6 modules**: Costs & Value · Safety & Protection · Range & Wrappers · Trading & Execution · Experience & Support · Research & Education. Rationale (quoting the proposal): *"ATLAS scores the plumbing (L), the economics (B) and the moat (P), but has no index for the customer proposition — fees, safety, investment range, wrappers, UX, service — which is 80–100% of the weight in every published methodology."* The unique product is B/P/L **connected to C** ("weak charting → single-sourced market-data vendor → high cost-to-serve"). **Status: absent** — no `theta_c`, no C modules, no wizard step.

### 3.2 The widget taxonomy — "assess all the widgets they have"  — `Suggested Changes §C2 (P1)`; **separate project, not in ATLAS**
This is a real, mature instrument — but it lives in the **"Brokerage App World Cup"** project, not ATLAS. Concrete structure (verified from the completed `_Claude` checklists):
- **15 categories:** Alerts & Notification · Onboarding & Compliance · Market Overview · Market Monitoring & Watchlist · Trading & Order · FX & Fixed-Income · Mutual Fund & ETF · Research & Analytical Tools · Social & Community · AI & Automation · Order & Risk Management · Account & Cash Management · Support & Education · Customisation & Gamification · Mobile-Specific Widgets.
- **93 widgets** total, each scored: **Present (Y/N)** · **Ease-to-find (1–5)** · **Usability (1–5)** · **Depth (1–5)** · Notes, rolled up to per-category coverage % + avg usability/depth (e.g. Saxo 61/93 = 65.6%; IBKR 76/93 = 82%).
- **Rarity (Common/Uncommon/Rare)** and **scope-vs-execution** separation are intended weights; canonical set is the **March 2026 "_Claude"** files. (Rarity is prose in the completed scorings; the structured rarity columns are in the online-only `*Widget Checklist.docx` templates — open those to import exact tags.)
- **Files:** `…/Briefing/Content-Bank/Projects/Brokerage-App-Reviews/{Saxo,IBKR,Lightyear,Revolut,Trading212,WeBull,HargreavesLansdown}/…_WidgetChecklist_COMPLETED_Claude.md` (7 apps already scored).

In ATLAS today the entire product surface is a **single** subcomponent (`MARKET_DATA → Widgets / AI / Video Services`, one Basic→Frontier rating). That's why it feels "completely missing." The taxonomy is the natural **evidence layer for the C-index** (and partly for L-FRONTEND).

### 3.3 Consumer Duty & Behavioural Design  — `Suggested Changes §C3 (P1)`; **not in scope**
FCA four-outcomes mapping + a Digital-Engagement-Practices inventory (confetti/streaks/leaderboards/push-defaults — the FCA found these raise trade counts 11–12%) + positive/exit frictions. A UK differentiator no commercial reviewer scores. **Status: absent.**

*(Also proposed, not built: knockout gates C4, persona-weighted views C5, dual-layer `PRESENT_PAYWALLED`/`PRESENT_DEFECTIVE` states C6, VoC proxies C7, disclosure-boundary flags C8.)*

---

## 4. UI/UX — the mechanics shipped; the *guided consulting experience* did not
The overnight pass made it clean and on-brand. But the `atlas_wizard_user_experience.md` brief specifies a **"guided consulting workflow,"** and the delivered wizard is a **bare data-entry form**. Gaps (all quote-backed from the UX brief):

| Intended (UX brief) | Delivered | Why an advisor feels it's "off" |
|---|---|---|
| **"Your Brokerages" home** — table with Country, Segment, **Last Score**, Last Updated; brokerage-detail tabs | Generic section launcher; assessments list is subject-only | No portfolio, no book-of-business, no "where's the value" |
| **Structured create** — Country, **Segment (Retail/Wealth/Institutional)**, Model Version | Single "subject (business name)" field | Assessments aren't typed/segmented; blocks later persona weighting |
| **Step-1 Business Profile** — asset-class chips, regions, regulatory footprint | "Overview" = subject + free-text notes | No structured context to anchor B or scope N/A modules |
| **Guided power cards** — plain-English summary, **brokerage examples**, notes, "if unsure start at 3–5" | 7 rows of Benefit/Barrier/grade dropdowns, no help | The step the guide says advisors get wrong most often has **zero in-context help** |
| **Tooltips / helper prompts everywhere**; confidence explained | None (raw labels like `unit_economics`) | Reads like an internal spreadsheet |
| **Summary visuals** — **radar** of module q_m, **B→P→L→V waterfall**, module table with **contribution to L + upgrade sensitivity κ_m** | Numeric bands + text module list (bottleneck added) | The diagnostic "aha" is never *shown* |
| **Scenario visuals** — bar chart of impact by module, ranked opportunities | Add-scenario + ΔV list, no charts | Prioritisation story doesn't land |
| **Post-completion analytics** — L-vs-V over time, module-health progression, cross-brokerage comparison, versioning | None | Nothing to return to |

**Two important caveats so we don't "fix" the right things wrongly:**
- The delivered **Benefit/Barrier** power model and the **UPI (ΔV ranking)** are *more correct* than the wizard drafts, which still show a **0–10 power slider** and a **Step-7 "ROI" formula** — both **explicitly retired** by the Methodology (score×£ is a "category error"). **Do not implement the drafts literally.** Keep benefit/barrier + UPI + the value-bridge; add the *guidance and visuals*.
- The delivered **uncertainty ranges (P10/P50/P90)** are correct and *ahead* of the drafts (which show single numbers). Keep them.

So the UX work is: **add guidance (per-power context, tooltips, business-profile step), add the diagnostic visuals (radar/waterfall/module table), and make the home a brokerage portfolio** — not a re-architecture.

---

## 5. Workflow blockers (found live, still open)
1. **Engagement → assessment linking is impossible.** No API attaches an assessment to an existing engagement (`assessment_ids` is set only at engagement-open time), so contracted-engagement → assessment → deliverable **can't complete in the UI** and deliverables never generate. Needs a backend endpoint.
2. **A solo advisor can't finish.** Finalise is gated on dual-rating consensus + committee (correct per methodology) with **no in-UI path** to assign a second rater or run the committee — the advisor hits a wall after scoring. Onboarding needs either a seeded governance flow or a labelled sandbox/solo path.

---

## 6. What's required before we onboard advisors — prioritized

**P0 — strategic scope decision (take it now)**
1. **Decide whether ATLAS assesses the customer proposition.** If yes (recommended — it's the industry-standard lens and the 10x differentiator), it's a **Methodology amendment (v1.3?) + ADR**, then: add `θ_C` + the 6 C modules to the registry, a wizard C-step, and a golden-master v2 fixture. This is the biggest single decision gating "is this the product we promised."
2. **Adopt the widget taxonomy as the C / front-end evidence layer** — import the 93×15 "_Claude" instrument (Present/Ease/Usability/Depth + rarity + scope-vs-execution N/A renormalisation). This is literally "assess all the widgets."

**P1 — needed for advisors to succeed with what exists**
3. **Unblock the core workflow** — engagement→assessment link endpoint + CTA; a usable finalise path (second-rater/committee) or an explicit solo/sandbox mode.
4. **Turn the wizard into guided consulting** — per-power explanation + brokerage examples + notes; a structured Step-1 business profile; tooltips/helper prompts; confidence explained. (Keep benefit/barrier + UPI + uncertainty.)
5. **Show the diagnostic** — radar + waterfall + module table (κ_m) on Summary; scenario impact chart. This is most of "UI/UX feels off."
6. **Brokerage-portfolio home** — "Your Brokerages" with last score / segment / updated as the default authenticated landing.

**P2 — depth, once the above lands**
7. Consumer Duty module (C3), persona-weighted views (C5), knockout gates (C4), dual-layer PRESENT states (C6), post-completion analytics/versioning.
8. Re-verify two engine items from the `Suggested Changes` §A against the shipped engine: **A1** empty-module renormalisation (the old "empty = 0" bug) and **A2** whether the rating gate can ever emit **Basic**.

---

## 7. Bottom line
The engineering is sound and faithful to the **ratified** methodology — this is a well-built producer-side diagnostic with a clean new skin and a complete rubric. What's missing is a **decision and its build-out**, not a correction: the **customer-proposition index and its widget evidence layer** — proposed as P1, backed by seven real app reviews, and standard in every commercial methodology — were never ratified into ATLAS, so the product today assesses the *producer* but not the *proposition*. Add that (P0), unblock the workflow and turn the wizard into the guided, visual consulting experience the UX brief describes (P1), and this becomes the advisor product we scoped. Until then, hold onboarding.

---

## Appendix A — delivered scope
- **B (10):** AUA, ACTIVE_CLIENTS, NET_REVENUE, REVENUE_PER_CLIENT, GROSS_MARGIN, COST_TO_SERVE, TAKE_RATE_LEVEL, NET_REVENUE_RETENTION, CLIENT_GROWTH_RATE, CAC_PAYBACK_MONTHS.
- **P (7):** Scale Economies, Network Economies, Counter-Positioning, Switching Costs, Branding, Cornered Resource, Process Power.
- **L (9 / 51):** Front End(6), App Server(7), Market Data(7), Orchestration(5), CMS(6), Back Office(6), OEMS(6), EMS Gateway(4), Liquidity & Connectivity(4). Critical modules for the L bottleneck: App Server, Back Office, OEMS.
- **V = θ_B·B + θ_P·P + θ_L·L**, θ = 0.25/0.35/0.40 (elicited). No C term.

## Appendix B — widget taxonomy (import source)
`…/Briefing/Content-Bank/Projects/Brokerage-App-Reviews/` — 7 apps (Saxo, IBKR, Lightyear, Revolut, Trading212, WeBull, Hargreaves Lansdown). Canonical = `*WidgetChecklist_COMPLETED_Claude.md` (March 2026, "Claude Code Analysis"). 15 categories × 93 widgets; Present(Y/N) + Ease/Usability/Depth (1–5) + Notes; rarity Common/Uncommon/Rare (structured columns in the online-only `*Widget Checklist.docx` templates). Lesson from the project: screen-recordings alone under-score (Jan Saxo 22% vs March 65.6%) — the March "_Claude" set is canonical.

## Appendix C — caveats for whoever builds this
- **Wizard drafts are partly stale.** `atlas_wizard_user_experience.md`/`wireframes.md` (Dec 2025) still specify a **0–10 power slider** and a **Step-7 ROI** formula — both **retired** by the current Methodology (ordinal Benefit/Barrier; UPI + three-layer value bridge; score×£ unrepresentable). Build the *guidance & visuals* from the drafts, not the slider/ROI.
- **Methodology version nuance:** v1.2 changes **only** §3.3/§7 (uncertainty). Deterministic scores (§5), the CoefficientSet, and the golden master keep the **1.1** stamp and are byte-identical — don't treat "v1.2" as a wholesale re-score.
- **Golden master is `draft-pending-ratification`** with two open items (gate "Basic" unreachable; floor rule stricter than the Methodology text) — settle these when C is ratified.

## Appendix D — sources
`ATLAS Golden Master — Suggested Changes.md`; `atlas_wizard_user_experience.md`; `atlas_wizard_wireframes.md`; `ATLAS Assessment - How It Works.md`; `docs/Grassmarket-PRD-v2.md`; `docs/ATLAS-Methodology-v1.2.md`; Brokerage-App-Reviews `_Claude` checklists; prototype `PRD_COMPLIANCE_REVIEW.md` / `UI_UX_AUDIT_REPORT.md`; repo `engine.py` + registry YAML; live production site.
