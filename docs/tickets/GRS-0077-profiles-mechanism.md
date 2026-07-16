# GRS-0077 — Operating-model profiles: the mechanism

**Status:** Planned
**Loop:** Loop 7 — Operating-model profiles
**Depends on:** ADR-0025 (operating-model profiles)

## Why

The 9-module L taxonomy is brokerage-shaped (OEMS, EMS Gateway, Liquidity Connectivity). Today an
exchange or wealth platform is assessed by marking subcomponents N/A — legitimate but stretched: it
silently narrows coverage instead of assessing what that operating model actually runs
(`docs/METHODOLOGY-V2-SCOPE.md` §2). The v2 answer is **assessment profiles, not new frameworks**: a
profile = (module/subcomponent selection + additions) × (critical set) × (weight set) per operating
model. This ticket builds the mechanism only; the registry stays the **superset** and a profile is a
view/filter over it. It is strictly ADDITIVE — retail brokerage is the v1 default and must not move.

## What to build

**Registry (`packages/bcap_contracts/src/bcap_contracts/registry.py` + `registry_data/`)**
- New `registry_data/profiles.yaml` (with `status:`, loaded via `_require` — ADR-0001) and a new
  `ProfileDef` entry type: selected module keys, per-profile subcomponent additions, and per-profile
  `critical` overrides. Criticality currently lives globally on `SubcomponentDef` (`registry.py:93`);
  a profile must be able to override it (an exchange may not treat `OEMS_*` as critical).
- A profile-scoped **view** helper on `Registry` that returns the filtered key sets. REUSE, do not
  rebuild: `assert_covers_keys` (`registry.py:275`), `_assert_unique_keys` (`:382`), strict
  accessors `require_*` (`:247`), and `load_registry`/`_build_registry` (`:314`) machinery.

**Coefficients (`packages/bcap_contracts/src/bcap_contracts/assessments.py`)**
- One `CoefficientSet` per profile (retail / exchange / wealth). REUSE `validate_against(registry)`
  (`assessments.py:172`) pointed at the profile-scoped key set — it gives per-profile completeness
  for free.

**Live-score service (`src/grassmarket/assessments/service.py:220`)**
- `live_score(...)` already takes `coefficients` + `registry` as args. Select the CoefficientSet
  **and** registry view by profile, not just draft-vs-elicited.

**Engine (`src/grassmarket/atlas/engine.py`)**
- Profile-filtered registry iteration: `_assert_inputs_cover_registry` (`engine.py:431`), the
  `_score_modules` module loop (`:114`), and per-profile triad-source validation
  (`_assert_triad_sources_registered` `:453`; the hardcoded `_PERCEIVED_POWERS` / `_ECONOMIC_GROUPS`
  `:46`) must all run against the profile view rather than the full superset.

## Acceptance / verification

- A profile-scoped registry view validates against its own CoefficientSet (unknown/missing key still
  refuses — ADR-0001 discipline preserved per profile).
- **The retail profile reproduces the golden master byte-identical** — `V = 0.478565`
  (`tests/test_atlas_engine_golden_master.py`). This is the load-bearing no-regression gate.
- `tests/test_registry.py` stays green; new `profiles.yaml` fails loud on a bad/missing key.
- Property tests still hold within a profile view (monotonicity, bottleneck, N/A renormalisation).

## Not in scope

- Exchange module content and its CoefficientSet — GRS-0078.
- Wizard profile selector — GRS-0079.
- Wealth/advisory and infrastructure-vendor profile content (later tickets).

> Note: `critical` flags + `subcomponent_status` are `draft-pending-ratification`
> (`modules.yaml:10-15`). Profile criticals therefore layer over an **unratified base set** — flag
> this in the ADR; a base-set ratification may shift what a profile need only override.
