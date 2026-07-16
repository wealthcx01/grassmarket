# Grassmarket — Consolidated Next Steps (July 2026)

**Purpose.** One place that binds the threads currently scattered across a business-estate sweep, a
deferred-methodology note, a review corpus in the Briefing pillar, and a fresh delivery review — so
the next phase is a sequenced plan rather than four parallel conversations.

**What this binds**

| Source | What it contributes |
|---|---|
| `ESTATE-RECONCILIATION.md` | Sweep of the OneDrive business folders vs. the build — commission v7, real deliverable types, exchange reality, CRM lifecycle, Workbench content gaps |
| `METHODOLOGY-V2-SCOPE.md` | The deferred v2 agenda: **C-index**, **operating-model profiles**, the **widgets** aspiration |
| `reviews/ATLAS-Delivery-Review-2026-07-15.md` | Live audit: delivered-vs-ratified scope, UI/UX gaps, workflow blockers |
| `adr/ADR-0023` + `ATLAS-Methodology-v1.3.md` (draft) | The C-index decision + staged amendment |
| `Briefing\Content-Bank\Projects\Brokerage-App-Reviews` | The C evidence + benchmark corpus (**16 apps, 7 scored, 93 widgets**) |
| `BACKLOG.md` | Ticket index (**stale** — see §6) |

> **Rule carried over from the estate sweep:** no client data is copied into this repo. These are
> references; ingestion happens as config/seed through the app's scoped storage, never committed files.

---

## 1. Where we are

- **Loops 0–6 shipped** (GRS-0001–0034): scaffold, ATLAS engine to Methodology v1.1/v1.2, wizard Path A, pipeline, deliverable builder, Workbench + governance, earnings, Path B, hardening, launch-readiness.
- **Since then**, a UI/UX + onboarding series has landed (≈GRS-0035–0065): the Claude-aligned design system, `/guide` primer, first-run walkthrough, earnings page, engagement→assessment linking, live-score bottleneck + module breakdown.
- **Rubric library complete** — all 204 anchors authored (was the repeatability bottleneck).
- **The engine is faithful to the ratified spec.** V = θ_B·B + θ_P·P + θ_L·L, 9 modules / 51 subcomponents. Nothing in the ratified scope is missing.
- **Not yet launched to advisors.** The blockers are below.

---

## 2. The product gap: ATLAS scores the producer, not the proposition

This is the headline finding and the reason onboarding should wait.

- ATLAS assesses **B/P/L** (economics, moat, plumbing). It does **not** assess what a customer experiences — fees, safety, range, execution, UX, support — which is **80–100% of the weight in every published brokerage methodology**.
- This was a **deliberate deferral**, not an oversight: C was proposed and parked at the GRS-0003 golden-master review and preserved in `METHODOLOGY-V2-SCOPE` §1. The delivery review re-raised it as the P0 product gap.
- **The evidence already exists, and it's bigger than the note assumed:** the Brokerage-App-Reviews corpus is **16 platforms**, **7 fully scored** (Saxo, IBKR, Lightyear, Revolut, Trading212, WeBull, Hargreaves Lansdown) against a **93-widget × 15-category** instrument (Present · Ease · Usability · Depth 1–5, each widget tagged **Common/Uncommon/Rare**). Worked: IBKR 82%, Saxo 65.6%, Revolut 58%, WeBull 50.5%, Lightyear 41.9%.
- **The flywheel:** those reviews *are* the benchmark corpus. C can launch with **peer-relative benchmarking already populated** — 7 platforms before the first paid C engagement, 9 more with evidence captured awaiting scoring. Each review is dual-use (thought leadership + benchmark row), the same pattern as calibration vignettes doubling as Practice Arena content.
- **Decision + amendment drafted:** `ADR-0023` (Proposed) adopts the **Phase E 10-module set** (the categories the corpus is already scored against) and a **staged entry**: v1.3 reports C *alongside* V (composite untouched, golden master survives) → v1.4 folds C into V after θ re-elicitation.
- **"Assess all the widgets" is resolved:** the widget checklist is **C's Level-1 data**, rarity-weighted, with scope separated from execution. The lone L subcomponent (`MARKET_DATA_VALUE_ADD_SERVICES`) stays — it assesses the *infrastructure to deliver* value-add services; C assesses the services *as experienced*.

