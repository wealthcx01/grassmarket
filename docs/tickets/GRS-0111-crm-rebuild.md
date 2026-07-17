# GRS-0111 — Rebuild the pipeline as an EliteVault-grade CRM

**Status:** Partially shipped (backend foundation) — see "Delivered" below
**Loop:** Part 2 — Pipeline / GTM engine (one program)
**Depends on:** ADR-0027 (Pipeline / GTM engine)

## Delivered (this PR — the "rebuild in Python" foundation)

The low-risk, fully-tested backend half of the flagship landed first, self-contained:
- **Win-probability scorer** (`src/grassmarket/pipeline/win_probability.py`) — deterministic and
  explainable, returning exactly `{score, label, reasons, missing_info}`, with **all weights + bands
  in `pipeline_config.yaml`** (config-not-code). It is a probability, never currency (ADR-0002).
  Surfaced as a pill on every board card (score + reasons/gaps in the tooltip).
- **Stage-history timeline** — `ProspectStageHistoryORM` + migration 0025; a row is written at the
  single `update_prospect_stage` choke-point (plus a creation row), owner-scoped; new
  `GET /prospects/{id}/history` endpoint; rendered as a timeline on the prospect detail page.

**Deferred (needs the `@dnd-kit` frontend dependency + attended review — not cleanly buildable in an
unattended autonomous pass):** the DnD kanban port, the slide-over `DealDetailPanel`, the KPI /
filter / search row, unifying the timeline with `CommsLogEntry` in one panel, and elevating
`company_name` / `primary_contact_*` into first-class **Company + Contact** entities. These carry a
new-dependency/CI risk (bun install of `@dnd-kit` unverified offline) and a substantial UI rebuild,
so they were held rather than shipped half-broken. Golden master untouched throughout.

## Why

The current pipeline — a basic kanban plus a simple weighted forecast — reads as "embarrassing… so
basic" in the founder review. Adding a prospect barely works: creating "WeBull Thailand" only asks
when a workshop is scheduled, surfaces no engagements list, and the scheduling ties to nothing, so
prospect → qualify → workshop → engagement never connect. This ticket rebuilds the pipeline into a
real CRM at EliteVault (`C:\dev\elite-vault\elite-vault-handover`) grade: rich prospect/deal cards, a
slide-over detail panel, an activity timeline, win-probability, a KPI/filter row, and first-class
Company + Contact entities — while fixing the flow so stages tie together. EliteVault is Next.js 16 +
SQLite/raw-SQL; Grassmarket is FastAPI + Postgres/SQLAlchemy + Pydantic contracts, so **UI patterns
port; SQL/route code does not** and is re-expressed as ORM + FastAPI + contracts.

## What to build

**Port directly (UI):**
- The `@dnd-kit` DnD kanban — EliteVault's `DraggableCard` / `DroppableColumn` plus the 5px
  click-vs-drag threshold. REUSE: Grassmarket already has **optimistic-move-with-revert**
  (`components/StageMoveControl.tsx`) and a stricter **legal-transition graph**; DnD must respect the
  legal targets and revert on a 409, not move freely.
- The **slide-over detail panel** (`DealDetailPanel.tsx`) with inline click-to-edit.
- The rich prospect/deal card and the KPI row + filter/search. Re-skin Tailwind → inline-style to
  match the Grassmarket design system.
- Target files: `frontend/app/pipeline/`, `components/{KanbanBoard,ForecastPanel,StageMoveControl}.tsx`,
  `app/prospects/[id]`.

**Rebuild in Python (shape ports, code doesn't):**
- **Win-probability** — re-express EliteVault's deterministic rule-based `scoreWinProbability`
  (`lib/ai/win-scorer.ts`) as a pure Python scorer returning `{score, label, reasons, missing_info}`,
  with **weights in `pipeline_config.yaml`** (config-not-code — never hardcoded).
- A **stage-history timeline** — new `ProspectStageHistoryORM`; write a row in the single choke-point
  `update_prospect_stage`, and unify it with the existing **`CommsLogEntry`** primitive (Grassmarket
  already has a comms-log EliteVault lacks) so the panel shows one activity/timeline.
- First-class **Company + Contact** entities — elevate the `company_name` string and inline
  `primary_contact_*` fields into real entities (the Prospect docstring already anticipates this for
  Holy Corner sync). Backend: `pipeline/` + `data/` + `web/routers/pipeline.py`; contracts in
  `packages/bcap_contracts/{entities,pipeline}.py`.

**Constraints:**
- Keep the **currency-free** forecast (ADR-0002): value/TCV colour-grading only under the Money
  boundary, or stay volume-only. Score-points and currency never mix in one equation.
- Keep owner-scoping (a consultant sees only their own pipeline) and config-not-code throughout.

## Acceptance / verification

- Adding a prospect creates a first-class Company + Contact and the card moves through
  prospect → qualify → workshop → engagement with stages tying together (the "add prospect does
  nothing useful" bug is gone).
- DnD respects the legal-transition graph and reverts optimistically on a 409.
- Win-probability comes from the Python scorer with weights read from `pipeline_config.yaml`; the
  detail panel shows an activity timeline unifying stage history + `CommsLogEntry`.
- The forecast stays currency-free (or values sit behind the Money boundary per ADR-0002); scoping
  tests still pass.

## Not in scope

- Gmail / Google Calendar sync (GRS-0112) and the AI/MCP GTM surface (GRS-0113).
- LSEG influencer maps (GRS-0114) and the 150-bank seed (GRS-0115).
