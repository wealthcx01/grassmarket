# ADR-0025 — Operating-model assessment profiles (retail / wealth / exchange / infrastructure)

- **Status:** Accepted (2026-07-16). Founder-directed (D-5): extend ATLAS beyond retail brokerages to wealth managers, exchanges, etc.; (D-3) **exchange-first**, driven by the active book (ASX, NSE Data & Analytics).
- **Date:** 2026-07-16
- **Deciders:** Founder + engineering
- **Normative source:** `docs/METHODOLOGY-V2-SCOPE.md` §2 (promoted here from agenda to decision).
- **Implements:** GRS-0077 (profiles-mechanism), GRS-0078 (exchange-profile), GRS-0079 (wizard-profile-selector).
- **Couples with:** ADR-0023 (the C-index inherits this mechanism; the retail widget taxonomy is the retail profile's C instrument only).

## Context

The 9-module L taxonomy is brokerage-shaped (OEMS, EMS Gateway, Liquidity Connectivity). Today an exchange or a pure wealth platform is assessed by marking subcomponents `NOT_APPLICABLE` — legitimate but stretched: it silently narrows coverage instead of assessing what those firms actually run (matching engine, surveillance, member gateways, clearing/settlement, data distribution for an exchange). The active advisory book is exchange-side, so this is not hypothetical.

The registry is fail-loud and key-addressed (ADR-0001): the engine and every CoefficientSet address subcomponents by globally-unique key, and `validate_against` asserts a coefficient set covers *exactly* the registry's keys. That machinery is exactly what a profile needs — it just needs to validate against a *subset*.

## Decision

**Assessment profiles, not new frameworks.** A **profile = (module/subcomponent selection + additions) × (critical set) × (weight set)** per operating model. The registry remains the **superset**; a profile is a validated **view/filter** over it. The four profiles: **retail brokerage** (the unchanged v1 default), **wealth/advisory platform**, **exchange / market infrastructure**, **infrastructure vendor**.

1. **Registry gains a profile dimension.** A new `profiles.yaml` + `ProfileDef` entry type declares each profile's selected module keys, any per-profile subcomponent additions, and a per-profile `critical` override set (criticality currently lives globally on `SubcomponentDef`; a profile overrides it — an exchange need not treat `OEMS_*` as critical, or at all).

2. **One CoefficientSet per profile.** Each profile carries its own elicited weights + critical-for-L set with provenance; `validate_against` pointed at the profile-scoped key set gives per-profile completeness for free. The live-score service selects the coefficient set (and registry view) **by profile** rather than only draft-vs-elicited.

3. **The engine iterates a profile-filtered registry.** `_assert_inputs_cover_registry`, the `_score_modules` loop, and the triad-source validation operate over the profile's selected keys; nothing in the L aggregation math changes.

4. **Additive and retail-invariant.** Retail brokerage stays the default and its scoring is **byte-identical** — the golden master must still reproduce. Profiles are opt-in via the wizard's segment selector.

5. **Benchmark populations segment by profile.** An exchange's L is never compared to a broker's; benchmark rows carry their profile.

6. **Sequencing:** the profile *mechanism* first (registry/engine/coefficient scaffolding), then the **exchange profile** as the first content instance (ahead of wealth, per the book). The C-index (ADR-0023) is built profile-aware from day one.

## Consequences

- New `profiles.yaml`/`ProfileDef`, per-profile critical overrides, per-profile CoefficientSets, profile-filtered engine iteration, and a real wizard profile selector (promoting `BusinessProfile.segment` from a free-text datalist).
- Interacts with an **unratified base** (`critical` flags + `subcomponent_status` are `draft-pending-ratification`) — profile criticals should be authored alongside registry ratification, not before it silently.
- The exchange profile's module content (matching engine, surveillance, member gateway, clearing/settlement, data distribution) is authored from the ASX/NSE engagement packs (reference only, never committed).

## Alternatives considered

- **Keep the single retail taxonomy and use `NOT_APPLICABLE` for everything else.** Rejected — it under-assesses non-brokerages (no exchange-specific modules) and pollutes benchmark comparability.
- **A separate framework per operating model.** Rejected — duplicates the engine, the rubric machinery, and the governance; profiles reuse all of it and keep one methodology.
- **Weights in the registry.** Rejected — weights belong in the CoefficientSet (ADR-0006); the registry only declares which keys exist per profile.
