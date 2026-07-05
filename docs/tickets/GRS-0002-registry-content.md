# GRS-0002 — Registry content (subcomponents + business-metric register)

- **Loop:** 1 (see PRD §9)
- **Branch:** `grs-0002-registry-content`
- **Status:** In review
- **Normative sources:** `docs/ATLAS-Methodology-v1.md` §2, §3, §5; ADR-0001.
- **Depends on:** GRS-0001 (merged).

## Goal

Populate the single key registry (ADR-0001) with the **51 subcomponents** across the 9 modules
and a **draft business-metric register**, so the golden master (GRS-0003) and engine (GRS-0004)
have real keys to score against. Everything authored here ships flagged
`draft-pending-ratification` — it is content for John (and, for weights, the elicitation panel)
to ratify, not settled methodology.

## What shipped

- **Contracts extended** (`bcap_contracts.registry`): `SubcomponentDef.description`;
  `MetricDef` now carries `unit`, `direction`, a `NormalisationSpec` (piecewise-linear
  `AnchorPoint`s), and a `status`; `Registry` exposes `subcomponent_status` / `metric_status`.
- **`modules.yaml`** — 51 subcomponents (6/7/7/5/6/6/6/4/4), labels + descriptions from the
  prototype's authoritative draft (`…/bruntsfield_advisory_assessment_wizard_v2/config/
  modules_subcomponents.yaml`), with draft `critical` flags. `status: draft-pending-ratification`.
- **`metrics.yaml`** — 10 draft business metrics with declared units, directions, and
  placeholder normalisation anchors for a mid-tier retail brokerage.
- **Tests** — registry now asserts 51 subcomponents / 10 metrics / draft statuses / every module
  has ≥1 critical subcomponent; a fully-covered `CoefficientSet` validates against the real
  registry; an under-covered one fails loud (`MissingKeyError`).

### GRS-0002a — registry hardening (fail-loud + naming), same PR

- **Required `status`** — the module set, the metric set, and each `MetricDef` read `status` by
  bracket access; a status-less dataset refuses to load (`RegistryError`), never defaults to
  `"settled"`. (Removed the last `.get(key, default)` on the registry path.)
- **Closed key-like sets** — `MetricDef.direction` ∈ {`higher_is_better`, `lower_is_better`},
  `NormalisationSpec.method` ∈ {`piecewise_linear`, `percentile`}, `MetricDef.group` ∈
  {`scale`, `unit_economics`, `momentum`} or `None`, all as `Literal` types: a typo is a
  load-time refusal (and carries into the JSON-Schema/TS mirror as an enum).
- **Anchor invariants on `NormalisationSpec`** (not one test row): a `piecewise_linear` curve must
  carry anchors; raws strictly ascending; normalised monotonic; and the curve's slope must agree
  with `MetricDef.direction`. `normalisation` is now a required field.
- **Naming** — all 51 subcomponent keys fully qualified to `<MODULE_KEY>_<LEAF>` with **global**
  uniqueness enforced in `_assert_unique_keys` (see §2 below for the list).
- **Housekeeping** — removed `REVIEW-PROMPT.md` (unrelated to this PR's diff).

## ⚠️ For John to ratify

### 1. Draft critical-subcomponent flags (drive the rating gate, §5.2)

A module cannot be reported **Advanced** if any *critical* subcomponent is Basic, nor **Frontier**
unless all critical are Advanced+ at E3+. These are my domain-reasoned proposals — please confirm
or adjust:

| Module | Proposed critical subcomponents | Rationale |
|---|---|---|
| FRONTEND | `FRONTEND_PERFORMANCE`, `FRONTEND_UX_NAVIGATION` | The client-facing product fails if core task flows or p95 latency fail. |
| APP_SERVER | `APP_SERVER_RESILIENCE_DR`, `APP_SERVER_SECURITY_COMPLIANCE` | A core platform that isn't recoverable or secure isn't "advanced" at any breadth. |
| MARKET_DATA | `MARKET_DATA_DEPTH_QUALITY`, `MARKET_DATA_LATENCY_TIMELINESS` | Wrong or late data poisons everything downstream. |
| ORCHESTRATION | `ORCHESTRATION_WORKFLOW_ENGINE` | The engine is the module; the rest are refinements. |
| CMS | `CMS_CRM_MODEL` | An incoherent CRM data model caps the whole client layer. |
| BACKOFFICE | `BACKOFFICE_CUSTODY`, `BACKOFFICE_REG_REPORTING` | Custody integrity and regulatory reporting are non-negotiable. |
| OEMS | `OEMS_PRE_TRADE_RISK` | Executing without pre-trade risk is a regulatory/again-loss red line. |
| EMS_GATEWAY | `EMS_GATEWAY_RISK_THROTTLING` | The gateway's job is safe throttled access; without it, breadth is irrelevant. |
| LIQ_CONNECT | `LIQ_CONNECT_LOCAL_EXCHANGES`, `LIQ_CONNECT_SETTLEMENT_CLEARING` | Can't trade or settle → the module is not "advanced". |

### 2. Subcomponent key inconsistency — RESOLVED in GRS-0002a

The prototype mixed bare (`PERFORMANCE`, `CUSTODY`) and prefixed (`OEMS_LATENCY_RELIABILITY`,
`EMS_CONNECTIVITY`, `ORCH_MONITORING`) forms. **John chose the consistent scheme**, so every key is
now fully qualified to `<MODULE_KEY>_<LEAF>` (GRS-0002a): the module-echo is stripped from the leaf
before prefixing and an immediately-repeated token is collapsed (`MARKET_DATA` + `DATA_DEPTH_QUALITY`
→ `MARKET_DATA_DEPTH_QUALITY`; `ORCH_MONITORING` → `ORCHESTRATION_MONITORING`; `EMS_CONNECTIVITY` →
`EMS_GATEWAY_CONNECTIVITY`). Global uniqueness is enforced at load time (`_assert_unique_keys`).

**The final 51 keys (please glance):**

- **FRONTEND (6):** `FRONTEND_PERFORMANCE`*, `FRONTEND_UX_NAVIGATION`*, `FRONTEND_DEVICE_COVERAGE`,
  `FRONTEND_PERSONALISATION`, `FRONTEND_ACCESSIBILITY_LOCALISATION`, `FRONTEND_EXPERIMENTATION_ANALYTICS`
- **APP_SERVER (7):** `APP_SERVER_HOSTING_ELASTICITY`, `APP_SERVER_RESILIENCE_DR`*,
  `APP_SERVER_API_DESIGN`, `APP_SERVER_SECURITY_COMPLIANCE`*, `APP_SERVER_DEVOPS_DEPLOYMENT`,
  `APP_SERVER_DATA_ARCHITECTURE`, `APP_SERVER_OBSERVABILITY`
- **MARKET_DATA (7):** `MARKET_DATA_EXCHANGE_COVERAGE`, `MARKET_DATA_INSTRUMENT_UNIVERSE`,
  `MARKET_DATA_DEPTH_QUALITY`*, `MARKET_DATA_LATENCY_TIMELINESS`*, `MARKET_DATA_HISTORY_DEPTH`,
  `MARKET_DATA_VENDOR_REDUNDANCY`, `MARKET_DATA_VALUE_ADD_SERVICES`
- **ORCHESTRATION (5):** `ORCHESTRATION_WORKFLOW_ENGINE`*, `ORCHESTRATION_ROUTING_LOGIC`,
  `ORCHESTRATION_EVENT_DRIVEN`, `ORCHESTRATION_CONFIG_VS_CODE`, `ORCHESTRATION_MONITORING`
- **CMS (6):** `CMS_RESEARCH_AUTHORING`, `CMS_RESEARCH_DISTRIBUTION`, `CMS_EMAIL_CAMPAIGNS`,
  `CMS_CRM_MODEL`*, `CMS_STATEMENTS`, `CMS_CONTENT_SEARCH_PERSONALISATION`
- **BACKOFFICE (6):** `BACKOFFICE_CUSTODY`*, `BACKOFFICE_PAYMENTS_FUNDING`, `BACKOFFICE_KYC_ONBOARDING`,
  `BACKOFFICE_PORTFOLIO_MGMT`, `BACKOFFICE_CREDIT_RISK`, `BACKOFFICE_REG_REPORTING`*
- **OEMS (6):** `OEMS_ASSET_COVERAGE`, `OEMS_EXEC_ALGOS`, `OEMS_PRE_TRADE_RISK`*, `OEMS_ORDER_TYPES`,
  `OEMS_LATENCY_RELIABILITY`, `OEMS_APIS_COLOCATION`
- **EMS_GATEWAY (4):** `EMS_GATEWAY_CONNECTIVITY`, `EMS_GATEWAY_ROUTING_POLICY`,
  `EMS_GATEWAY_RISK_THROTTLING`*, `EMS_GATEWAY_MONITORING`
- **LIQ_CONNECT (4):** `LIQ_CONNECT_LOCAL_EXCHANGES`*, `LIQ_CONNECT_FOREIGN_BROKERS`,
  `LIQ_CONNECT_FUND_HOUSES`, `LIQ_CONNECT_SETTLEMENT_CLEARING`*

`*` = draft critical (gates the module rating, §5.2 — see §1 above).

### 3. Draft business-metric register (10 metrics)

`AUA`, `ACTIVE_CLIENTS`, `NET_REVENUE`, `REVENUE_PER_CLIENT`, `GROSS_MARGIN`, `COST_TO_SERVE`,
`NET_REVENUE_RETENTION`, `CLIENT_GROWTH_RATE`, `TAKE_RATE_DURABILITY`, `CAC_PAYBACK_MONTHS`. Units
and directions are declared; the **normalisation anchor values are placeholders** for a mid-tier
retail brokerage pending your Stage-1 judgement (they become percentile-vs-benchmark from Stage 2,
§11). Please sanity-check the metric *set* and the anchor bands.

## Out of scope

Rubric anchors (204 — separate content track), elicited weights (the panel; replaces the draft
`CoefficientSet`), and the engine itself (GRS-0004). No scoring code in this ticket.
