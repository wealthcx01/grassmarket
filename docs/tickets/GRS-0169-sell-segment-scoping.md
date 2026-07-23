# GRS-0169 — Sell-from-report: segment-scope the catalogue and the gap matcher

**Status:** Done (2026-07-23). Staging-rerun finding (3/5 personas — "laughed out of the room").
**Loop:** rerun remediation. Amends ADR-0039.

## Why

A wealth report was pitched Brandfetch off a BRANDING power gap while citing "Not yet assessed:
UI & Navigation" — a retail C-module that doesn't exist in the wealth taxonomy; an exchange report
got a logo API. Two defects: (a) the join resolved C fit-targets against the FULL registry instead
of the assessment's profile view; (b) the retail-only catalogue had no per-segment applicability.

## Fix

- C fit-targets resolve against the assessment's PROFILE VIEW (the portfolio's own seam); a
  C-module absent from the view is not-applicable, never "not yet assessed".
- `product_fit.yaml` v2: required per-product `profiles:` list (validated against the profile
  registry, fail loud); every current product is `[retail]`. A product never surfaces for a
  profile it doesn't list.
- When no product applies to the profile, `SellOpportunities.note` explains the segment isn't
  covered — an advisor must never read "no recommendations" as "no weak areas".

## Acceptance

Wealth/exchange assessments get zero recommendations + the note; retail behaviour unchanged.
