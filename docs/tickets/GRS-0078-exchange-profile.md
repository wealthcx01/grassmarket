# GRS-0078 — Exchange operating-model profile (content)

**Status:** Planned
**Loop:** Loop 7 — Operating-model profiles
**Depends on:** ADR-0025 (operating-model profiles), GRS-0077 (profiles mechanism)

## Why

Exchange-first is the founder decision (D-3): the active book (ASX, NSE) drives which profile ships
second. An exchange runs infrastructure the retail L taxonomy never names — matching engine, market
surveillance, member/gateway connectivity, clearing & settlement interfaces, market-data
distribution. Assessing it by N/A-stretching the brokerage taxonomy silently narrows coverage rather
than measuring what the exchange actually operates (`docs/METHODOLOGY-V2-SCOPE.md` §2). This ticket
provides the **content** that fills the GRS-0077 mechanism for the exchange operating model.

## What to build

**Profile content (`packages/bcap_contracts/src/bcap_contracts/registry_data/`)**
- An `exchange` entry in `profiles.yaml` (the `ProfileDef` type from GRS-0077): selected module keys
  from the superset, plus exchange-specific subcomponent additions for market infrastructure —
  matching engine, market surveillance, member/gateway connectivity, clearing & settlement
  interfaces, market-data distribution. New subcomponent keys stay globally unique and fully
  qualified `<MODULE_KEY>_<LEAF>` (`_assert_unique_keys`, `registry.py:382`).
- An exchange-specific **critical set** via the profile's `critical` overrides (an exchange may not
  treat `OEMS_*` as critical, but WILL treat matching-engine / surveillance subcomponents as
  critical). Additions land in the registry superset; the profile selects/overrides — retail is
  untouched.

**Coefficients (`packages/bcap_contracts/src/bcap_contracts/assessments.py`)**
- A **draft** exchange `CoefficientSet` (`client_usable=False` until elicited) that
  `validate_against` (`assessments.py:172`) the exchange profile's key set — exactly covers it, no
  unknown / missing key.

**Harvest (reference only — NOT committed)**
- Populate structure + criticals from the ASX/NSE engagement packs:
  `…/BruntsfieldCapital/Business/Advisory/Engagements/Active/{ASX,NSI}`. Read-only source, same rule
  as the prototype-harvest folders — labels/structure inform the YAML; the packs never enter the repo.

## Acceptance / verification

- An exchange assessment scores over the **exchange module set** with the GRS-0077 profile view —
  WITHOUT N/A-stretching the retail taxonomy (no retail-only subcomponent appears in the run).
- The exchange CoefficientSet exactly covers the exchange profile key set (fail-loud on any drift).
- Benchmark populations **segment by profile**: an exchange's L is never pooled with or compared to a
  broker's (a comparison across profiles is refused, not silently averaged).
- Retail golden master unaffected (`V = 0.478565`); `tests/test_registry.py` green with the additions.

## Not in scope

- Wealth/advisory and infrastructure-vendor profiles.
- Eliciting the real exchange weights/criticals (θ panel) — this ships a DRAFT set only.
- Wizard changes — GRS-0079.

> Note: exchange criticals layer over a base set still marked `draft-pending-ratification`
> (`modules.yaml:10-15`); record provenance so a later base ratification can reconcile cleanly.