---

## 3. The other open threads (from the estate sweep)

| # | Thread | State | Action |
|---|---|---|---|
| 3.1 | **Earnings must encode Commission Schedule v7** | The v7 template is the *decided* model, not an open item: Stream A product commission (per-product Yr1/Yr2 rates + dated windows), Stream B consultancy (sourcing × delivery-type matrix, pay-when-paid, uncapped). GRS-0028 shipped against a **placeholder** assumption. | Verify the shipped earnings config schema covers two streams, Yr1/Yr2 tiers, dated windows, the sourcing×delivery matrix and pay-when-paid. **Ticket the delta.** Seed config from v7. |
| 3.2 | **Deliverable types: PRD ≠ practice** | Real house output is **Outside Read Deck, Note, Primer, Strategic Assessment / 7 Powers Brief** (ASX, NSI packs). The PRD's seven types don't include these. | New ticket: add house deliverable types as builder templates; harvest structure/house style from the ASX/NSI packs (reference only). Check "Workshop Output" against the real Outside Read pattern. Same packs are the best **vignette/case-study source** — anonymise first. |
| 3.3 | **Operating-model profiles — exchange first** | The 9-module L taxonomy is brokerage-shaped; exchanges are assessed today by marking subcomponents N/A (legitimate but stretched). The active book is **exchange-side (ASX, NSE)** — revenue reality answers the scope note's open question. | Promote the **exchange profile** from v2-nice-to-have to **early-v2**, plausibly *ahead of* C. Needs its own ADR (profile = module selection + criticals + weight set per operating model). |
| 3.4 | **Pipeline/CRM should mirror the real lifecycle** | Real flow: Proposal (versioned GTM decks + internal strategy + adversarial critique) → MSA + Engagement Schedule (versioned → executed) → Active → Deliverables. | Verify GRS-0011–0013's stage model accommodates contract documents (MSA/ES versions, executed dates) and the internal-strategy + critique pattern. Seed the real book at cutover (operator task; production only, never fixtures). |
| 3.5 | **Workbench content: seeds exist, library doesn't** | Onboarding kit + Challenger Sales summary exist. **Power Primers (the Power Drills quiz source) are NOT written** — specified in the Foundation Package v3 SOW. | Content-authoring dependency for GRS-0024's quiz bank, alongside vignettes. Founder track. |
| 3.6 | **UI/UX: mechanics without the guided consulting** | The design pass made it clean, but the wizard is data-entry, not the *"guided consulting workflow"* the UX brief specifies. | Per-power explanations + brokerage examples + notes; structured Step-1 business profile (segment/regions/asset classes/licensing); tooltips; **diagnostic visuals** (radar of module q_m, B→P→L→V waterfall, module table with κ_m); **"Your Brokerages" portfolio home**. ⚠️ Build the *guidance and visuals* from the UX drafts — **not** their 0–10 power slider or Step-7 ROI, both **retired** by the methodology. |
| 3.7 | **Datasets** | Widget checklists → C benchmark corpus (§2). Regulatory Filing Database v3 → candidate reference dataset for the knowledge base. | Fold the first into Loop 7; park the second for Holy Corner phase. |

**Confirmed absences (useful negatives, from the sweep):** CPI/Holy Corner/Viewforth have no textual presence in the business folders — build-internal concepts. Several OneDrive scaffolds are empty; nothing to harvest.

---

## 4. Decisions required from the founder (blocking)

| # | Decision | Blocks | Recommendation |
|---|---|---|---|
| 1 | **Ratify the C module set** — Phase E 10 vs. the 6-module industry synthesis | ADR-0023 → v1.3 normative → Loop 7 | **Phase E 10.** The corpus is already scored against it; the 6-set forces a re-score and drops AI & personalisation + Innovation. |
| 2 | **Confirm staged C entry** — report alongside V (v1.3) then into V (v1.4), vs. straight to a fourth θ | ADR-0023 | **Staged.** Keeps §5.1, the `1.1` stamp and the ratified golden master intact until we have real C evidence. |
| 3 | **Sequence: exchange profile vs. C-index first** | Loop 7 scope | **Exchange profile first or in parallel** — the active book (ASX, NSE) is exchange-side today; C's retail widget instrument doesn't apply to exchanges anyway. |
| 4 | **Confirm v7 as the earnings config source** (or supersede) | Earnings delta ticket | Confirm; the placeholder is known-wrong. |
| 5 | **Approve harvesting ASX/NSI pack structure** as deliverable templates (anonymised) | Deliverable-types ticket | Approve. |
| 6 | **Commission the Power Primers** (Foundation Package strand 1, unwritten) | GRS-0024 quiz bank | Commission; it's a content dependency with no code workaround. |
| 7 | **θ re-elicitation panel** — share a session with the v1 annual re-elicitation? | v1.4 (θ_C), GRS-0033 cadence | Share the session. |

