# GRS-0082 — C engine + coefficients (Stage 1: report-alongside)

**Status:** Planned
**Loop:** Loop 7 — C-index (Customer Proposition)
**Depends on:** ADR-0023 (Accepted), ATLAS-Methodology-v1.3

## Why

ADR-0023 stages C entry: v1.3 computes C and **reports it alongside V**; V itself is unchanged
until v1.4 (GRS-0086). This is the whole point of the staged design — C rides the existing L
aggregation path verbatim, so v1.3 adds a fully-tested index without perturbing the settled
composite. This ticket builds `_score_c` and its coefficients and surfaces C as a reported result.

**HARD CONSTRAINT:** Stage 1 (v1.3) must NOT touch the composite line
`src/grassmarket/atlas/engine.py:76-80`. `tests/test_atlas_engine_golden_master.py` pins
V=0.478565 to the last decimal. C is REPORTED ALONGSIDE V here; it is summed into V only at v1.4.
The golden master must stay **byte-identical** after this ticket.

## What to build

Files:
- `src/grassmarket/atlas/engine.py` — add `_score_c`, a clone of `_score_l` (`engine.py:233`) with
  its own `alpha_c` / `delta_c` / `critical_modules_for_c` coefficients. Call it and attach its
  result to `AtlasResult`, but do **not** add its value into the `v_value` sum at `:76-80`.
  `_score_modules` (`:106`) and `_rating_gate` (`:190`) are reused unchanged; NOT_APPLICABLE /
  NOT_ASSESSED renormalisation stays as-is.
- `packages/bcap_contracts/src/bcap_contracts/results.py` — `CompositeResult.c_index` reported
  (populated) but **not summed** (`results.py:112`); add a `CustomerResult` contract mirroring
  `LResult` (weighted term / min term / value).
- `frontend/lib/types.ts` — add `PRESENT_PAYWALLED` and `PRESENT_DEFECTIVE` to `NonScoreState`
  (`types.ts:8`) and mirror them in the backend common enum.
- `src/grassmarket/atlas/assessments.py` — add C-internal + rarity-weight provenance families to
  `_PROVENANCE_FAMILIES` (`assessments.py:39-49`) so a populated C set with no provenance fails
  loud; add C bands to `LiveScore` (`assessments.py:491`).
- CoefficientSet — `alpha_c`, `delta_c`, `critical_modules_for_c`. Per ADR-0023 (I-4), launch
  default = the existing elicited coefficients reused; a real θ_C panel is post-launch.

Reuse: `_score_l` structure, `_score_modules`, `_rating_gate`, the renormalisation rules, the
provenance/fail-loud machinery — all verbatim.

New: `PRESENT_PAYWALLED` / `PRESENT_DEFECTIVE` states, rarity-weight provenance family, `c_index`
reported field, `CustomerResult`.

## Acceptance / verification

- `tests/test_atlas_engine_golden_master.py` passes with V=0.478565 unchanged — assert byte-identical.
- `_score_c` reproduces `_score_l` behaviour on an equivalent input (property parity test): C
  monotonic in subcomponents, bottleneck behaviour, N/A renormalisation, Not-Assessed excluded.
- A populated C set with no matching provenance family raises (fail-loud test).
- An unknown coefficient key in the C set is a load-time error (registry test).
- `CompositeResult` carries `c_index` but the V sum at `:76-80` is textually unchanged (diff check).

## Not in scope

- Any V composition change / four-index V — GRS-0086 (Stage 2, gated).
- Wizard capture and grid — GRS-0083.
- Benchmark ingestion — GRS-0084; deliverable sections — GRS-0085.
