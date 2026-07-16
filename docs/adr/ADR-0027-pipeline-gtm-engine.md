# ADR-0027 — Pipeline / GTM engine (one flagship program)

- **Status:** Accepted (2026-07-16). Founder-directed in the Part-2 UI/UX review: the current kanban +
  weighted forecast is "embarrassing… so basic"; adding a prospect "does nothing useful." Build a real
  go-to-market engine, as **one program** (not phased).
- **Date:** 2026-07-16
- **Deciders:** Founder + engineering
- **Normative source:** `docs/planning/PART2-uiux-review.md` §4.
- **Implements:** GRS-0111 (crm-rebuild), GRS-0112 (gmail-calendar), GRS-0113 (ai-mcp-gtm),
  GRS-0114 (lseg-influencer-maps), GRS-0115 (seed-target-universe).
- **Couples with:** ADR-0024 (Google OAuth — the session substrate the Gmail/Calendar scopes extend);
  ADR-0002 (currency-free scoring — the forecast honours the Money boundary).

## Context

The pipeline today is a thin optimistic-move kanban (`StageMoveControl.tsx`) over a legal-transition graph,
with a weighted `ForecastPanel`. The prospect → qualify → workshop → engagement flow does not tie together
(adding "WeBull Thailand" only asks when a workshop is scheduled; there is no engagements list; scheduling
binds to nothing). Meanwhile the advisory book needs advisers to **book workshops and qualify prospects at
scale**, natively inside the app, against a concrete target universe (150 banks) and with warm-intro paths
sourced from market data.

The founder supplied the reference model: **EliteVault** (the LabCI CRM, `C:\dev\elite-vault\elite-vault-
handover`) — Next.js 16 + SQLite/raw-SQL + `@dnd-kit`. Its **UI patterns** port; its **SQL/route code does
not** (Grassmarket is FastAPI + Postgres/SQLAlchemy + Pydantic contracts — everything is re-expressed as ORM
+ routers + contracts). The differentiator is **LSEG influencer mapping** via the existing `bcap-lseg` MCP
connector (surfaces *influencers* — analysts who cover relevant stocks and want retail flow — not the digital
product owners; a warm-intro door, per the Barclays Live worked example).

## Decision

Build the pipeline as **one flagship GTM program** binding five tickets:

1. **GRS-0111 — EliteVault-grade CRM + fix-the-flow.** Rich prospect/deal cards, a slide-over detail panel
   (inline click-to-edit), an activity/stage-history timeline, win-probability, a KPI/filter/search row, and
   first-class **Company + Contact** entities. Port the UI (`@dnd-kit` DnD kanban, `DealDetailPanel`), but
   respect Grassmarket's stricter legal-transition graph (revert on 409). Rebuild the logic in Python
   (win-probability as a config-driven `pipeline_config.yaml` scorer; `ProspectStageHistoryORM` unified with
   the existing `CommsLogEntry`). The forecast stays **currency-free** (ADR-0002).
2. **GRS-0112 — Native Gmail + Google Calendar.** Workshops booked into Calendar; emails tied to prospects.
   Extends the Google OAuth of ADR-0024 with Gmail/Calendar scopes + a connected-accounts area. Greenfield
   (EliteVault has no Google integration to port); `CommsLogEntry` is the attach point.
3. **GRS-0113 — AI / MCP GTM surface.** A space to run best-in-class prospecting/enrichment/outreach MCP
   skills (Claude sales plugins et al.).
4. **GRS-0114 — LSEG influencer maps.** Per-target influencer maps via `bcap-lseg` (TR.Analyst* keyed by
   ticker → filter by brokerage contributor ID → dedup into an org chart + a web overlay for the real owner),
   with the influencer≠owner distinction. Deliverable shape = the Barclays workbook's three tabs.
5. **GRS-0115 — Seed the universe.** Load the 150 target banks as prospects and batch-prepopulate influencer
   maps. Depends on GRS-0114.

## Consequences

- New/expanded contracts (`bcap_contracts/{entities,pipeline}.py` — Company, Contact, stage history,
  win-probability), ORM + migration, `pipeline_config.yaml`, `web/routers/pipeline.py` endpoints, and a
  substantial frontend rebuild under `frontend/app/pipeline/`.
- New external dependencies gated behind operator provisioning: Google Gmail/Calendar scopes (ADR-0024),
  the `bcap-lseg` connector, and any GTM MCP skills. AI-surfaced enrichment/outreach is approval-gated
  (ADR-0009); no client data is committed (the 150-bank list + Barclays example are reference-only, seeded
  through scoped storage).
- Owner-scoping (non-negotiable #9) and config-not-code (commission/forecast weights) are preserved.

## Alternatives considered

- **Phase it (CRM first, integrations later).** Rejected by the founder — this is the flagship GTM initiative
  and the pieces reinforce each other (a CRM without Calendar booking or influencer maps is still "basic").
- **Fork EliteVault directly.** Rejected — stack mismatch (SQLite/raw-SQL/Next 16 vs FastAPI/Postgres/
  contracts); we port UX patterns, not code.
- **Currency in the forecast.** Rejected — ADR-0002 keeps score-points and money separate; value/TCV
  colour-grading only under the Money boundary, otherwise volume-only.
