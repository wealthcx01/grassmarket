# Grassmarket Backlog — index

All tickets exist as files in `docs/tickets/` (detail lives there, not here). The builder updates a
ticket's status and appends "What shipped" when its PR lands.

**Loops 0–6 shipped (GRS-0001–0034).** Since then a UI/UX, governance and onboarding series has
landed (GRS-0035–0065), plus an estate-reconciliation + guided-consulting track (GRS-0066–). The
authoritative sequencing narrative is `NEXT-STEPS-2026-07.md` (the binder); this file is just the index.

> **Index freshness (2026-07-30).** This file had drifted: it stopped at GRS-0163 while three
> further programmes — the two-estimator fix, the 2026-07-23 founder-feedback wave, and the
> 2026-07-26 staging-review wave — took the range to GRS-0226. The section immediately below closes
> that gap. Everything from GRS-0173 onward carries the **open-PRs-never-merge holding rule**: work
> lands on its own branch with a PR and is collected on an integration branch for the founder, so
> "In review" here means "built, gated, and waiting on the founder", not "half-done".

## The two-estimator fix (GRS-0164–0172, 2026-07-22) — all shipped

From `reports/staging-rerun-2026-07-22.md`: two different estimators were quoting two different
scores for the same assessment. ADR-0040 made the deterministic composite the one number every
surface quotes.

| Ticket | Title | Status |
|---|---|---|
| GRS-0164 | Surface the Customer-Proposition index (C) alongside V | Done |
| GRS-0165 | Wizard density part 2: C collapse + segmented rating control | Done |
| GRS-0166 | Finalised assessment: wizard rail quotes the locked score | Done |
| GRS-0167 | One-number rule: every surface quotes the deterministic score (ADR-0040) | Done |
| GRS-0168 | Portfolio coverage measured against the assessment's own profile view | Done |
| GRS-0169 | Sell-from-report: segment-scope the catalogue and the gap matcher | Done |
| GRS-0170 | Powers step: unrated ≠ "None", un-rate affordance, one-click chips | Done |
| GRS-0171 | Two-step finalise confirmation | Done |
| GRS-0172 | Trust-polish sweep | Done |

## Founder-feedback wave (GRS-0173–0204, 2026-07-23) — built, in review

| Ticket | Title | Status |
|---|---|---|
| GRS-0173 | Workspace domain SSO — @bruntsfield.capital sign-in (ADR-0044) | In review, PR #206 |
| GRS-0174 | Voice & style guide + application copy sweep | In review, PR #201 |
| GRS-0175 | Guide & Primer rewrite (/help merged into /guide) | In review, PR #208 |
| GRS-0176 | Vertical Kanban for the pipeline | In review, PR #205 |
| GRS-0177 | Portfolio clarity: dedupe, explain, clean | In review, PRs #214/#218 — **the staging cleanup script has not been run** (needs deploy access) |
| GRS-0178 | New-assessment creation form redesign | In review, PR #215 (stacked on 0177) |
| GRS-0179 | `docs/ATLAS-Scoring-Explained.md` — the maths, in English | In review, PR #204 |
| GRS-0180 | 7 Powers mathematics adaptation — normative document | In review, PR #203 |
| GRS-0181 | Wizard pagination: smaller pages per module | In review, PR #216 (stacked on 0182) |
| GRS-0182 | Summary & Interpretation repair (double-V removed) | In review, PR #213 |
| GRS-0183 | Remove ConnectTrade from the catalogue | In review, PR #202 |
| GRS-0184 | Scenario workspace v2 | Planned |
| GRS-0185 | Brandfetch variant segment scoping | In review, PR #217 |
| GRS-0186 | Global navigation + Deliverables reachability | In review, PR #207 |
| GRS-0187 | Consulting commissions on the Earnings page (Stream B) | In review, PR #217 |
| GRS-0188 | The founder review gate (ADR-0041) | In review, PR #219 — retires peer governance; callers repaired |
| GRS-0189 | Rebuild the deliverables to the story architecture | Planned |
| GRS-0190 | Rich lesson renderer + content contracts (ADR-0043) | In review, PR #212 |
| GRS-0191 | Academy content depth program (the 100x) | Superseded — content half became GRS-0215+ |
| GRS-0192 | Content freshness watcher | Planned |
| GRS-0193 | Import the GTM contact databases (ADR-0045) | In review, PR #209 |
| GRS-0194 | LSEG influencer maps via bcap-lseg | In review, PR #211 (stacked on 0193) |
| GRS-0195 | Agentic GTM research spike | Closed — recommendation is BUILD THIN, PR #210 |
| GRS-0196 | Practice Arena v2: an AI client to practise against | Planned |
| GRS-0197 | Gmail + Google Calendar integration | Planned |
| GRS-0198 | Pipeline linkage: assessment & deliverable milestones | Planned |
| GRS-0199 | Bench honesty + Opportunity Radar wiring | Planned |
| GRS-0200 | LSEG influencer dataset: first network-wide pull | Done — dataset produced |
| GRS-0201 | Wizard Powers step: embed the Helmer adaptation | Planned |
| GRS-0202–0204 | Outreach contract / sequencer / send path | Draft, not scheduled (from the 0195 spike) |

