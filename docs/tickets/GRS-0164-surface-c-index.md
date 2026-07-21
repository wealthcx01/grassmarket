# GRS-0164 — Surface the Customer-Proposition index (C) alongside V

**Status:** In progress (2026-07-21). Founder-directed ("surface C first"). Promotes GRS-0163 item 3.
**Priority:** HIGH — highest-leverage demo fix. **Loop:** demo-readiness.

## Why

C is already computed but hidden. The engine scores a Customer-Proposition index C (ADR-0023 Stage 1,
`c_index_of`) that discriminates far more sharply than the headline V — on the brokerage run C spread was
Revolut 55.6 / HL 41.0 / WeBull 61.9 (~21 pts) vs V's 54–61 (~5 pts). C captures the customer-experience
story (UX, onboarding, trading experience) that V compresses because V is scale-weighted (B). But C only
appeared in the live wizard rail: `BrokeragePortfolioEntry` had no `c_index` and the portfolio/deliverable
showed only V. So the most demo-relevant score was invisible.

## What

- Contract: `BrokeragePortfolioEntry.c_index: Score | None` (reported alongside V, not folded in;
  regenerated JSON schema).
- `repository.list_brokerage_portfolio`: recompute C per row via `c_index_of` under the profile's
  registry view (deterministic, document-derived — present even for a draft; None when not scoreable).
- Frontend portfolio table: a **Customer (C)** column next to **Platform (V)**, with an explanatory
  tooltip; "—" when C isn't scoreable.
- Tests: portfolio surfaces C when C-data is present; null (never fabricated 0) without it.

## Follow-ups (separate)

- Add C to the deliverable/executive-summary headline (same alongside-V framing).
- Persisting C on the immutable scoring run (vs recompute-on-read) — deferred; C is deterministic so
  recompute is consistent, but a stored C would match the immutability model (non-negotiable #6).

## Acceptance

The portfolio shows V and C side by side; the C spread across the demo brokerages reads at a glance.
