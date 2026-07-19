# GRS-0147d — Wealth infrastructure taxonomy (ADR-0035 Phase 3, completion)

**Status:** Implemented (2026-07-19). Ships **draft / not-client-usable** (Phase-4 elicitation is
founder/panel-gated).
**Loop:** Part 2 — segment-fit remediation (from the persona re-run measurement)

## Why

The re-run measurement showed the wealth model, shipped **metric-deep only** (GRS-0147c), *lowered*
the two wealth personas' confidence (Tom 55→46, James 68→58): they praised the wealth metrics but the
**Infrastructure Deep Dive — the bulk of the scored subcomponents — was still retail** (OEMS,
watchlists, time-to-first-trade), because `for_profile` *added* wealth subcomponents without *removing*
the retail ones. "A retail template with a wealth cover sheet." This makes the infra taxonomy
wealth-native.

## What changed (additive; retail/exchange + golden master byte-identical)

- **Profile mechanism (`registry.py`)** — `ProfileDef` gains two per-module levers, mirroring the
  metric mechanism: `subcomponent_selection` (keep ONLY these superset subs on a module; an empty list
  drops all retail subs) and `module_name_overrides` (rename a module for the operating model). Both
  keep the module **keys** unchanged, so scoring and `scoreability_blockers` — which address modules by
  key — still resolve, and no scoring/golden-master change is possible. Retail/exchange set neither.
- **Wealth profile (`profiles.yaml`)** — each of the 7 wealth modules now drops its retail
  subcomponents, is renamed wealth-native (Client Portal & Planning; Platform & AUM Economics;
  Investment Data & Research; Advice Workflow & Investment Governance; Client Management & Suitability;
  Custody, Settlement & CASS; Portfolio Management & Dealing), and carries **26 authored wealth
  subcomponents** (suitability/COBS-9A, custody/CASS, model portfolios & rebalancing, financial
  planning, adviser workflow, PROD governance, …). Criticals: platform resilience, suitability,
  custody/CASS. Zero retail-subcomponent leak into the wealth view.

## Acceptance
- A wealth assessment's Infrastructure Deep Dive reads entirely wealth-native (no OEMS/watchlists);
  the wealth view scores end-to-end; the wealth criticals are suitability + custody + resilience.
  Retail view byte-identical, golden master V=0.478565 unchanged; 782 backend tests + schema + ruff +
  pyright green. The wizard renders it with no frontend change.
- Still Phase-4-gated: the "indicative, not client-usable" banner remains until the wealth
  weight/critical elicitation panel runs.