## Staging-review wave (GRS-0205–0226, 2026-07-26 onward)

From the 2026-07-26 staging review. Wave 4 (the course rebuild) is the part that has landed.

| Ticket | Title | Status |
|---|---|---|
| GRS-0205 | Rewrite every string in the app, not just the reviewed screens | Planned |
| GRS-0206 | Rive as the diagram and motion system (ADR-0049) | Planned — rewritten 2026-07-29 after reading the repo |
| GRS-0207 | Outreach and CRM platform: decide, then build thin | Planned |
| GRS-0208 | One clean demo account + a founder admin who can act as any advisor | Planned |
| GRS-0209 | The Operating Model dropdown still does not line up | Planned |
| GRS-0210 | Smart search must know the firms an advisor will type | Planned |
| GRS-0211 | The client deliverable, rebuilt: what it says | Planned |
| GRS-0212 | Customer Proposition for exchanges: research, model, ship | Planned |
| GRS-0213 | Scenarios an advisor can drive, with a narrative assistant | Planned |
| GRS-0214 | What the client gets free vs on engagement | Planned |
| **GRS-0215** | **Rebuild the courses as courses, not paragraphs** — the depth standard | **In review, PR #220** (deck export still unbuilt) |
| **GRS-0216** | **The OpenBB course** — 196 slides, eight sections | **In review, PR #220** |
| **GRS-0217** | **The remaining product courses, to the same standard** | **In progress** — Benzinga PR 1 of n, opened at 2 of 8 sections. Order set by commission: Benzinga (1500 bps) → Brandfetch (750/375) → sales-ops-playbook |
| GRS-0218 | The Sales Egoist course | Blocked on source material |
| GRS-0219 | The client report as a Bruntsfield-branded PDF | Planned |
| GRS-0220 | The client report as an interactive web page, read tracking | Planned |
| GRS-0221 | Stage 6 layout: the panels that fight each other | Planned |
| GRS-0222 | The narrative assistant: drafting against real scored data | Planned |
| GRS-0223 | "All the scores seem surprisingly similar": find out why | Planned |
| GRS-0224 | Repository coverage for the dormant peer-governance code | Planned (arose from 0188) |
| **GRS-0225** | **Diagrams for the courses, authored not decorated** — nine scenes | **In review, PR #220** |
| **GRS-0226** | **The slide reader and the section gate** — makes 0215/0216/0225 visible | **In review, PR #220** |

## Demo-readiness program (GRS-0158–0163, 2026-07-21) — get the studio performant enough to show advisor hires

From the staging deep-dive + brokerage end-to-end run (`reports/product-confidence-staging-2026-07-20.md`,
`reports/brokerage-e2e-staging-2026-07-21.md`). Target = **demo-ready** (recruit advisors), distinct from
**production-ready** (real client deliverables — still gated on founder coefficient elicitation).

