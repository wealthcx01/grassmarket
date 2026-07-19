# GRS-0147c — Wealth operating model (ADR-0035 Phase 3)

**Status:** Implemented (2026-07-19) — ADR-0035 Phase 3. Ships **draft / not-client-usable** (Phase 4
elicitation is founder/panel-gated).
**Loop:** Part 2 — segment-fit remediation

## Why

The loudest, most cross-cutting stress-test finding: there was **no wealth operating model**, so both
wealth personas had to mislabel their firm as "Retail brokerage" and were scored on retail
AUA/ARPU/OEMS — while the Academy treats "wealth manager" as first-class. ADR-0025 already ratified a
wealth profile; Phase 2 (GRS-0147b) added the per-profile-metric mechanism that makes a wealth-native
B index possible without touching the retail golden master. This authors the content.

## What changed (additive; retail/exchange unchanged; golden master byte-identical)

- **`profiles.yaml` `wealth` block** — selects the advisory-relevant modules (drops the brokerage/
  exchange EMS member-gateway + liquidity-connectivity), adds wealth-native infra subcomponents
  (suitability/COBS-9A + custody/CASS as criticals; mandate mix, AUM economics, financial planning,
  investment governance/PROD), overrides the broker pre-trade-risk gate non-critical, and — via the
  Phase-2 levers — sets `metrics: []` + `metric_additions` = the **wealth B metric set**: AUM,
  adviser headcount, client count, revenue margin (bps), cost/income, AUM-per-adviser, recurring-
  revenue %, **net-new-money rate** (signed), AUM growth (signed), retention. Anchors pinned to
  FY2024 UK wealth peers; each carries GRS-0144 domain bounds (magnitudes `min_raw:0`, the two
  signed metrics unbounded).
- **`draft_wealth_coefficient_set`** (draft_coefficients.py) + `_WEALTH_CRITICAL_MODULES_FOR_L =
  (APP_SERVER, CMS, BACKOFFICE)` — covers the wealth view exactly, `client_usable=False`, a distinct
  `wealth-v1-draft-pending-elicitation` version (benchmark rows segment by profile, never pooled).
- **`profile_scoring_context`** (active.py) routes `wealth` to its draft set, mirroring exchange.
- The `/registry/profiles` selector and `/registry?profile=wealth` view already serve it, so the
  wizard renders the wealth modules + wealth metrics with no frontend change.

## Acceptance
- A wealth assessment scores end-to-end over wealth-native modules + metrics; no retail metric leaks;
  the retail coefficient set is incompatible with the wealth view (fail-loud). Ships with the honest
  "indicative, not client-usable" banner until the Phase-4 wealth elicitation panel. Golden master
  V=0.478565 unchanged; 781 backend tests + schema sync + ruff format/check + pyright green.
