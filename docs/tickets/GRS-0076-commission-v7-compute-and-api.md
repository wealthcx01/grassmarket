# GRS-0076 — Commission Schedule v7: compute, pay-when-paid gate, API

**Status:** Planned
**Loop:** Track B — Earnings v7
**Depends on:** ADR-0026 (two-stream v7 commission, amends ADR-0017); GRS-0075 (config + contracts + migration)

## Why

GRS-0075 lands the v7 config shape, the `ProductRef` catalog, the reworked two-stream
`CommissionConfig`, and the extended `CommissionLine` / ORM. This ticket makes them compute: the two
independent streams price differently (product Yr1/Yr2 with a hard window cut-off; consultancy by
sourcing × delivery-type × period), and v7 introduces **pay-when-paid** — a line cannot reach `paid`
until the client's cash is received and retained. Both build directly on the reusable, already-
proven money discipline (banker's rounding, integer-only, no-FX refusal) in
`earnings/commission.py:25` — do not reinvent it.

Note: v7 changed the config *shape* (streams, products, multi-year, dated windows, pay-when-paid),
which is why it rides ADR-0026's amendment to ADR-0017 rather than a silent rate edit. Independent-
consultant vs employee ("contracting as") remains consultant context, not a compute input.

## What to build

- **Compute — `src/grassmarket/earnings/commission.py`** (alongside `compute_engagement_commission`,
  `commission.py:25`, reusing its `Money` + banker's-rounding + currency-match refusal verbatim):
  - `compute_product_commission(base_value, product, contract_year, config)` — Stream A. Applies the
    product's `yr1_bps` or `yr2_bps` per `contract_year`; **post-window returns zero** (a Yr3+ / past
    `window_months` line prices to £0, not a fallback rate). Yr1/Yr2 are the first/second 12-month
    periods measured from first cash received under the Qualifying Deal — the caller supplies the
    period; the helper does not infer dates.
  - `compute_consultancy_commission(base_value, sourcing, delivery_type, period, config)` — Stream B.
    Looks up the `sourcing × delivery_type` cell, applies `yr1_bps` for the first-12-months period or
    `thereafter_bps` after. Uncapped, ongoing share-of-outcome.
  - Both stamp `rate_ref` from the v7 config so a later config change is never retroactive
    (`commission.py:56` pattern).
- **Pay-when-paid gate — `src/grassmarket/data/repository.py`:** in `advance_commission_payment`
  (`repository.py:841`), advancing to `PaymentStatus.PAID` requires `client_paid_on` set on the line;
  otherwise refuse (`ConflictError`). Keep the forward-only `_PAYMENT_ORDER` invariant
  (`repository.py:719`) — no skips, no reversals.
- **Repository — `record_engagement_commission` (`repository.py:773`):** branch by stream. A Stream-A
  record takes `product_id` + `contract_year` and calls `compute_product_commission`; a Stream-B
  record takes `delivery_type` (+ existing sourcing) and calls `compute_consultancy_commission`.
  Persist the new provenance fields via `_new_commission_line` (`repository.py:721`) so the extended
  `content_hash` seals them. Admin-only stays (governance unchanged, ADR-0014 / ADR-0017).
- **API — `src/grassmarket/web/routers/earnings.py`:** `RecordCommissionRequest`
  (`earnings.py:41`) gains `stream`, `product_id`, `contract_year`, `delivery_type` (validated per
  stream — product fields required for Stream A, delivery_type for Stream B). Prefer splitting into
  two record endpoints (`/commissions/product`, `/commissions/consultancy`) over one overloaded body
  if the per-stream validation gets awkward — call the choice out in the PR.

## Acceptance / verification

- **Stream A unit tests:** Yr1 vs Yr2 rate applied correctly per product; a post-window line
  (past `window_months`) computes exactly £0; ConnectTrade / OpenBB / Brandfetch distribution /
  redistribution each reproduce their `{yr1, yr2, window}` from config.
- **Stream B unit tests:** all four `sourcing × delivery_type` cells (bruntsfield_led self/firm,
  consultant_led self/firm) × both periods (first-12-mo vs thereafter) apply the right bps.
- **Pay-when-paid:** advancing to `paid` is refused with `ConflictError` while `client_paid_on` is
  unset, and succeeds once it is set; forward-only order still holds (no invoiced→pending, no
  pending→paid skip).
- **Golden reproduction:** Byoung's filled schedule
  (`…/Resources/Consultants/Byoung/…CommissionSchedule_Byoung.docx` — referenced, **not** committed)
  reproduces the expected line set (product + consultancy) exactly.
- **Seal integrity:** `content_hash` is stable across a `pending → invoiced → paid` advance and
  across setting `client_paid_on` is handled per ADR-0026 (decide whether `client_paid_on` is inside
  or outside the seal and test that decision); banker's rounding + no-FX refusal tests still green.

## Not in scope

- Config shape, `ProductRef`, ORM columns, and migration — all GRS-0075.
- Earnings-statement / UI rendering of streams, products, or the pay-when-paid state.
- Automatic Yr1/Yr2 period inference from cash-received dates (the caller supplies the period; a
  date-driven period engine is a later ticket).
- Cross-advisor aggregation (Holy Corner scope); self-scoped views/summary/statement
  (`repository.py:863`, `:877`) are unchanged.