| Ticket | Title | Phase | Priority |
|---|---|---|---|
| GRS-0158 | Academy production seed (empty-Workbench fix) | 1 populate | HIGH |
| GRS-0159 | Repeatable demo-data seed (Revolut + HL end-to-end) | 1 populate | HIGH |
| GRS-0161 | Reconcile the two V numbers (portfolio vs deliverable) | 1 legible | HIGH |
| GRS-0163 | Demo-polish sweep (segment/attribution/error copy/spinner) | 1 legible | MED |
| GRS-0160 | Assessment wizard density UX pass (the "clunky" fix) | 2 feel | HIGH |
| GRS-0162 | "What can I sell against this report" (gaps → products) | 3 value | MED-HIGH |

## Shipped

| Range | Theme |
|---|---|
| GRS-0001–0015 | Scaffold, CI, auth + scoping, contracts, ATLAS engine to Methodology v1.1/v1.2 + golden master, wizard Path A |
| GRS-0016–0019 | Loop 4 — Deliverable Builder (value bridge, AI drafts gated, diagnostic pack, deliverables frontend) |
| GRS-0020–0027 | Loop 5 — Workbench + Governance (dual-rating + consensus, committee queue, calibration, certification, learning content + Power Drills, Practice Arena, bench queue, workbench frontend) |
| GRS-0028–0034 | Loop 6 — Earnings, Path B (ingestion/transcription, extraction→review→scoring), prediction register + benchmark ingestion, hardening + compliance, elicited coefficients, launch readiness |
| GRS-0035–0065 | UI/UX + onboarding series — Claude-aligned design system, `/guide` primer, first-run walkthrough, earnings page, engagement→assessment linking, live-score bottleneck + module breakdown, dual-rating + committee UI, review-before-send |

_Note: some earlier tickets shipped with placeholder config (earnings v7, GRS-0028) or against the
ratified-v1 scope only — the deltas are tracked as new tickets below, not silent edits._

## In flight — estate reconciliation + guided consulting (Track A, no methodology decision needed)

| Ticket | Title | Status |
|---|---|---|
| GRS-0066 | Estate doc corrections + engine A1/A2 re-verification | In review |
| GRS-0067 | Earnings v7 delta — audit shipped config vs Commission Schedule v7, ticket the gap | Planned |
| GRS-0068 | Guided consulting: structured create + Step-1 business profile (country/segment/asset classes/regions/licensing) | Planned |
| GRS-0069 | Guided power cards — plain-English + brokerage examples + notes + tooltips (KEEP benefit/barrier; **no** 0–10 slider) | Planned |
| GRS-0070 | Diagnostic visuals — module-q_m radar, B→P→L→V waterfall, module table with κ_m, scenario impact chart (KEEP P10/P50/P90) | Planned |
| GRS-0071 | "Your Brokerages" portfolio home (segment / last score / last updated) | Planned |
| GRS-0072–0073 | House deliverable types (Outside Read Deck / Note / Primer / Strategic Assessment) | Planned |

## Next loop — gated on founder decisions (Track B)

| Item | Blocks | Gate |
|---|---|---|
| **Loop 7 — C-index (Customer Proposition)** — C registry (10 Phase-E modules + 93 widget subcomponents + rarity tags), rubric anchors from the 7 scored checklists, wizard C-step, benchmark ingestion (approval-gated), deliverable sections; reported *alongside* V (Stage 1) | v1.3 normative | Founder D1 (ratify Phase E 10) + D2 (staged entry) — `adr/ADR-0023` |
| **Exchange operating-model profile** — profile = module selection + criticals + weight set per operating model | Loop 7 scope / sequencing | Its own ADR (`METHODOLOGY-V2-SCOPE` §2); active book is exchange-side (ASX, NSE) |
| **v1.4** — θ re-elicitation across four lenses → C enters V → golden-master v2 | C-in-composite | After 2–3 C engagements + D1/D2 |