---

## 5. Sequenced plan

**Now — costless / no decision needed**
1. Bring the binder docs into git (this PR) so the agenda stops living on one laptop.
2. Briefing continues the review cadence — **score the 9 captured-but-unscored apps** (Capital, Charles Schwab, EFG Hermes, EasyEquities, Futu, Hapi, Robinhood, Trii, eToro) on the existing 93-widget instrument. Every one is a future benchmark row; this is the cheapest C groundwork available.
3. Close the delivery review's **P1 UI/UX** items (§3.6) — they need no methodology decision.
4. Verify the **earnings v7 delta** (§3.1) and ticket it.

**On decisions 1–3 — the next loop**
5. **Loop 7 (GRS-01xx):** C registry (10 Phase-E modules + 93 widget subcomponents + rarity tags) · C rubric anchors seeded from the 7 completed checklists · wizard C-step · benchmark ingestion of the corpus (approval-gated per ADR-0009) · deliverable sections (proposition heatmap, differentiation-vs-rarity map) · C reported alongside V.
6. **Profile ADR + exchange profile** (§3.3) — likely ahead of or beside Loop 7, per the active book.
7. **v1.4:** θ re-elicitation across four lenses → C enters V → **golden-master v2**.

**Onboarding gate.** Advisors can be onboarded once: (a) the guided-consulting UI/UX items land, (b) the workflow is unblocked end-to-end (contract → assessment → deliverable), and (c) either C ships or we consciously position the first cohort as *infrastructure diligence only*. **(c) is a positioning decision, not a technical one** — worth taking explicitly rather than by default.

---

## 6. Corrections to existing docs (do these when merging)

- **`METHODOLOGY-V2-SCOPE.md` is stale on the corpus:** it records a *"~70-widget checklist"* and *7 platforms*. The live instrument is **93 widgets**; the corpus is **16 platforms, 7 scored**. Its §1 and §3 are otherwise superseded by ADR-0023 (§2 profiles remains live and needs its own ADR).
- **`BACKLOG.md` is stale:** it lists GRS-0016–0034 as `Planned`; they have shipped, and the series now runs past GRS-0065. It has no Loop 7. Refresh the index and add the Loop 7 / profile threads.
- **`ATLAS-Methodology-v1.3.md` is DRAFT** — not normative until ADR-0023's decisions 1–2 are taken.

## 7. Document map

| Doc | Role |
|---|---|
| `ATLAS-Methodology-v1.2.md` | **Normative today** |
| `ATLAS-Methodology-v1.3.md` | Draft — adds C (reported), pending ADR-0023 |
| `adr/ADR-0023-customer-proposition-index.md` | The C decision (Proposed) |
| `METHODOLOGY-V2-SCOPE.md` | v2 agenda — §1/§3 superseded by ADR-0023; **§2 (profiles) still live** |
| `ESTATE-RECONCILIATION.md` | Business-estate sweep → the §3 threads here |
| `reviews/ATLAS-Delivery-Review-2026-07-15.md` | Delivered-vs-ratified + UI/UX audit |
| `NEXT-STEPS-2026-07.md` | **This doc — the binder** |
| `planning/PART1-oauth-earnings-profiles-cindex.md` | Part 1 execution plan — GRS-0073–0086 (on `main`) |
| `planning/PART2-uiux-review.md` | Part 2 execution plan — section-by-section UI/UX review → GRS-0087–0134 + ADR-0027–0030 |
| `BACKLOG.md` | Ticket index (needs refresh) |
| `Advisor-Guide-to-ATLAS.md` / `ATLAS-Methodology-Guide.md` | Advisor-facing guide + formal foundations |
