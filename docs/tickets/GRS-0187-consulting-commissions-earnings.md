# GRS-0187 — Consulting commissions on the Earnings page

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: In review (2026-07-26) — carrot contract, builder, endpoint, Stream-B card and._
statement section shipped; PR open. (2026-07-23, founder feedback item 26.) **Priority:** MED.
**Loop:** founder-feedback remediation, Wave 1.

## Why

The earnings page explains what an advisor earns per product but says nothing about direct
consulting — Stream B of the v7 schedule. Verified on staging: "Consultancy (Stream B) £0.00"
with no explanation of the matrix, and the "close this next" carrot only ever suggests a
product. The computation already exists (`compute_consultancy_commission`, config-driven per
ADR-0026); it is purely unsurfaced.

## Scope

1. **Consultancy carrot contract.** New Pydantic model `ConsultancyCommissionCarrot` in
   `packages/bcap_contracts/src/bcap_contracts/commissions.py`, mirroring
   `ProductCommissionCarrot` (~273): `delivery_type: DeliveryType`, `sourcing: SourcingAttribution`,
   `delivery_label: str`, `sourcing_label: str`, `yr1_bps: int`, `thereafter_bps: int`,
   `example_deal: Money`, `yr1_commission: Money`, `thereafter_commission: Money`,
   `schedule_version: str`. Frozen, `extra="forbid"`. Regenerate the JSON schema into
   `packages/bcap_contracts/.../json_schema/` and add the `ConsultancyCommissionCarrot` interface
   to `frontend/lib/types.ts` beside `ProductCommissionCarrot`.
2. **Carrot builder.** New module `src/grassmarket/earnings/consultancy_carrot.py`, structured
   exactly like `product_carrot.py`:
   - `consultancy_commission_carrot(delivery_type, sourcing, config, *, example_deal=None) ->
     ConsultancyCommissionCarrot`: resolves the cell via `config.require_consultancy_rate`
     (fail-loud on an unknown cell), prices the worked example with
     `compute_consultancy_commission(example, sourcing, delivery_type, 1, config)` for Year 1 and
     `... , 2, config)` for the thereafter period, and stamps `config.version`.
   - `all_consultancy_carrots(config, *, example_deal=None)`: the four cells in a fixed, stable
     order — `bruntsfield_led×self_sourced`, `bruntsfield_led×firm_sourced`,
     `consultant_led×self_sourced`, `consultant_led×firm_sourced` — iterating
     `DeliveryType` × `V7_SOURCING` so a newly-added axis surfaces automatically.
   - The illustrative deal reuses the same £100,000 teaching figure as the product carrot
     (`10_000_000` minor units) under a new ref `grs-0187:illustrative-example-deal`. Decision:
     the same headline figure keeps the two cards comparable; a distinct ref keeps provenance
     honest.
   - `delivery_label`/`sourcing_label` are human strings ("Bruntsfield-led" / "Consultant-led";
     "Self-sourced" / "Firm-sourced") produced here, not typed into the UI, so wording lives with
     the rate.
3. **Endpoint.** `GET /earnings/consultancy-commissions` in
   `src/grassmarket/web/routers/earnings.py`, mirroring `list_product_commissions` (~103) → 200
   `list[ConsultancyCommissionCarrot]` from `all_consultancy_carrots(load_commission_config())`.
   Available to every signed-in advisor (the schedule is not personal data); no principal scoping
   beyond authentication.
4. **Earnings page — Stream B card.** `frontend/app/earnings/page.tsx`: add
   `api.consultancyCommissions(signal)` to the `reload` `Promise.all` (line ~81) and a new
   `Consulting (Stream B)` `<section>` after Product commissions (~247). It renders the four
   carrots as cards (same card styling as products): title `{delivery_label} · {sourcing_label}`,
   a mono line `{yr1_bps/100}% first year · {thereafter_bps/100}% thereafter`, and a muted worked
   example `e.g. <MoneyAmount money={yr1_commission}/> then <MoneyAmount money={thereafter_commission}/>`.
   A one-line intro states the rates are read live from the schedule and never typed in — the same
   copy discipline as the product intro. New client method `consultancyCommissions` in
   `frontend/lib/api.ts` beside `productCommissions` (~1147).
