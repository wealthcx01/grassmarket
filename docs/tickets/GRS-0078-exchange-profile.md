# GRS-0078 — Exchange operating-model profile (content)

**Status:** Shipped
**Loop:** Loop 7 — Operating-model profiles
**Depends on:** ADR-0025, GRS-0077 (mechanism)
**Branch:** `grs-0078-exchange-profile`

## Why

Exchange-first (D-3): the active book (ASX, NSE) is exchange-side. An exchange runs infrastructure
the retail L taxonomy never names — matching engine, market surveillance, member connectivity,
clearing & settlement, market-data distribution. GRS-0077 built the profile mechanism; this ticket
fills it with the exchange content.

## What shipped

**`profiles.yaml` — the `exchange` profile:**
- Selects **8 of the 9** superset modules (drops `CMS` — a retail client-management system is not an
  exchange concern), in superset order.
- **Subcomponent additions** (market infrastructure, keys `<MODULE>_<LEAF>`): `OEMS_MATCHING_ENGINE`
  (critical), `BACKOFFICE_MARKET_SURVEILLANCE` (critical), `EMS_GATEWAY_MEMBER_CONNECTIVITY`,
  `LIQ_CONNECT_CLEARING_SETTLEMENT_IF`, `MARKET_DATA_DISTRIBUTION`.
- **Critical override:** `OEMS_PRE_TRADE_RISK` → non-critical (a broker's pre-trade gate isn't the
  exchange's critical control — the matching engine is).
- Additions/overrides live in the profile, so the **superset `modules.yaml` and the golden master are
  untouched** (retail reproduces `V = 0.478565`).

**Coefficients (`atlas/draft_coefficients.py`):** `draft_v1_coefficient_set` generalised to take a
`critical_modules_for_l` + `version` (retail defaults unchanged, byte-identical). New
`draft_exchange_coefficient_set` — a **draft** set (`client_usable=False`) covering the exchange view
exactly, with exchange criticals `(APP_SERVER, OEMS, LIQ_CONNECT)` and a distinct
`exchange-v1-draft-pending-elicitation` version. `profile_scoring_context("exchange")` routes it.

## Guardrails

- **No N/A-stretching:** an exchange assessment scores over the exchange module set; no retail-only
  (`CMS_*`) subcomponent appears in the run.
- **Never pooled across profiles:** the exchange and retail coefficient sets are **mutually
  incompatible** (`validate_against` refuses each on the other's view), so an exchange's L can never
  be silently scored/pooled under broker coefficients. Benchmark rows carry the distinct exchange
  `coefficient_version`, so the population is segmentable — the profile-filtered benchmark *comparison*
  lands with GRS-0084.
- **Draft, not ratified:** `client_usable=False`, structure authored from the ASX/NSE engagement
  packs (reference-only, never committed); criticals layer over a base set still
  `draft-pending-ratification`. The exchange weight-elicitation panel refines it (same activation seam
  as retail).

## Tests

`tests/test_exchange_profile.py` — exchange view selects market-infra not CMS; criticals reflect the
matching engine + surveillance; coeff set covers the view with exchange criticals + distinct version;
an exchange assessment scores end-to-end; coeff sets mutually incompatible (no pooling); retail
unchanged; unknown profile fails loud. Golden master + property tests green.

## Not in scope

- Wealth/advisory + infrastructure-vendor profiles (later).
- Eliciting real exchange weights (θ panel) — draft only.
- Wizard selector — GRS-0079. Profile-filtered benchmark comparison — GRS-0084.
