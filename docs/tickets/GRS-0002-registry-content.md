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

## ⚠️ For John to ratify

### 1. Draft critical-subcomponent flags (drive the rating gate, §5.2)

A module cannot be reported **Advanced** if any *critical* subcomponent is Basic, nor **Frontier**
unless all critical are Advanced+ at E3+. These are my domain-reasoned proposals — please confirm
or adjust:

| Module | Proposed critical subcomponents | Rationale |
|---|---|---|
| FRONTEND | `PERFORMANCE`, `UX_NAVIGATION` | The client-facing product fails if core task flows or p95 latency fail. |
| APP_SERVER | `RESILIENCE_DR`, `SECURITY_COMPLIANCE` | A core platform that isn't recoverable or secure isn't "advanced" at any breadth. |
| MARKET_DATA | `DATA_DEPTH_QUALITY`, `LATENCY_TIMELINESS` | Wrong or late data poisons everything downstream. |
| ORCHESTRATION | `WORKFLOW_ENGINE` | The engine is the module; the rest are refinements. |
| CMS | `CRM_MODEL` | An incoherent CRM data model caps the whole client layer. |
| BACKOFFICE | `CUSTODY`, `REG_REPORTING` | Custody integrity and regulatory reporting are non-negotiable. |
| OEMS | `PRE_TRADE_RISK` | Executing without pre-trade risk is a regulatory/again-loss red line. |
| EMS_GATEWAY | `EMS_RISK_THROTTLING` | The gateway's job is safe throttled access; without it, breadth is irrelevant. |
| LIQ_CONNECT | `LOCAL_EXCHANGES`, `SETTLEMENT_CLEARING` | Can't trade or settle → the module is not "advanced". |

### 2. Subcomponent key inconsistency inherited from the prototype

Keys are preserved **verbatim** from the draft, which mixes bare (`PERFORMANCE`, `CUSTODY`) and
prefixed (`OEMS_LATENCY_RELIABILITY`, `EMS_CONNECTIVITY`, `ORCH_MONITORING`) forms. All 51 are
globally unique, so it works — but if you'd prefer a consistent `MODULE_SUBCOMPONENT` scheme, say
so now (before the golden master references these keys) and I'll normalise in this ticket.

### 3. Draft business-metric register (10 metrics)

`AUA`, `ACTIVE_CLIENTS`, `NET_REVENUE`, `REVENUE_PER_CLIENT`, `GROSS_MARGIN`, `COST_TO_SERVE`,
`NET_REVENUE_RETENTION`, `CLIENT_GROWTH_RATE`, `TAKE_RATE_DURABILITY`, `CAC_PAYBACK_MONTHS`. Units
and directions are declared; the **normalisation anchor values are placeholders** for a mid-tier
retail brokerage pending your Stage-1 judgement (they become percentile-vs-benchmark from Stage 2,
§11). Please sanity-check the metric *set* and the anchor bands.

## Out of scope

Rubric anchors (204 — separate content track), elicited weights (the panel; replaces the draft
`CoefficientSet`), and the engine itself (GRS-0004). No scoring code in this ticket.
