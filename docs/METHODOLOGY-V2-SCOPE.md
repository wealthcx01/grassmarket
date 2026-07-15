# ATLAS Methodology v2 — Scope Note

**Status: agreed direction, not yet normative.** This document captures the three deferred extensions to ATLAS so they survive as a deliberate v2 agenda rather than scattered fragments (a ticket footnote, a registry line, an N/A workaround). Nothing here changes v1.x behaviour; each item lands via the standard ADR + methodology-version process when scheduled.

> **Corpus figures corrected (GRS-0066, 2026-07-15).** This note was written against an early read of the review corpus. The live instrument is **93 widgets × 15 categories** (not "~70"), and the corpus is **16 app folders, 7 fully scored** (Saxo, IBKR, Lightyear, Revolut, Trading212, WeBull, Hargreaves Lansdown) with 9 more captured-but-unscored — not "7 platforms" total. Where the numbers below say "~70" or imply seven is the corpus size, read 93 / 16 (7 scored). §1 and §3 of this note are otherwise **superseded by `adr/ADR-0023`**; §2 (operating-model profiles) stays live and gets its own ADR. Full accounting: `NEXT-STEPS-2026-07.md` §2/§6 and ADR-0023 §Context.

Provenance: the C-index was proposed and deferred during the GRS-0003 golden-master review ("deferred to Methodology v2 / a new loop, per John"). Its source material is the Briefing pillar's Brokerage-App-Reviews project (`OneDrive\...\Business\Briefing\Content-Bank\Projects\Brokerage-App-Reviews`): the Brokerage App World Cup 2026 brief, the 93-widget checklist annex (15 categories, each widget tagged Common/Uncommon/Rare), completed widget checklists for Trading212, Saxo, Revolut, WeBull, IBKR, Lightyear and Hargreaves Lansdown (7 scored of 16 captured), and the Phase E scoring matrix whose weightings were explicitly left "to be determined collaboratively later."

---

## 1. C — The Customer Proposition Index (fourth lens)

**What it is.** ATLAS v1 assesses what the business achieves (B), why it's defensible (P), and whether the plumbing can carry it (L). None of these directly assesses **what the customer actually experiences** — the front-of-house proposition. C fills that gap: the quality, completeness and differentiation of the customer-facing product.

**The instrument already exists in draft.** The World Cup brief's methodology maps almost one-to-one onto ATLAS discipline:

| World Cup artefact | ATLAS v2 equivalent |
|---|---|
| Widget checklist (93 widgets, 15 categories) | C-index subcomponent registry — presence, usability, depth, customisation, integration, regional relevance per widget group |
| Common / Uncommon / Rare tags | Differentiation weighting: a Rare widget done well scores differentiation; a missing Common widget is a proposition bottleneck |
| Phase E categories (onboarding, UI/UX, trading experience, product range, research/education, AI & personalisation, security, support, fees, innovation) | C-index module set (~10 modules), same two-track scoring as L: continuous score + rating gate |
| Novice-reviewer UX journal (steps, time-to-task, friction) | Evidence artifacts for C ratings (E3-grade by construction) |
| "Note absence, don't penalise" + "weightings determined later" | N/A discipline + elicited weights with provenance — already solved in v1 |

**Model sketch.** C = same aggregation family as L: subcomponents → modules → C, with bottleneck blend and rating gates. V extends to `V = θ_B·B + θ_P·P + θ_L·L + θ_C·C` (Σθ = 1 re-elicited). C also feeds the triad: Perceived Value gains its strongest evidence source (observed customer experience rather than claimed NPS).

**The flywheel point.** Briefing's app reviews *are* the C-index benchmark corpus. Every World Cup review is simultaneously thought-leadership content and an anonymised benchmark row — the same dual-use pattern as calibration vignettes doubling as Practice Arena content. This makes C the first index to launch with peer-relative benchmarking (Stage 2) already populated: 7+ platforms reviewed before the first paid engagement.

**Build implications (when scheduled):** C-registry (modules + widget subcomponents, rarity tags), C-rubrics seeded from the completed checklists, wizard step(s), ingestion path for Briefing review data (approval-gated), benchmark store rows from existing reviews, deliverable sections (proposition heatmap, differentiation map vs. rarity), θ re-elicitation.

## 2. Operating-model profiles (exchanges and beyond)

**Problem.** The 9-module L taxonomy is brokerage-shaped (OEMS, EMS Gateway, Liquidity Connectivity). Today an exchange or pure wealth platform is assessed by marking subcomponents N/A — legitimate but stretched: it silently narrows coverage rather than assessing what an exchange actually runs (matching engine, market surveillance, member connectivity, clearing interfaces, data dissemination).

**v2 answer: assessment profiles, not new frameworks.** A profile = (module/subcomponent selection + additions) × (critical sets) × (weight set) per operating model:

- **Retail brokerage** (v1 default — unchanged)
- **Wealth/advisory platform** (de-emphasise OEMS/EMS; add advice, suitability, portfolio construction depth)
- **Exchange / market infrastructure** (add matching, surveillance, member gateway, clearing/settlement interfaces, market-data distribution as first-class modules)
- **Infrastructure vendor** (the Bruntsfield thesis target: assess the product platform itself plus its multi-tenant delivery capability)

Each profile carries its own elicited weights and criticals with provenance; the registry gains a profile dimension; benchmark populations segment by profile (never compare an exchange's L to a broker's). The C-index inherits the same profile mechanism (an exchange's customers are members and issuers, not retail investors — different widget set entirely).

## 3. Granular experience assessment (the "widgets" aspiration)

v1 carries a single subcomponent (`MARKET_DATA_VALUE_ADD_SERVICES` — "Widgets / AI / Video Services"). The original aspiration was per-widget assessment depth. Resolution: this is absorbed by the C-index (item 1), whose registry is *built from* the widget checklist — per-widget presence/quality/differentiation becomes the C-index's Level-1 data. The lone L-subcomponent stays where it is (it assesses the *infrastructure* to deliver value-add services; C assesses the services as experienced).

## Sequencing

1. **Now (costless):** this scope note lives in the repo; Briefing reviews continue accumulating benchmark-grade data using the existing checklist.
2. **v2 kickoff (post-launch, founder decision):** C-index registry + rubrics drafted from the review corpus; profile mechanism ADR; θ re-elicitation panel (can share a session with the v1 annual re-elicitation).
3. **Build:** a new loop (Loop 7 / GRS-01xx series) — registry extension, wizard step, benchmark ingestion from Briefing, deliverable sections.

## Decisions needed from John before v2 kickoff

- Ratify the C-index module set (start from the Phase E categories?).
- Whether C enters V (fourth θ) or reports alongside V unweighted in its first release (lower-risk staging: report C separately for 2–3 engagements, then elicit θ_C).
- Which profile ships second (exchange vs. wealth) — driven by pipeline reality.
