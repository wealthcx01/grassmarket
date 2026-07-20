# GRS-0151 — Critical-control cap on V (ADR-0038)

**Status:** Done (2026-07-20). Founder-directed after the GRS-0150 scored effect.
**Loop:** Part 2 — segment fit / scoring integrity. **ADR:** ADR-0038.

## Why

The GRS-0150 research trimmed θ_L on the segment sets (infra is hygiene, priced into B — correct for a
*value* lens). The scored effect exposed the cost: a firm strong everywhere **except a critical
control** scored *higher* under the trimmed θ_L (wealth 75→81, exchange 79→82). ATLAS judges whether a
platform is **sound**, not what it's worth — a broken CASS/clearing control must show and must not be
out-weighted.

## What shipped

- **`CoefficientSet.critical_control_cap_floor` (κ, optional).** When set, the engine applies
  `V = min(V_weighted, κ + (1−κ)·min(q_m over critical-for-L modules))` after the weighted V.
  - Absent ⇒ **no cap, V byte-identical** — retail golden master + every three-index set untouched.
  - Excludes fully-unassessed criticals (D9, like ADR-0034); only ever LOWERS V; monotone.
  - Carries provenance (`critical_control_cap` family); a floor with no critical modules refuses to
    construct.
- **`CriticalControlCapResult`** on `AtlasResult` (floor, l_min_critical, cap, v_uncapped, bound,
  binding_module) — recorded even when it does not bind, so the guardrail is legible, not silent.
- **κ = 0.5 on both segment starter sets** (`elicited_{wealth,exchange}_coefficient_set`) — a broken
  critical control caps V at ≈60. Sets remain **gated off** (ADR-0022) until founder + panel ratify.
- Schemas regenerated; ADR-0038 + Methodology-v1.5 note (optional §5.1 cap term).

## Scored effect (κ = 0.5)
| Firm | Wealth | Exchange |
|---|---|---|
| Strong | 96.3 (slack) | 100.0 (slack) |
| Weak on a critical control | 81.2 → **60.0** (capped) | 81.7 → **60.0** (capped) |
| Weak everywhere | ~13 (below cap) | ~8 (below cap) |

## Tests
`tests/test_critical_control_cap.py` — no-cap ⇒ None + V untouched; cap binds/ceilings on a broken
wealth & exchange critical; cap present-but-slack when criticals strong; V = min(uncapped, cap) always;
monotone through the cap; construction refuses cap-without-criticals and cap-without-provenance.
Golden master + full suite green.
