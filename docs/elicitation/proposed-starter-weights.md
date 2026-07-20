# Proposed STARTER weights — wealth & exchange (for founder review)

**Status:** Draft starter values for review — **NOT ratified, NOT activated.** These are an engineering
proposal to seed the panel (ADR-0037); the profiles still score with the uniform draft set and the
"indicative, not client-usable" banner stays until you ratify + I flip the activation seam. Weights are
**relative** (the engine normalises); read them as "how much more/less than the others."

Rationale principle: weight highest what a **sophisticated buyer in that segment would stake the
franchise on**, and what a **regulator would treat as a critical control**.

---

## WEALTH — proposed starter

### Headline θ (sum = 1.00)
| θ_B | θ_P | θ_L | Rationale |
|---|---|---|---|
| **0.35** | **0.30** | **0.35** | A wealth firm's value is its *franchise economics* (AUM, margin, retention → B) and *moats* (switching costs, brand → P) as much as its platform. B nudged above the retail 0.30; L trimmed from 0.40 (wealth is less tech-differentiated than a broker, but custody/suitability is a real floor). |

### α (bottleneck aggression)
| α_l | α_module | Rationale |
|---|---|---|
| **0.75** | **0.70** | Slightly more bottleneck-weighted than retail (0.70): in a regulated wealth firm a single failed critical control (a CASS breach, a suitability failure) should drag the score hard. |

### Module weights δ (relative)
| Module | δ | Why |
|---|---|---|
| Custody, Settlement & CASS (BACKOFFICE) | **1.5** | Client-asset protection — the #1 regulatory risk. |
| Client Management & Suitability (CMS) | **1.4** | COBS 9A suitability — the redress-liability core. |
| Platform & AUM Economics (APP_SERVER) | **1.2** | Resilience + fee integrity underpin everything. |
| Portfolio Management & Dealing (OEMS) | **1.1** | MPS/rebalancing/best-ex — the investment engine. |
| Advice Workflow & Investment Governance (ORCHESTRATION) | **1.0** | PROD/CIO governance. |
| Client Portal & Planning (FRONTEND) | **0.8** | Important, but table-stakes and less differentiating. |
| Investment Data & Research (MARKET_DATA) | **0.7** | Largely commoditised / outsourced. |

### Critical-for-L (gate the L index)
Keep the draft: **APP_SERVER (platform resilience), CMS (suitability), BACKOFFICE (custody/CASS)** — the
three a regulator would call load-bearing. *(Open question for the panel: is Portfolio Management also
critical?)*

### B — group weights + within-group metric weights
| Group | weight | Metrics (weight) |
|---|---|---|
| unit_economics | **1.2** | Revenue margin bps **1.3**, Cost/income **1.2**, AUM/adviser **1.0**, Recurring-rev % **1.0** — margin durability under Consumer Duty is the value driver. |
| scale | **1.0** | AUM **1.5**, Adviser headcount **1.0**, Client count **0.8** — AUM is the headline. |
| momentum | **1.0** | Net-new-money rate **1.5**, Retention **1.2**, AUM growth **0.8** — organic NNM strips market beta; total AUM growth is noisier. |

### Power weights w_power
Switching Costs **1.5**, Branding **1.4**, Scale Economies **1.1**, Process Power **1.0**, Cornered
Resource **0.9**, Counter-Positioning **0.8**, Network Economies **0.7** — sticky advice relationships +
trusted brand are the wealth moats; network effects are weak.

### Strength encoding
None **0.0** / Emerging **0.35** / Established **0.70** / Wide **1.0** — same convex curve retail elicited
uses (a real moat is worth much more than an emerging one).

---

## EXCHANGE — proposed starter

### Headline θ (sum = 1.00)
| θ_B | θ_P | θ_L | Rationale |
|---|---|---|---|
| **0.25** | **0.35** | **0.40** | An exchange *is* its infrastructure (matching engine, clearing, uptime → L) and its network moat (liquidity, listings lock-in → P). B trimmed — volume is cyclical and increasingly commoditised; the durable value is the toll-booth + the moat. |

### α
| α_l | α_module | Rationale |
|---|---|---|
| **0.80** | **0.70** | Most bottleneck-sensitive of the three: a matching-engine or clearing failure is systemic — one weak critical must dominate. |

### Module weights δ (relative)
| Module | δ | Why |
|---|---|---|
| Matching Engine (OEMS) | **1.5** | The heart of the venue. |
| Core Trading Platform (APP_SERVER) | **1.4** | Uptime/resilience — a systemic obligation. |
| Clearing & Settlement (LIQ_CONNECT) | **1.3** | CCP risk / settlement finality. |
| Post-Trade & Surveillance (BACKOFFICE) | **1.1** | Regulatory market-integrity imperative. |
| Market-Data Dissemination (MARKET_DATA) | **1.0** | A growing revenue + fairness surface. |
| Member Connectivity (EMS_GATEWAY) | **0.9** | Gateways/colocation. |
| Trading Operations & Controls (ORCHESTRATION) | **0.8** | Operational, less differentiating. |
| Member Front-End & APIs (FRONTEND) | **0.6** | Members mostly connect via API. |

### Critical-for-L
Draft is **APP_SERVER, OEMS, LIQ_CONNECT**. **Proposed: add BACKOFFICE (surveillance)** — for a
systemically-regulated venue, market-integrity surveillance is load-bearing → critical set of four.

### B — group weights + metric weights
| Group | weight | Metrics (weight) |
|---|---|---|
| scale | **1.2** | ADV **1.4**, Data revenue **1.3**, Open interest **1.2**, IPOs won **0.8** — volume + the recurring data toll-booth. |
| unit_economics | **1.1** | EBITDA margin **1.3**, Take rate **1.2**, Recurring-rev % **1.2** — toll-booth economics + de-risking. |
| momentum | **0.9** | Net-revenue growth **1.2**, Volume growth **0.8** — revenue growth is more durable than cyclical volume. |

### Power weights w_power
Network Economies **1.6**, Switching Costs **1.4**, Scale Economies **1.2**, Cornered Resource **1.2**
(index/data franchises, licences), Process Power **0.9**, Branding **0.9**, Counter-Positioning **0.8** —
liquidity network effects + listing/clearing lock-in are the exchange moat.

### Strength encoding
None **0.0** / Emerging **0.35** / Established **0.70** / Wide **1.0** (same as wealth/retail).

---

## What I need from you
Mark up anything you'd change (these are starters, not gospel). On your approval I'll (1) wire them into
`elicited_wealth/exchange_coefficient_set` with a provenance record, gated OFF; (2) show you the **scored
effect** (V for a strong vs weak illustrative firm under these vs the uniform draft, to sanity-check
they discriminate sensibly); and only then, on your sign-off, (3) flip the activation seam to
client-usable — one recorded commit per profile.
