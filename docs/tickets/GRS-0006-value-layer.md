# GRS-0006 — Value layer + scoring-run persistence (closes Loop 1)

- **Loop:** 1, final ticket (see PRD §9)
- **Branch:** `grs-0006-value-layer`
- **Status:** In review
- **Normative source:** `docs/ATLAS-Methodology-v1.1.md` §10; ADR-0001, ADR-0002.
- **Depends on:** GRS-0004 (engine), GRS-0005 (Monte Carlo).

## Goal

The value layer and immutable scoring-run persistence — the last Loop 1 piece. **ADR-0002 is the
whole game:** score-points and currency never meet in one equation. Three strictly separated pieces,
each in its own domain, plus persistence through the repository.

## 1. Scenario prioritisation — SCORE domain (`grasmarket.value.scenarios`)

A scenario is evaluated by **full re-scoring**: `score()` on baseline and on scenario inputs, diff V
→ ΔV. `prioritise_upgrades` ranks candidate scenarios by ΔV descending — the **Upgrade Priority
Index**. No LV formula, no κ, no score×currency term (prototype defect D2). Nothing here imports
`Money`.

## 2. The value bridge — CURRENCY + ORDINAL domains (`grassmarket.value.bridge`)

Three separated computations (Methodology §10):

- **Cost** (layer 1) — effort × day-rate → `Money`.
- **Levers** (layer 2) — each of the four evidenced levers (**cost-to-serve, project drag, incident
  expected loss, revenue enablement**) → risk-adjusted NPV as `Money`. Every figure is traceable to
  a client-supplied baseline in a **typed `AssumptionRegister`**; a `ValueBridge` whose figures cite
  a missing assumption refuses to construct.
- **Strategic** (layer 3) — moat/durability as an **ordinal** `StrengthRating`, never a decimal.

`Money` only ever combines with `Money` (same currency; cross-currency `add` is refused). No function
takes both a `Score` and a `Money` — the ADR-0002 AST scan now covers `grassmarket.value` too.

## 3. Scoring-run persistence — through the repository only

`ScoringRunORM` is **append-only and immutable**: rows are inserted, never mutated, with the ONE
exception of finalisation (`finalised` False→True, which locks the inputs; re-finalising is a
`ConflictError`). Each run stores the full inputs + result (every intermediate) as JSON, the three
version stamps (engine / methodology / coefficient), and a **content hash** (SHA-256 over inputs +
versions) that is deterministic and recomputable from the stored inputs — the tamper-evidence seal.
Access is **absolutely scoped**: `list`/`get`/`get_record`/`finalise` all route through
`_assert_can_access`; a consultant can never read another's runs (admins excepted, explicitly).

## Alembic replaces `create_all`

The **first migration** (`migrations/versions/0001_initial_schema.py`) is now the schema source of
truth — consultants, invitations, prospects, and the new `scoring_runs`. `run_migrations(engine)`
applies it on the given engine's connection (so it works with the in-memory SQLite in tests), and the
app and the test fixture both use it. `create_all` is retained only as a models-direct helper; a
parity test asserts the migration and the models build identical tables + columns.

## Tests

- **ADR-0002 AST scan stays green**, now including `grassmarket.value` — no signature mixes Score and
  Money; `Money` still needs a currency + assumption ref to construct.
- **Worked value bridge** on Meridian: assumption register (7 client-supplied baselines) rendered as
  a table; cost + four levers + strategic rating; total lever NPV is `Money`; a lever citing a
  missing assumption fails to construct; cross-currency totalling is refused.
- **Scenario ΔV + Upgrade Priority Index**: upgrading the OEMS bottleneck raises V; the index ranks
  the bigger-ΔV upgrade first; a no-op scenario has ΔV = 0.
- **Scoring-run persistence**: version stamping; content-hash stability run-to-run; hash recomputes
  from the stored inputs (tamper-evidence); finalisation locks and re-finalising is refused; a
  consultant sees only their own runs (scoping), admin excepted.
- **Migration**: migration ⟺ models parity; `scoring_runs` exists with its scoping + hash columns.

## Loop 1 is complete

The golden master, the deterministic engine, Monte Carlo, and the value bridge now run **end to
end**: `score()` reproduces the ratified Meridian fixture exactly; Monte Carlo wraps it for ranges;
scenarios rank in the score domain; the bridge prices in currency; runs persist immutably and scoped.

## Backlog (Loop 1 wrap / Loop 2 planning — NOT this ticket)

- (a) A metric/power input-uncertainty model so §7 yields real B/P ranges, not degenerate bands.
- (b) The deliverable layer must label unmodelled B/P uncertainty honestly — never as a tight band.

## Out of scope

The wizard (Loop 2); deliverable generation; the elicited weights (the panel's, replacing the drafts).