5. **Carrot strip.** `frontend/components/EarningsProgress.tsx` gains a `consultancyCarrots`
   prop; the "close this next" strip may cite one consultancy example. Decision: it surfaces the
   `consultant_led × self_sourced` cell (the highest advisor share, and the one entirely in the
   advisor's own gift) as the single consultancy suggestion, so the motivating figure is the one
   the advisor most controls. `earnings/page.tsx` passes the loaded consultancy carrots through.
6. **Statement (.docx).** `src/grassmarket/earnings/statement.py`
   `build_earnings_statement` gains a `consultancy_carrots: Sequence[ConsultancyCommissionCarrot]`
   parameter and, after the Summary section, a "Consulting commissions (Stream B)" heading listing
   the four cells as `{delivery_label} · {sourcing_label}: {yr1}% first year, {thereafter}%
   thereafter (e.g. {yr1_commission} then {thereafter_commission} on a {example_deal} engagement)`.
   `routers/earnings.py` `download_statement` (~139) passes
   `all_consultancy_carrots(load_commission_config())`.
7. **Recording unchanged.** `record_consultancy_commission` (routers/earnings.py ~205) stays
   admin-only and untouched; this ticket adds no write path. Display only.

## Test plan

Backend (pytest, offline):
- New `tests/test_consultancy_carrot.py`:
  - `all_consultancy_carrots` returns exactly four carrots in the fixed order, with `yr1_bps` /
    `thereafter_bps` equal to `commissions.yaml` (3000/2500, 1500/1000, 6500/5500, 4500/3500).
  - Each carrot's `yr1_commission` / `thereafter_commission` equals
    `compute_consultancy_commission` applied to the £100,000 example (asserted in minor units, so
    the integer money discipline is exercised).
  - Reads live from config: build a fixture `CommissionConfig` with an altered cell and assert the
    carrot's rate and £ move with it (never a typed constant).
  - `schedule_version` is stamped from `config.version`.
- `tests/test_earnings.py` additions:
  - `GET /earnings/consultancy-commissions` → 200 with four rows for any authenticated advisor;
    401 without a token.
  - The downloaded statement bytes contain the "Consulting commissions (Stream B)" heading and the
    four rate lines (parse with python-docx in the test).

Frontend (vitest, per-file):
- `bunx vitest run frontend/app/earnings/page.test.tsx`: the Stream B section renders four cards
  with the correct percentages and worked £ figures from the mocked
  `api.consultancyCommissions`; the section is absent when the call returns `[]`.
- `bunx vitest run frontend/components/EarningsProgress.test.tsx`: the carrot strip can surface the
  `consultant_led × self_sourced` consultancy example when passed `consultancyCarrots`.

## Out of scope

- Recording or editing consultancy commission lines (already admin-only, unchanged).
- Seed hygiene / duplicated demo commission lines (fixed by GRS-0177; this ticket assumes clean
  lines).
- Any change to `compute_consultancy_commission` or the v7 matrix values.
- One ticket = one branch = one PR; the contract regeneration ships in this PR.

## Acceptance

An advisor can read, from the earnings page alone, all four consulting rates
(bruntsfield-led vs consultant-led × self- vs firm-sourced) with a worked £ example each, and the
same four appear in the downloaded statement; every rate and £ is traceably live from
`commissions.yaml` (test-enforced against a mutated fixture config), and no consultancy figure is a
typed constant anywhere in the surface.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `55e34f5` (GRS-0185 + GRS-0187: scope Brandfetch by segment, surface Stream B). This ticket shipped jointly with GRS-0185 on one branch — the Stream-B consulting commissions on the Earnings page are the GRS-0187 half.