## Parallel founder/content track (dependencies, not tickets)

| Item | Blocks |
|---|---|
| Ratify ADR-0023 decisions 1–2 | Loop 7 normative status |
| Commission the Power Primers (Foundation Package strand 1, unwritten) | GRS-0024 quiz bank depth |
| Score the 9 captured-but-unscored apps (Capital, Charles Schwab, EFG Hermes, EasyEquities, Futu, Hapi, Robinhood, Trii, eToro) | C benchmark corpus breadth at launch |
| Confirm Commission Schedule v7 as earnings config source | GRS-0067 |
| Approve harvesting ASX/NSI pack structure (anonymised) as deliverable templates | GRS-0072–0073 |
| θ re-elicitation panel — share a session with v1 annual re-elicitation? | v1.4 (θ_C) |

## Planned — Part 1 (founder-greenlit 2026-07-16) — see `planning/PART1-oauth-earnings-profiles-cindex.md`

| Tickets | Workstream | ADR |
|---|---|---|
| GRS-0073, 0074 | Google OAuth sign-in + public-site → app login handoff | ADR-0024 |
| GRS-0075, 0076 | Earnings: Commission Schedule v7 (two-stream) | ADR-0026 (amends ADR-0017) |
| GRS-0077, 0078, 0079 | Operating-model profiles (exchange-first) | ADR-0025 |
| GRS-0080–0086 | C-index / Loop 7 (Stage 1 v1.3; 0086 = Stage 2 v1.4, gated) | ADR-0023 · Methodology v1.3 |

## Planned — Part 2: Advisor Studio UI/UX & product review (founder-greenlit 2026-07-16) — see `planning/PART2-uiux-review.md`

Section-by-section founder review → 48 tickets (GRS-0087–0134) + 4 ADRs. Suggested order: session fix →
Home/Primer/rename → Deliverables + Revolut demo → Wizard Phase A → Pipeline program → Academy program →
earnings/guide → Phase-B flags.

| Tickets | Section / workstream | ADR |
|---|---|---|
| GRS-0087–0091 | §1 Home / Dashboard (account menu, health chip, welcome, rename, IA) | ADR-0030 (rename) |
| GRS-0092–0097 | §2 Primer depth + P/L label refinement | ADR-0030 (labels) |
| GRS-0098–0110 | §3 Portfolio + Wizard rigor (Phase A now; 0100/0101/0109 Phase B) | ADR-0025 / ADR-0023 (overlap) |
| GRS-0111–0115 | §4 Pipeline / GTM engine (one program) | ADR-0027 |
| GRS-0116–0119 | §5 Deliverables / Engagements (0117 demo now, 0119 sandbox later) | ADR-0029 |
| GRS-0120 | §0 Session persistence / stop random sign-outs | ADR-0024 |
| GRS-0121–0132 | §6 Workbench → Bruntsfield Academy (one program) | ADR-0028 |
| GRS-0133 | §7 My Earnings — gamify + chart | ADR-0026 (reuse) |
| GRS-0134 | §8 Guide navigation shell (last) | — |

## Sequencing notes

- Track A (GRS-0066–0072) needed **no** methodology decision — the advisor-day-1 guided-consulting program; shipped.
- **Part 1 (GRS-0073–0086)** is unblocked: founder D-1..D-7 resolved (`PENDING-FOUNDER-REVIEW.md`). Suggested order: OAuth → Earnings v7 → profiles mechanism/exchange → C-index Stage 1; C into V (v1.4, GRS-0086) is gated on the θ_C panel + golden-master v2.
- Track B (Loop 7 / exchange profile / v1.4) consumes the review corpus through the app's scoped storage (never committed to this repo).
- After Track B: phase 2 = Holy Corner (Elite Vault adaptation, new ticket prefix), phase 3 = Viewforth.
  Both consume `bcap-contracts` as-is.
