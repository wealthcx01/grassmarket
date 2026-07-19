# ADR-0035 — Segment fit: per-profile metric selection, the wealth operating model, and metric input-domain validation

- **Status:** Accepted (2026-07-19). Founder-directed stress-test remediation (raise advisor trust from a mean 57/100 toward ≥95). Extends ADR-0025.
- **Date:** 2026-07-19
- **Deciders:** Founder + engineering
- **Normative source:** `docs/tickets/GRS-0147` (segment fit) + `GRS-0144` (input validation); domain taxonomies in the stress-test synthesis (`reports/mock-advisor-stress-test-2026-07-19.md`).
- **Implements:** GRS-0144, GRS-0147. **Extends:** ADR-0025 (operating-model profiles). **Couples with:** ADR-0006 (weights live in the CoefficientSet), ADR-0001 (fail-loud registry).

## Context

Segment fit was the loudest, most cross-cutting stress-test finding — **all 5 personas**, capping the
confidence of 4 of them:

- **No wealth operating model.** The wizard offers only *Retail brokerage* and *Exchange*. Both wealth
  personas (SJP, Brewin Dolphin) had to mislabel their firm as "Retail brokerage" while the Academy
  treats "wealth manager" as first-class — an internal contradiction a wealth board notices.
- **Retail-framed, GBP-locked metrics.** B is scored on AUA/ARPU/Gross-Margin in GBP for *every*
  profile. This fits neither an exchange (ADV, cleared notional, index/data revenue) nor a US
  neobroker (funded accounts, MAU, PFOF, USD).
- **Non-retail self-flags "not client-usable."** Exchange shows "weights & criticals pending
  elicitation — indicative, not client-usable," so there is no defensible deliverable for those
  personas' customers today.
- **No input-domain validation (GRS-0144).** A negative −£999,999 AUA saved cleanly and *scored* —
  `_interpolate` silently clamps an out-of-range raw to the nearest anchor. A visible non-negotiable
  #3 (fail-loud) violation.

**The architectural fact that shapes this decision:** ADR-0025's profile mechanism only reshapes the
**L / infrastructure-module** dimension. `Registry.for_profile()` passes `metrics` and `powers`
through verbatim, and `CoefficientSet.validate_against` asserts `w_metric` covers *exactly*
`registry.metric_keys()`. So adding a wealth profile the way exchange was added gives wealth-native
*modules* but still scores B on retail metrics — and **adding wealth/exchange metric rows to the
shared `metrics.yaml` would change the retail metric set and break the golden master.** Per-profile
metrics are a missing capability, not a data edit.

## Decision

Fix segment fit in four ordered phases; ship the trust wins that don't need an elicitation panel
first, and gate client-usability on the panel.

1. **Phase 1 — Metric input-domain validation (GRS-0144). Ships now; no methodology change.**
   Add optional bounds to `MetricDef` (a `sign: non_negative | signed` flag and/or `min_raw`/`max_raw`)
   and **refuse to score** a raw outside the metric's declared domain (and any non-finite raw), rather
   than clamp — enforced fail-loud where the registry is in scope, surfaced as a scoreability blocker,
   never a 500. Bounds come from the per-segment sign table (most magnitudes are strictly non-negative;
   net flows, growth rates, and margins are legitimately signed). Purely additive: valid inputs score
   identically, so the golden master is untouched.

2. **Phase 2 — Per-profile metric selection. Ships now (mechanism); retail-invariant.**
   Mirror the module mechanism for metrics: `metrics.yaml` becomes a profile-tagged superset, add a
   `metric_keys` selection to `ProfileDef`, filter metrics in `for_profile` exactly as modules are
   filtered, and give each profile its own `w_metric`/`group_weights`. Retail's selection = today's
   exact 10 → the retail view is byte-identical → golden master preserved (guarded by a test mirroring
   the existing profile-invariance test). This is the capability that makes segment-native B possible.

3. **Phase 3 — Wealth operating model (L). Structure ships now; client-usable gated.**
   Add a `wealth` block to `profiles.yaml` (wealth infra modules: suitability/advice process,
   discretionary-vs-advisory mandate mix, custody/CASS, platform/AUM economics, financial planning,
   investment governance/PROD), a `draft_wealth_coefficient_set`, a `profile_scoring_context` branch,
   and the wizard selector option — removing the mislabel-as-retail contradiction. Attach the wealth
   metric set (Phase 2) and UK regulatory framing (Consumer Duty, MiFID/COBS 9A suitability, SM&CR,
   PROD) as first-class context. Ships **draft / not-client-usable** until Phase 4.

4. **Phase 4 — Ratify + elicit. Founder/panel-gated (NOT autonomous), per non-negotiable #2.**
   Ratify the metric numbers (units, anchors, group membership) per segment; run per-profile weight/
   critical elicitation (swing-weighting/Delphi, §6); author `elicited_<profile>_coefficient_set`s with
   provenance and flip the `active.py` seam in one recorded commit. Only this flips a profile
   client-usable and stops the "not client-usable" banner. Also decides the wealth revenue-margin
   fair-value ceiling and the currency/FX-normalisation policy.

## Consequences

- New optional `MetricDef` bounds + fail-loud domain check; `metrics.yaml` gains per-metric sign/bounds
  and profile tags; `ProfileDef` gains `metric_keys`; `for_profile` filters metrics; per-profile
  CoefficientSets carry their own metric weights; a `wealth` profile + draft coefficient set + wizard
  option; a golden-master-invariance test for the retail metric view.
- The domain metric taxonomies (wealth/exchange/retail, with anchors and sign constraints) are authored
  content pending founder ratification — they drop into Phases 2–3 once ratified.
- Multi-currency: money-metrics declare a `currency`; raws FX-normalise to it at ingest rather than
  assuming GBP.

## Alternatives considered

- **Just add a wealth profile like exchange (no per-profile metrics).** Rejected — gives wealth modules
  but leaves B on retail AUA/ARPU, so the loudest complaint stays. It also can't add wealth metrics
  without breaking the retail golden master.
- **Add all segment metrics to the shared superset and weight the irrelevant ones to zero.** Rejected —
  zero-weighted metrics still demand inputs, pollute coverage, and change `registry.metric_keys()`
  (breaking the golden master); it also mixes segments' vocabularies on one screen.
- **Ship non-retail profiles client-usable with authored default weights (skip the panel).** Rejected —
  violates non-negotiable #2 (settled methodology; weights are elicited, provenanced, recorded). Draft
  profiles are honestly labelled indicative until the panel runs.
