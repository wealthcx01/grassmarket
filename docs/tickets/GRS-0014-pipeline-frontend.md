# GRS-0014 — Pipeline frontend

- **Loop:** 3 (see PRD §9) — **the last Loop 3 ticket; this closes Loop 3.**
- **Branch:** `grs-0014-pipeline-frontend`
- **Status:** In review
- **Normative source:** PRD §4 (Pipeline Management); ADR-0002 (score/currency separation — held at
  the view layer too). Backend: GRS-0011..0013.
- **Depends on:** GRS-0010 (frontend api-client + JWT pattern), GRS-0011..0013 (the Loop 3 API).

## Goal

Drive the Loop 3 API to a working advisor CRM: a kanban pipeline, prospect/workshop/engagement
detail, the currency-free forecast, and recovery fees shown from the API's `Money`.

## What shipped (Next.js App Router + TypeScript)

1. **Kanban board** (`/pipeline`, `KanbanBoard` + `StageMoveControl`): ten stage columns rendered
   from `/pipeline/board`; each card shows time-in-stage and a stale flag. **Moving a card calls the
   transition endpoint — the BACKEND owns legality.** An illegal move returns 409; the UI **reverts
   the card and surfaces the reason**, never a silent success or a faked move.
2. **Forecast** (`ForecastPanel`): the pipeline forecast is **deal-VOLUME, currency-free** (labelled
   "deal volume · not £") — it renders no £ because the API sends none here.
3. **Prospect detail** (`/prospects/[id]`): stage (movable, backend-validated), its workshops
   (schedule from here), and its engagements (open one once contracted).
4. **Workshop views** (`/workshops/[id]`): schedule → **deliver** → **recovery-fee eligibility**. Any
   £ is displayed **straight from the API's `Money`** via `MoneyAmount`/`formatMoney` — never
   recomputed or combined client-side (ADR-0002 at the view layer). Eligibility is the backend's
   call: an out-of-window attribution returns 409 and the reason is surfaced.
5. **Engagement detail** (`/engagements/[id]` + list): linked assessments, the deliverables-progress
   shell (Loop 4 fills content), and the **append-only comms log in chronological order** + a form to
   add an entry.
6. **Design tokens + auth**: paper/ink, Bottle Green `#1A3B26`, Source Serif 4 / Inter / IBM Plex
   Mono. Reuses the GRS-0010 api-client + JWT pattern; scoping is server-enforced, the client only
   carries the token.

## Tests

- **`StageMoveControl`**: an illegal-move **409 reverts the card** to its previous stage and shows
  the reason (not a silent success); a successful move keeps the new stage.
- **`MoneyAmount`/`formatMoney`**: `Money` renders as currency **from the API object** (£7,500.00
  from `amount_minor: 750000`), never a client-side recomputation; USD/EUR format from the object.
- `npm test` (vitest) is a CI step; **7 frontend tests pass**. Type-check, lint, and a production
  build are all green.

## Exit criteria (closes Loop 3)

A consultant runs a prospect through the full pipeline in the UI (backend validates each move,
illegal moves refuse and revert), schedules and delivers a workshop, sees recovery-fee eligibility
and the fee (from `Money`), and opens an engagement with its comms log — all scoped, CI green.

## Non-negotiables honoured

Backend owns legality (illegal move → 409, revert + reason, never faked); Money is displayed from the
API, never recomputed or combined (ADR-0002 at the view layer); the forecast is currency-free; data
scoping is server-enforced (the client carries the JWT); contract types drive the TS types; one
ticket = one branch = one PR.
