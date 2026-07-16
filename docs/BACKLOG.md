# Grassmarket Backlog — index

All tickets exist as files in `docs/tickets/` (detail lives there, not here). The builder updates a
ticket's status and appends "What shipped" when its PR lands.

**Loops 0–6 shipped (GRS-0001–0034).** Since then a UI/UX, governance and onboarding series has
landed (GRS-0035–0065), plus an estate-reconciliation + guided-consulting track (GRS-0066–). The
authoritative sequencing narrative is `NEXT-STEPS-2026-07.md` (the binder); this file is just the index.

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

## Sequencing notes

- Track A (GRS-0066–0073) needs **no** methodology decision — it is the advisor-day-1 guided-consulting
  program and proceeds in parallel with the founder decisions.
- Track B (Loop 7 / exchange profile / v1.4) is **gated** on founder D1/D2 and on the review corpus
  being ingested through the app's scoped storage (never committed to this repo).
- After Track B: phase 2 = Holy Corner (Elite Vault adaptation, new ticket prefix), phase 3 = Viewforth.
  Both consume `bcap-contracts` as-is.
