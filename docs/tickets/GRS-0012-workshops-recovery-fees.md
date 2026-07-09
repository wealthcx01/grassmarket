# GRS-0012 — Workshops & recovery fees (backend)

- **Loop:** 3 (see PRD §9)
- **Branch:** `grs-0012-workshops-recovery-fees`
- **Status:** In review
- **Normative source:** PRD §4 (Pipeline Management); ADR-0001 (config completeness),
  ADR-0002 (score/currency separation), CLAUDE.md #6 (immutable, hashed records).
- **Depends on:** GRS-0006 (`Money` + assumption register), GRS-0011 (pipeline lifecycle).

## Goal

Workshop management and the Workshop Recovery Fee — **the ticket where Money enters the pipeline**.
The whole risk is the ADR-0002 boundary: currency and score never mix.

## What shipped

1. **Workshop management** (`Workshop` contract gains `WorkshopState`; `WorkshopORM`): a workshop
   linked to one of the consultant's own prospects, with a Pre-Workshop Brief and Workshop Output,
   moving scheduled → delivered. Scoped through the repository (own workshops only); a workshop can
   only attach to a prospect the principal owns.
2. **Recovery-fee attribution — where Money lives** (`bcap_contracts.fees`,
   `src/grassmarket/pipeline/fees.py`):
   - The fee is **`Money`** — a currency + the `assumption_register_ref` (the config it derives
     from). A bare currency figure is unconstructible (GRS-0006). Money only ever combines with
     Money.
   - **Rates are configuration, never code** (`registry_data/recovery_fees.yaml`): per-tier fee +
     the 12-month attribution window, loaded fail-loud — every consultant tier must have a fee or
     the config refuses to load. Changing the fee is a config edit.
   - **The 12-month window** is honoured at its exact inclusive edge: contracting `window_days`
     after delivery is eligible; one day later is not; before delivery is never.
   - **Append-only, immutable, content-hashed** (`RecoveryFeeAttributionORM`, the scoring-run
     pattern): a delivered workshop whose prospect contracts within the window yields one immutable
     record citing the rate reference + window it used, sealed with a SHA-256 hash recomputable from
     the stored fields. One attribution per workshop (a second is a conflict); rows are never
     updated.
3. **ADR-0002 boundary extended**: the AST guard's `_SCAN_DIRS` now includes
   `src/grassmarket/pipeline` (the whole subtree — the score-free forecast *and* the Money fees). No
   function signature and no expression mixes a Score/index with Money; the guard stays green with
   the new surface scanned.
4. **API** (`workshops` + `recovery-fees` routers): `POST/GET /workshops`, `GET /workshops/{id}`,
   `POST /workshops/{id}/deliver`, `POST /workshops/{id}/recovery-fee`, `GET /recovery-fees`. Money
   never appears in a handler signature — endpoints speak dates and ids; the £ is computed and
   persisted inside the repository. Cross-owner access → 404; a window/state/duplicate refusal → 409.
5. **Persistence**: `workshops` + `recovery_fee_attributions` tables via **Alembic migration 0004**;
   migration↔models parity holds.

## Tests

The AST guard stays green with pipeline scanned; a `Money` without a currency + ref refuses; the
attribution window is eligible inside and refused outside, tested at the exact edge (`==window` ok,
`+1` not); rates come from config (two configs → two fees, no code change); attribution records are
immutable + hashed (recompute equal, field-sensitive, second attribution → conflict); a fee needs a
delivered workshop; cross-owner workshop/fee access is 404 (HTTP) and the fee flow is scoped.
**201 backend tests pass** (+14).

## Non-negotiables honoured

Repository-only persistence; data scoping absolute + tested; the ADR-0002 boundary is structural and
guarded across the pipeline tree; recovery-fee rates + window are fail-loud config; attribution
records are append-only + auditable + hashed; `Money` never bare; contract-typed with schema parity;
one ticket = one branch = one PR.
