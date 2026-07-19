# GRS-0147g — Exchange operating model, made native (ADR-0035, exchange completion)

**Status:** Implemented (2026-07-19). Ships **draft / not-client-usable** (Phase-4 elicitation is
founder/panel-gated).
**Loop:** Part 2 — segment-fit remediation

## Why

The two exchange personas (LSEG, Deutsche Börse) hit the identical gap the wealth personas did before
GRS-0147d: the exchange profile added a few market-infra subcomponents but **kept the retail ones**
and was still scored on **retail AUA/ARPU metrics** — "a retail template" for a venue that runs a
matching engine and clears trades. GRS-0147d built the mechanism (per-profile metrics + per-module
subcomponent selection + module renames); this applies it to exchange, mirroring wealth.

## What changed (additive; retail/wealth + golden master byte-identical)

- **`profiles.yaml` exchange block** — each of the 8 exchange modules drops its retail subcomponents
  (`subcomponent_selection: []`), is renamed venue-native (Matching Engine; Core Trading Platform;
  Market-Data Dissemination; Member Connectivity; Clearing & Settlement; Post-Trade & Surveillance;
  Trading Operations & Controls; Member Front-End & APIs), and carries **24 exchange subcomponents**
  (matching/auction engine, latency & determinism, platform uptime, market-data fairness, clearing
  risk & margin, settlement finality, surveillance, member connectivity/colocation…). Criticals:
  platform uptime, matching engine, market surveillance. **Zero retail-sub leak.**
- **Exchange B index** — `metrics: []` + `metric_additions` = the venue metric set (ADV, open
  interest/cleared notional, IPOs won, index & market-data revenue, take rate, EBITDA margin [signed],
  recurring-revenue %, net-revenue growth [signed], volume growth [signed]) with FY2024-peer anchors +
  GRS-0144 domain bounds. No retail metric leak; currency USD-appropriate units.
- The `draft_exchange_coefficient_set` + `active.py` routing already existed and now cover the native
  view exactly.

## Acceptance
- An exchange assessment's Infrastructure Deep Dive + B index read entirely venue-native; the exchange
  view scores end-to-end; no retail sub/metric leaks; the retail/exchange coefficient sets stay
  mutually incompatible (fail-loud). Retail/wealth views byte-identical; golden master V=0.478565
  unchanged; 784 backend tests + schema + ruff + pyright green. Wizard renders it with no frontend
  change. Phase-4 elicitation still gates client-usability.
