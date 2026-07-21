# Grassmarket Backlog — index

All tickets exist as files in `docs/tickets/` (detail lives there, not here). The builder updates a
ticket's status and appends "What shipped" when its PR lands.

**Loops 0–6 shipped (GRS-0001–0034).** Since then a UI/UX, governance and onboarding series has
landed (GRS-0035–0065), plus an estate-reconciliation + guided-consulting track (GRS-0066–). The
authoritative sequencing narrative is `NEXT-STEPS-2026-07.md` (the binder); this file is just the index.

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
