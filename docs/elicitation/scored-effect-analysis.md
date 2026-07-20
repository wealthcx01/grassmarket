# Scored effect — draft (uniform) vs research-refined elicited weights (GRS-0150)

Illustrative firms scored under each profile's **draft** (uniform) coefficient set and the
**research-refined elicited starter** set (`elicited_{wealth,exchange}_coefficient_set`, gated off).
Powers strong = (Wide benefit, Wide barrier); metrics at their best/worst anchor; "weak on a critical
control" = all Frontier **except** the critical-for-L module subcomponents set to Basic.

## Wealth (θ 0.35/0.30/0.35 draft → **0.45/0.30/0.25** elicited)
| Firm | Draft V | Elicited V | Δ |
|---|---|---|---|
| Strong (all Frontier, strong metrics + powers) | 97.5 | 96.3 | −1.2 |
| Strong **except weak on a critical control** | 75.1 | **81.2** | **+6.1** |
| Weak (all Basic) | 25.2 | 23.1 | −2.2 |

## Exchange (θ 0.25/0.35/0.40 draft → **0.30/0.37/0.33** elicited)
| Firm | Draft V | Elicited V | Δ |
|---|---|---|---|
| Strong (all Frontier, strong metrics + powers) | 100.0 | 100.0 | 0.0 |
| Strong **except weak on a critical control** | 79.2 | **81.7** | **+2.5** |
| Weak (all Basic) | 21.0 | 20.6 | −0.4 |

## What the numbers say

**Good:** the weights discriminate cleanly — strong firms ~96–100, weak firms ~21–25 — and the
non-uniform δ/w_metric/w_power flow through the engine (the sets are provably distinct from the draft).

**The important finding — a genuine design decision surfaced:** a firm that is strong everywhere
**except a critical infrastructure control (a CASS/custody failure for wealth, a clearing failure for
exchange) scores HIGHER under the research-refined weights** (+6.1 wealth, +2.5 exchange). Why? The
research lowered **θ_L** (wealth 0.40→0.25, exchange 0.40→0.33) because, *for enterprise value*,
infrastructure is hygiene already priced into B's cost/income — so a firm weak *only* on infra is worth
almost as much. The critical-module gate + high α_l still drag **L** down correctly; but with θ_L low,
that low L barely moves **V**.

This is the **"what is ATLAS *for*?"** question made concrete:
- **Enterprise-value proxy** ("what is this platform worth?"): the research weights are right — a CASS
  weakness is a *risk*, not a write-off of value.
- **Operational-maturity / soundness assessment** ("is this platform safe to trust?"): a critical-
  control failure *should* tank the score — which argues for **keeping θ_L higher** (wealth 0.40/0.30/
  0.30, exchange 0.25/0.35/0.40), or adding a **hard cap** so any Basic critical control gates V
  directly, independent of θ_L.

## Resolution — the critical-control cap (ADR-0038, shipped)

Founder decision: **keep the research EV-leaning θ AND add an explicit critical-control cap** (option
(b)), so the moat/economics-lead-value evidence and the "a failed critical control must show" product
guarantee coexist. The engine now applies, when a set carries a cap floor κ:

```
cap = κ + (1 − κ) · min(q_m over critical-for-L modules);   V = min(V_weighted, cap)
```

Both segment starter sets carry **κ = 0.5** (a broken critical control caps V at ≈60/100). The cap is
opt-in (κ absent ⇒ V byte-identical; retail golden master untouched), recorded on the result
(`CriticalControlCapResult`), and monotone. Re-scored effect **with the cap active**:

### Wealth (κ = 0.5)
| Firm | Draft V | Elicited V (capped) | Δ | cap |
|---|---|---|---|---|
| Strong | 97.5 | 96.3 | −1.2 | slack (100) |
| Strong **except weak on a critical control** | 75.1 | **60.0** | **−15.1** | CAPPED 81.2→60.0 |
| Weak | ~13 | ~13 | ~0 | below cap |

### Exchange (κ = 0.5)
| Firm | Draft V | Elicited V (capped) | Δ | cap |
|---|---|---|---|---|
| Strong | 100.0 | 100.0 | 0.0 | slack (100) |
| Strong **except weak on a critical control** | 79.2 | **60.0** | **−19.2** | CAPPED 81.7→60.0 |
| Weak | ~8 | ~8 | ~0 | below cap |

The anomaly is resolved: a broken CASS/clearing control now ceilings the score (81→60), while strong
firms and already-weak firms are untouched. κ = 0.5 is the engineering starter; it is elicited and
ratified with the rest of the segment weights (ADR-0037) — nothing is activated until founder + panel
sign off, and both sets stay gated off until then.
