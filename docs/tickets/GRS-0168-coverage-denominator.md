# GRS-0168 — Portfolio coverage measured against the assessment's own profile view

**Status:** Done (2026-07-23). Staging-rerun finding (4/5 personas). **Loop:** rerun remediation.

## Why

`list_brokerage_portfolio` computed coverage against the FULL registry's subcomponent count, so a
fully-rated 24-subcomponent exchange assessment showed "Completeness 47%" (24/51) on the portfolio
row and engagement card while the wizard said "24/24 — 100% of applicable". Confirmed in source.

## Fix

- `_document_coverage` takes the assessment's profile REGISTRY VIEW: assessed / (view's applicable
  subcomponents), rows outside the view ignored — the same denominator the wizard uses.
- Portfolio column relabelled "Completeness" → "Coverage" (one word, one number, everywhere).

## Acceptance

A fully-rated profile-scoped assessment shows 100% coverage on every surface; retail unchanged
(its view IS the superset).
