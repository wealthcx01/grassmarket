# GRS-0075 — Commission Schedule v7: config, contracts, product catalog, migration

**Status:** Planned
**Loop:** Track B — Earnings v7
**Depends on:** ADR-0026 (two-stream v7 commission, amends ADR-0017)

## Why

GRS-0028 shipped the earnings engine against an explicitly *placeholder* rate model
(`commissions.yaml` `version: commissions-v1-draft`, "DRAFT v1 values … NOT final"), and GRS-0067
audited it against the ratified `Bruntsfield_Consultant_CommissionSchedule_TEMPLATE_v7.docx` and
found the schema too flat. v7 is the *decided* commercial model, and it changes the config **shape**,
not just the numbers: two independent streams, per-product multi-year rates with dated windows, a
delivery-type × sourcing matrix, and pay-when-paid. Because it alters the shape (extra axes,
products, multi-year tiers, dated windows), it needs the **ADR-0026** amendment to ADR-0017's
governance — a rate-value change alone would not. This ticket lands the config + contracts + product
catalog + migration; GRS-0076 lands compute + API.

Note: independent-consultant vs employee (the template's "contracting as: individual / company") is
consultant *context* recorded for the schedule, **not** a scoring or rate axis — do not add it to any
rate key.

## What to build

- **Config — `packages/bcap_contracts/src/bcap_contracts/registry_data/commissions.yaml`** → bump
  `version` to `commissions-v7`. Replace the flat `rates_bps` with:
  - **Stream A `products`** map, per product `{yr1_bps, yr2_bps, window_months}`: ConnectTrade
    1500/1000/24, OpenBB 1500/1000/24, Brandfetch distribution 750/500/24, Brandfetch redistribution
    375/375/36.
  - **Stream B `consultancy`** matrix `sourcing × delivery_type → {yr1_bps, thereafter_bps}`:
    bruntsfield_led self 3000/2500 · firm 1500/1000; consultant_led self 6500/5500 · firm 4500/3500.
  - Generalise the single `attribution_window_days` scalar in `recovery_fees.yaml` (the only existing
    "window" precedent, `recovery_fees.yaml:11`) into the per-product `window_months` idea — i.e. a
    window is now product-scoped config, not one global scalar. (Leave the recovery-fee scalar as-is
    if it is still load-bearing; call the reconciliation out in the ADR.)
- **Contracts — `packages/bcap_contracts/src/bcap_contracts/commissions.py`:**
  - New `DeliveryType` StrEnum (`bruntsfield_led` / `consultant_led`), mirroring the existing
    `SourcingAttribution` shape (`commissions.py:34`).
  - Reconcile `SourcingAttribution` to v7's **self / firm** (firm = Bruntsfield funnel / inbound).
    **Decision to record in ADR-0026:** fold the existing `co_sourced` into `firm`, or retain it as a
    variant — pick one and document it; do not leave three legacy values silently mapped.
  - New **product-catalog contract `ProductRef`** — nothing exists today (engagements have no product
    field). Minimal: `product_id`, display name, and the Stream-A rate lookup key; validated against
    the `products` config map at load time (ADR-0001 completeness, fail loud on an unknown product).
  - Rework `CommissionConfig` (`commissions.py:54`) into nested **Stream-A product config +
    Stream-B matrix**, each with its own completeness validator (the `_require_every_combination`
    pattern at `commissions.py:66`): every product must carry all three fields; every
    sourcing × delivery_type cell must be present — a gap is a load-time refusal, no defaults.
  - Extend `CommissionLine` (`commissions.py:118`) with `product_id`, `delivery_type`,
    `contract_year` (Yr1 / Yr2 marker), and `window_end`; extend the completeness/`extra="forbid"`
    guards accordingly.
  - Extend `commission_content_hash` (`earnings/commission.py:60`) to seal the four new fields
    (append to the canonical field list — `payment_status` stays excluded, `commission.py:73`).
- **ORM + migration — `src/grassmarket/data/models.py`:** `CommissionLineORM` (`models.py:300`) gains
  columns for `product_id`, `delivery_type`, `contract_year`, `window_end`, and a `client_paid_on`
  date (the pay-when-paid anchor GRS-0076 gates on). New Alembic migration adds them nullable
  (existing recovery-fee + v1 lines keep null provenance).

## Acceptance / verification

- `load_commission_config()` fails loud on an incomplete v7 file: a missing product field, a missing
  Stream-B matrix cell, or a negative bps all raise `CommissionConfigError` at load (no `.get`
  default anywhere on the path — CLAUDE.md #3).
- `commissions-v7` loads with full Stream-A + Stream-B completeness; `ProductRef` validates against
  the config and refuses an unknown `product_id`.
- `CommissionLine` and `CommissionConfig` round-trip (Pydantic v2 + JSON Schema); the new fields
  serialise and the TS mirror regenerates.
- `commission_content_hash` changes when any of the four new fields change and is stable otherwise;
  the existing seal tests still pass for legacy null-provenance lines.
- The Alembic migration applies clean forward on a v1 DB and the columns are nullable.

## Not in scope

- Compute helpers, the pay-when-paid gate, repository branching, and API request changes — GRS-0076.
- Any UI / earnings-statement rendering of streams or products.
- Writing ADR-0026 itself (this ticket *depends on* it; the sourcing-reconciliation and
  window-generalisation decisions are recorded there, not here).
- Back-filling `product_id` / `delivery_type` onto historical v1 lines (they stay null; non-retroactive).
