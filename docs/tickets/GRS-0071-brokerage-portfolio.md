# GRS-0071 — "Your Brokerages" portfolio home

**Status:** Shipped
**Loop:** Track A (guided consulting UX — delivery review §4, NEXT-STEPS §3.6)
**Branch:** `grs-0071-brokerage-portfolio`

## Why

The delivery review asked for a "Your Brokerages" portfolio home (segment / last score / last
updated) — an at-a-glance book of the advisor's assessments, rather than a flat list of card tiles.
The assessments index showed only subject + state + updated time, and had no score column because the
list endpoint doesn't carry V (that lives on the immutable scoring run).

## What shipped

**Contract:** new `BrokeragePortfolioEntry` (assessment_id, subject, segment, state, `v_index` P50,
`uncertainty_rating`, finalised_at, updated_at). `v_index` is None until finalised — a draft has no
immutable score, and we never fabricate one. Registered for schema export (parity green).

**Repository:** `list_brokerage_portfolio(principal)` — one row per assessment, newest-touched first,
each carrying its segment (from `document.profile`) and, when finalised, its last V + uncertainty
from the scoring run. **Reuses `list_assessments` for scoping**, so the owner-only guarantee
(CLAUDE.md #9) is inherited, not re-implemented.

**Endpoint:** `GET /assessments/portfolio`, declared before `/{assessment_id}` so "portfolio" isn't
parsed as a UUID (same guard as `/rating-requests`).

**Frontend:** the assessments index becomes the **Your Brokerages** portfolio — a table
(Brokerage · Segment · Last score · Status · Last updated), the create form retained. Last score
shows V (0–100) with the uncertainty rating as a chip, or "—" for an unfinalised assessment. Dashboard
tile relabelled to match.

## Guardrails

- Owner-scoped through the reused `list_assessments` path — proven by `test_scoping` + the new test.
- No scoring behaviour change; the score shown is the finalised run's V, read-only.

## Tests

`tests/test_brokerage_portfolio.py` — owner-scoping + segment surfacing (null when unset, never
fabricated), no score until finalised, newest-first ordering. Backend scoping/schema/lifecycle subset
(30) + parity green; frontend type-check · lint · vitest green.

## Not in scope

- House deliverable types — GRS-0072/0073.
- Operating-model profile selector — Track B.
