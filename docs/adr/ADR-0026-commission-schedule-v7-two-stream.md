# ADR-0026 — Commission Schedule v7: two-stream commission model

- **Status:** Accepted (2026-07-16). Founder-confirmed (D-4): Commission Schedule v7 is the earnings config source; Byoung is the first-hire validation case.
- **Date:** 2026-07-16
- **Deciders:** Founder + engineering
- **Amends:** ADR-0017 (commission-config-and-earnings-governance). The machinery and governance stand; this changes the config **shape**.
- **Normative source:** `Bruntsfield_Consultant_CommissionSchedule_TEMPLATE_v7.docx` (Advisory/Resources, referenced not committed).
- **Implements:** GRS-0075 (config + models), GRS-0076 (compute + API).

## Context

GRS-0028 "My Earnings" shipped against a **placeholder** config: a single flat `rates_bps` matrix of `ConsultantTier × SourcingAttribution → bps`. ADR-0017 explicitly flagged the rates as the open commercial item. The ratified v7 schedule is materially richer than "new rate values" — it changes the config's **axes**: two distinct commission streams, a product catalogue, multi-year tiers, dated windows, a delivery-type axis, and pay-when-paid semantics. That is a schema change, hence this amending ADR (per CLAUDE.md: commission config is governed, not silently edited).

The earnings kernel is reusable as-is: Money discipline + banker's rounding + no-FX refusal, the `content_hash` seal (which deliberately excludes `payment_status`), `version`+`rate_ref` non-retroactivity, the fail-loud completeness validator, the forward-only payment lifecycle, and self-scoped views/summary/statement.

## Decision

Adopt the **two-stream v7 model** as the commission config schema (`commissions.yaml` → `commissions-v7`).

**Stream A — Product commission.** Per product: `{Year-1 rate, Year-2 rate, window months}`, applied to Cash Received under a Qualifying Deal. Year 1 / Year 2 are the first / second twelve-month periods measured from the first Cash Received; past the window the rate is zero. Seed products: ConnectTrade 15%/10%/24mo, OpenBB 15%/10%/24mo, Brandfetch distribution 7.5%/5%/24mo, Brandfetch redistribution 3.75%/3.75%/36mo. **Amendable by written notice** (new products / future rates) — the existing `version`+`rate_ref` freeze already guarantees non-retroactivity.

**Stream B — Consultancy commission.** A matrix **delivery-type × sourcing → {first-12-month rate, thereafter rate}**:

| | Self-sourced | Firm-sourced |
|---|---|---|
| **Bruntsfield-led** (Power Platform Assessment / methodology work) | 30% / 25% | 15% / 10% |
| **Consultant-led** (bespoke, client-/consultant-determined scope) | 65% / 55% | 45% / 35% |

Applied to Consultancy Cash Received; **uncapped, ongoing share-of-outcome** for as long as the engagement generates cash.

**Pay-when-paid.** All commission is derivative and contingent: paid within 10 business days after Bruntsfield actually receives *and retains* the corresponding funds. The payment lifecycle gains a `client_paid_on` precondition — a line cannot advance to `paid` until the client cash is recorded — layered on the existing forward-only `pending → invoiced → paid`.

**Model shape.** New `DeliveryType` enum (bruntsfield_led / consultant_led) mirroring `SourcingAttribution`; sourcing reconciled to v7's **self / firm** (firm = the Bruntsfield funnel/inbound; the existing `co_sourced` is folded or retained as a labelled variant — the build decides and records it); a new **product-catalogue** contract (`ProductRef` — none exists today); `CommissionConfig` reworked into a nested Stream-A product config + Stream-B matrix with new completeness validators; `CommissionLine` gains `product_id`, `delivery_type`, `contract_year` (Yr1/Yr2), `window_end`, and `client_paid_on`, all sealed by an extended `content_hash`.

**Per-consultant schedules.** Each consultant has their own filled schedule (rates may vary and be amended by notice). Byoung's and Randy's filled instances validate the build (real records, referenced not committed). "Contracting as individual / company" is consultant **context**, not a scoring input.

## Consequences

- Config schema change + contract/ORM changes + an Alembic migration + two new compute functions + a pay-when-paid gate + API request fields. All governed by this ADR amending ADR-0017.
- The completeness validator now enforces both streams (every product has yr1/yr2/window; every delivery-type × sourcing cell present) — a partial config fails loud.
- Retainer commission (in `CommissionKind`) still has no dedicated flow (unchanged from ADR-0017); out of scope here.

## Alternatives considered

- **Just change the rate numbers in the existing flat matrix.** Rejected — v7 needs axes the flat matrix does not have (products, multi-year, windows, delivery-type, pay-when-paid); it is a shape change, not a value change.
- **Model products as engagements.** Rejected — Stream A product commissions are a distinct catalogue with their own multi-year windows; conflating them with consultancy engagements loses the Yr1/Yr2/window semantics.
