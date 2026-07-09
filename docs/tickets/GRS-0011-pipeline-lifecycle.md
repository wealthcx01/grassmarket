# GRS-0011 — Pipeline & prospect lifecycle (backend)

- **Loop:** 3 (see PRD §9) — first ticket of the advisor-CRM loop.
- **Branch:** `grs-0011-pipeline-lifecycle`
- **Status:** In review
- **Normative source:** PRD §4 (Pipeline Management); ADR-0001 (registry completeness),
  ADR-0002 (score/currency separation).
- **Depends on:** GRS-0001 (the prospects skeleton).

## Goal

Turn the Loop 0 prospects skeleton into a working kanban: the full ten-stage lifecycle with
**validated** transitions, time-in-stage flags, and a currency-free deal-volume forecast — all
scoped to the owning consultant and fail-loud.

## What shipped

1. **The stage machine** (`bcap_contracts.pipeline`): the ten kanban stages already existed; this
   adds the **transition graph** (`LEGAL_TRANSITIONS`) and `assert_legal_transition`. The forward
   path plus the two ever-available off-ramps (Nurture / Closed); Contracted→Active→Delivered has
   no Nurture off-ramp; Closed re-opens only into Nurture. An illegal jump (Prospect→Contracted) or
   a no-op same-stage move is refused with `IllegalStageTransition` — never a silent allow.
2. **Time-in-stage** (`Prospect.stage_entered_at`, new): set on creation and **reset on every
   validated transition**. The pipeline service flags a prospect stale when its days-in-stage
   crosses the per-stage threshold. `now` is injected, so flags are deterministic.
3. **Deal-volume forecast** (`PipelineForecast`, `PipelineBoard`): the board annotates every scoped
   prospect with days-in-stage + stale flag; the forecast is **probability-weighted deal volume**
   (Σ close-probability over the book) with a per-stage breakdown. **Currency-free by construction**
   — no `Money` is imported into the pipeline module. The £ value forecast + recovery fees are
   GRS-0012, where Money enters and the ADR-0002 AST guard extends to cover the pipeline modules.
4. **Rates are configuration, never code** (`registry_data/pipeline_config.yaml`): per-stage
   close-probability and stale-after-days. Loaded fail-loud (`load_pipeline_config`) — every one of
   the ten stages must be present or the config refuses to load (ADR-0001 completeness); an unknown
   stage key or an out-of-range probability is a validation refusal.
5. **Repository + API**: `update_prospect_stage` now validates the transition and resets the stage
   clock (still the single scoped write path). New scoped endpoints `GET /pipeline/board` and
   `GET /pipeline/forecast` read the principal's OWN prospects only. An illegal transition on an
   owned prospect is **409**; a cross-owner stage update is **404** (never revealing existence).
6. **Persistence**: `prospects.stage_entered_at` column + **Alembic migration 0003** (backfills
   existing rows via `server_default=now()`); the migration↔models parity test still passes.

## Tests

Transition graph (forward legal / skip-ahead refused / same-stage refused / off-ramps +
re-engagement); config completeness refusal; time-in-stage stale flag against an injected `now`;
forecast probability-weighting (Closed contributes 0, open excludes terminal stages); repository
create sets the stage clock and a legal move resets it, an illegal move refuses; HTTP illegal→409,
legal→200, board/forecast scoped to owner, cross-owner stage update→404, endpoints require auth.
**187 backend tests pass** (+16). Schema parity + migration parity green.

## Non-negotiables honoured

Repository-only persistence; data scoping absolute + tested (own board/forecast, cross-owner→404);
ADR-0002 boundary kept by staying currency-free (Money deferred to GRS-0012 with the guard); rates
are config; fail-loud config + transitions; contract-typed with schema parity; entity-shaped
`Prospect` for later Holy Corner sync; one ticket = one branch = one PR.
