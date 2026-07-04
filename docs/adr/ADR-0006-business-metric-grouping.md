# ADR-0006 — Group-weighted Business index (B)

- **Status:** Proposed (group weights to be ratified by the elicitation panel)
- **Date:** 2026-07-04
- **Deciders:** Founder + engineering + elicitation panel (Loop 1)
- **Normative source:** `docs/ATLAS-Methodology-v1.md` §5.3.
- **Raised by:** review item B1.

## Context

`B = Σ_k w_k·n_k / Σ_k w_k` (§5.3). With uniform `w_k` over the 10 draft metrics, the four scale
metrics (AUA, Active Clients, Net Revenue, Revenue-per-Client — strongly collinear, since
ARPU ≈ revenue ÷ clients) let sheer size count ~4× of 10. B then over-weights scale and
under-weights unit economics and momentum.

## Decision

B is a **group-weighted mean**. Every metric declares a **group** (registry structure): `scale`
| `unit_economics` | `momentum`. B is computed as:

```
B = Σ_g W_g · ( Σ_{k∈g} w_k·n_k / Σ_{k∈g} w_k ) / Σ_g W_g
```

— the within-group mean of each group, combined with **group weights `W_g`**. Group weights are
draft-uniform (1/3 each) pending elicitation and live with the coefficients, not the registry.
Collinear scale metrics now count once (as the scale group). Metrics in a NOT_APPLICABLE /
NOT_ASSESSED state (ADR-0007 / review B4) drop out and their group renormalises.

Draft groups: **scale** = AUA, ACTIVE_CLIENTS, NET_REVENUE · **unit_economics** =
REVENUE_PER_CLIENT, GROSS_MARGIN, COST_TO_SERVE, TAKE_RATE_LEVEL · **momentum** =
NET_REVENUE_RETENTION, CLIENT_GROWTH_RATE, CAC_PAYBACK_MONTHS.

## Consequences

- Structural de-collinearisation; the panel sets both within-group `w_k` and across-group `W_g`
  by swing weighting (§6). For Meridian the number barely moves (0.679 → 0.679) because the values
  are similar — the point is correct weighting, not a different headline today.
- The grouping is draft content; the metric set and group assignment are John's to ratify
  (review B3 also renames TAKE_RATE_DURABILITY → TAKE_RATE_LEVEL and flags a possible durability
  redefinition).
