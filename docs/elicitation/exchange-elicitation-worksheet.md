# Exchange profile — weight & critical elicitation worksheet (ADR-0037, Phase 4)

**Panel:** Bruntsfield weight-elicitation panel · **Method:** swing-weighting / Delphi (Methodology §6)
**Profile:** `exchange` · **Instructions:** fill the **Elicited** column for every row. The **Draft**
column is the current uniform placeholder the engine scores with today (`client_usable=False`). Once
complete, engineering wires these into `elicited_exchange_coefficient_set` and activates in one
recorded commit (ADR-0022). Each family needs a **dispersion** note for its provenance record.

## 1. Headline index weights θ (must sum to 1.00)
| Family | Meaning | Draft | **Elicited** |
|---|---|---|---|
| θ_B | Business (metrics) weight in V | 0.30 | ___ |
| θ_P | Power weight in V | 0.30 | ___ |
| θ_L | Infrastructure (L) weight in V | 0.40 | ___ |

## 2. Bottleneck aggression α
| Family | Meaning | Draft | **Elicited** |
|---|---|---|---|
| α_l | L-index min-vs-mean blend (1.0 = pure bottleneck) | 0.70 | ___ |
| α_module | module q_m min-vs-mean blend | 0.70 | ___ |

## 3. Module weights δ (across the 8 exchange modules)
| Module | Draft | **Elicited** |
|---|---|---|
| Member Front-End & APIs (FRONTEND) | 1.0 | ___ |
| Core Trading Platform (APP_SERVER) | 1.0 | ___ |
| Market-Data Dissemination (MARKET_DATA) | 1.0 | ___ |
| Trading Operations & Controls (ORCHESTRATION) | 1.0 | ___ |
| Post-Trade & Surveillance (BACKOFFICE) | 1.0 | ___ |
| Matching Engine (OEMS) | 1.0 | ___ |
| Member Connectivity (EMS_GATEWAY) | 1.0 | ___ |
| Clearing & Settlement (LIQ_CONNECT) | 1.0 | ___ |

## 4. Critical-for-L modules (which modules gate L)
| Module | Draft critical? | **Elicited critical?** |
|---|---|---|
| Core Trading Platform (APP_SERVER) | ✅ | ___ |
| Matching Engine (OEMS) | ✅ | ___ |
| Clearing & Settlement (LIQ_CONNECT) | ✅ | ___ |
| Post-Trade & Surveillance (BACKOFFICE) | — | ___ |

## 5. B-index metric weights w_metric + group weights
Group weights:
| Group | Draft | **Elicited** |
|---|---|---|
| scale | 1.0 | ___ |
| unit_economics | 1.0 | ___ |
| momentum | 1.0 | ___ |

Per-metric weights:
| Metric | Group | Draft | **Elicited** |
|---|---|---|---|
| EXCH_ADV (average daily volume) | scale | 1.0 | ___ |
| EXCH_OPEN_INTEREST (open interest / cleared notional) | scale | 1.0 | ___ |
| EXCH_IPOS_WON (IPOs / listings won) | scale | 1.0 | ___ |
| EXCH_DATA_REVENUE (index & market-data revenue) | scale | 1.0 | ___ |
| EXCH_TAKE_RATE (revenue per contract) | unit_economics | 1.0 | ___ |
| EXCH_EBITDA_MARGIN | unit_economics | 1.0 | ___ |
| EXCH_RECURRING_REV_PCT | unit_economics | 1.0 | ___ |
| EXCH_NET_REVENUE_GROWTH | momentum | 1.0 | ___ |
| EXCH_VOLUME_GROWTH | momentum | 1.0 | ___ |

## 6. Power weights w_power (shared 7 Helmer powers)
| Power | Draft | **Elicited** |
|---|---|---|
| Branding | 1.0 | ___ |
| Cornered Resource | 1.0 | ___ |
| Counter-Positioning | 1.0 | ___ |
| Network Economies | 1.0 | ___ |
| Process Power | 1.0 | ___ |
| Scale Economies | 1.0 | ___ |
| Switching Costs | 1.0 | ___ |

## 7. Strength encoding (None/Emerging/Established/Wide → score)
| Level | Draft | **Elicited** |
|---|---|---|
| None | 0.0 | ___ |
| Emerging | 0.5 | ___ |
| Established | 0.8 | ___ |
| Wide | 1.0 | ___ |

---
**Sign-off:** panel name ______ · date ______ · review-due (annual) ______ · dispersion summary ______
