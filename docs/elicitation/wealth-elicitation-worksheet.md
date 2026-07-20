# Wealth profile — weight & critical elicitation worksheet (ADR-0037, Phase 4)

**Panel:** Bruntsfield weight-elicitation panel · **Method:** swing-weighting / Delphi (Methodology §6)
**Profile:** `wealth` · **Instructions:** fill the **Elicited** column for every row. The **Draft**
column is the current uniform placeholder (what the engine scores with today, `client_usable=False`).
Once complete, engineering wires these into `elicited_wealth_coefficient_set` and activates in one
recorded commit (ADR-0022). Every family also needs a one-line **dispersion** note (how much the panel
disagreed) for its provenance record.

## 1. Headline index weights θ (must sum to 1.00)
| Family | Meaning | Draft | **Elicited** |
|---|---|---|---|
| θ_B | Business (metrics) weight in V | 0.30 | ___ |
| θ_P | Power weight in V | 0.30 | ___ |
| θ_L | Infrastructure (L) weight in V | 0.40 | ___ |

## 2. Bottleneck aggression α (per Methodology §5.2)
| Family | Meaning | Draft | **Elicited** |
|---|---|---|---|
| α_l | L-index min-vs-mean blend (1.0 = pure bottleneck) | 0.70 | ___ |
| α_module (per module, or one global) | module q_m min-vs-mean blend | 0.70 | ___ |

## 3. Module weights δ (relative importance across the 7 wealth modules)
| Module | Draft | **Elicited** |
|---|---|---|
| Client Portal & Planning (FRONTEND) | 1.0 | ___ |
| Platform & AUM Economics (APP_SERVER) | 1.0 | ___ |
| Investment Data & Research (MARKET_DATA) | 1.0 | ___ |
| Advice Workflow & Investment Governance (ORCHESTRATION) | 1.0 | ___ |
| Client Management & Suitability (CMS) | 1.0 | ___ |
| Custody, Settlement & CASS (BACKOFFICE) | 1.0 | ___ |
| Portfolio Management & Dealing (OEMS) | 1.0 | ___ |

## 4. Critical-for-L modules (which modules gate the L index)
| Module | Draft critical? | **Elicited critical?** |
|---|---|---|
| Platform & AUM Economics (APP_SERVER) | ✅ | ___ |
| Client Management & Suitability (CMS) | ✅ | ___ |
| Custody, Settlement & CASS (BACKOFFICE) | ✅ | ___ |
| (any other of the 7 the panel deems critical) | — | ___ |

## 5. B-index metric weights w_metric + group weights
Group weights (B is a group-weighted mean, ADR-0006):
| Group | Draft | **Elicited** |
|---|---|---|
| scale | 1.0 | ___ |
| unit_economics | 1.0 | ___ |
| momentum | 1.0 | ___ |

Per-metric weights within each group:
| Metric | Group | Draft | **Elicited** |
|---|---|---|---|
| WEALTH_AUM (AUM) | scale | 1.0 | ___ |
| WEALTH_ADVISER_HEADCOUNT | scale | 1.0 | ___ |
| WEALTH_CLIENT_COUNT | scale | 1.0 | ___ |
| WEALTH_REVENUE_MARGIN_BPS | unit_economics | 1.0 | ___ |
| WEALTH_COST_INCOME | unit_economics | 1.0 | ___ |
| WEALTH_AUM_PER_ADVISER | unit_economics | 1.0 | ___ |
| WEALTH_RECURRING_REV_PCT | unit_economics | 1.0 | ___ |
| WEALTH_NET_NEW_MONEY_RATE | momentum | 1.0 | ___ |
| WEALTH_AUM_GROWTH | momentum | 1.0 | ___ |
| WEALTH_RETENTION | momentum | 1.0 | ___ |

## 6. Power weights w_power (the 7 Helmer powers, shared across profiles)
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
| Level | Draft | **Elicited** (retail elicited used 0 / 0.35 / 0.70 / 1.0) |
|---|---|---|
| None | 0.0 | ___ |
| Emerging | 0.5 | ___ |
| Established | 0.8 | ___ |
| Wide | 1.0 | ___ |

---
**Sign-off:** panel name ______ · date ______ · review-due (annual) ______ · dispersion summary ______
