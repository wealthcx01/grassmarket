# GRS-0067 — Earnings config: Commission Schedule v7 delta

**Status:** Audited — delta specified; build gated (see Gates)
**Loop:** Track A (estate reconciliation)
**Branch:** `grs-0067-earnings-v7-delta`
**Source of truth for v7:** `NEXT-STEPS-2026-07.md` §3.1 (structure) + the OneDrive Commission
Schedule v7 template (exact axes/rates — **not** in this repo; ingested as config, never committed).

## Why

GRS-0028 shipped the earnings engine against an explicitly **placeholder** rate model
(`commissions.yaml` `version: commissions-v1-draft`, "DRAFT v1 values … NOT final"). The estate sweep
established that Commission Schedule **v7** is the *decided* commercial model — not an open item — so
the shipped schema must be audited against it and the gap ticketed (NEXT-STEPS §3.1). This ticket is
that audit; it does **not** change any rate or scoring behaviour (CLAUDE.md #2, #6).

## What v7 requires (NEXT-STEPS §3.1)

- **Stream A — product commission:** per-**product** rates, **Year-1 / Year-2** tiers, **dated
  windows** (a rate applies within an effective date range).
- **Stream B — consultancy:** a **sourcing × delivery-type** matrix, **pay-when-paid** (commission
  becomes payable when the *client* pays, not at contract signing), **uncapped**.

## What shipped today (GRS-0028)

Config `commissions.yaml` → `CommissionConfig`:
- A single basis-point rate keyed **only by `(ConsultantTier × SourcingAttribution)`**, applied once
  to an engagement's `base_value`. Fail-loud completeness over every tier × attribution.
- `CommissionKind = {engagement, workshop_recovery_fee, retainer}` — one economic kind for advisory
  work; **no stream distinction**.
- `PaymentStatus = pending → invoiced → paid` — a manual forward-only lifecycle; `earned_on` is
  stamped at **record time**.
- Immutable `CommissionLine` (SHA-256 seal over the financial fields; `payment_status` excluded so it
  can advance), `rate_ref` provenance so a rate change is never retroactive, integer-bps Money math.

## The delta (shipped → v7)

| # | v7 requirement | Shipped state | Gap |
|---|---|---|---|
| D1 | Two economically distinct **streams** (A product, B consultancy) | One `engagement` kind | Add a `stream` axis (or `CommissionKind` values `stream_a_product` / `stream_b_consultancy`); statement + summary segment by stream. |
| D2 | Stream A **per-product** rates | No product dimension | Config gains a product key; a commission line cites the product it was earned on. |
| D3 | Stream A **Yr1 / Yr2** rate tiers (recurring) | Single one-time rate | Config gains a `year_index` (1/2+) dimension; the engine must know which contract-year a line falls in. Recurring, not one-shot. |
| D4 | Stream A **dated windows** (rate effective ranges) | Single `version`, no dates | Config gains `effective_from`/`effective_to` per rate row (or dated config versions); `rate_bps_for` selects by the line's `earned_on`. Preserve non-retroactivity: a recorded line keeps its `rate_ref`. |
| D5 | Stream B matrix = **sourcing × delivery-type** | Matrix = tier × sourcing | Add a **delivery-type** axis (Outside Read Deck / Note / Primer / Strategic Assessment — see GRS-0072/0073). Confirm with v7 whether **tier** survives as a Stream-B axis or is replaced by delivery-type. |
| D6 | Stream B **pay-when-paid** | `earned_on` at record time; manual PENDING→PAID | Model the trigger: a Stream-B line becomes *payable* only on the client-payment event of its underlying invoice. The lifecycle enum already exists; the **trigger/link is missing** (no client-payment → commission-payable edge). |
| D7 | Stream B **uncapped** | No cap logic | ✅ Satisfied by default (nothing caps). Add an explicit test asserting no cap, so a future change can't silently introduce one. |

## What must NOT regress (v7 build guardrails)

The shipped architecture is correct and every v7 change must preserve it:
- **Rates are config, fail-loud complete** (ADR-0001) — every valid cell must exist or load refuses;
  the new dimensions (product, year, window, delivery-type) multiply the completeness matrix, so the
  validator must enumerate the *real* required cells, never default a missing one.
- **Money is integer bps, never float**; **immutability seal + `rate_ref` provenance**; **non-retroactive**
  recorded lines; **self-scoping** at the repository layer.
- **Score-points and currency never mix** (ADR-0002) — this is all currency, no Score touches it.

## Gates (why this is a ticket, not a build in this PR)

1. **Founder decision #4** (NEXT-STEPS §4): confirm v7 as the earnings config source (recommended:
   Confirm — the placeholder is known-wrong). Low-stakes; does not block writing this ticket.
2. **The exact v7 axes and rate values live in the OneDrive template**, not this repo. Building the
   config *shape* from §3.1's prose is possible, but the *values* and the precise Stream-B matrix
   (does tier survive? which delivery types?) must come from the template — inventing them would
   violate "nothing hallucinated." Ingestion is **config/seed through scoped storage, never committed
   files** (NEXT-STEPS carried-over rule).
3. **Delivery-type axis (D5) depends on GRS-0072/0073** house deliverable types landing first, so the
   Stream-B matrix keys against a real enum rather than a placeholder.

## Recommended build sequence (follow-on tickets, once gates clear)

1. Land GRS-0072/0073 (house deliverable types) → gives D5 its delivery-type enum.
2. `bcap_contracts` schema v2: `stream`, `product`, `year_index`, dated windows, delivery-type matrix;
   completeness validator over the real cell set; `rate_bps_for` selects by (stream, …, earned_on).
3. Engine: recurring Yr1/Yr2 accrual + pay-when-paid trigger (client-payment event → payable).
4. Seed the real v7 schedule via scoped config (operator task; production, never fixtures).
5. Golden-master style test: a worked v7 statement (both streams, a Yr2 line, a windowed rate change,
   a pay-when-paid transition) reproduced exactly.

## What shipped (this PR)

- `docs/tickets/GRS-0067-earnings-v7-delta.md` — this audit + delta spec.
- No code change (audit-only; the build is the follow-on sequence above).
