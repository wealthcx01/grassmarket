# ADR-0001 — Scale system and the single key registry

- **Status:** Accepted
- **Date:** 2026-07-03
- **Deciders:** Founder + engineering (Loop 0)
- **Normative source:** `docs/ATLAS-Methodology-v1.md` §3, §5, §6. Where this ADR and the
  Methodology disagree, the Methodology wins and this ADR is a defect.
- **Supersedes:** the prototype's four conflicting scales (1–5 vs 0.2/0.5/0.8/1.0 vs 0–10
  vs 0–100) — feasibility register defect **D8**, methodology gap **§5.8**.

## Context

The ATLAS prototype carried at least four numeric scales across its documents and code, and
resolved key names by silent fallback (`.get(key, default)`, caught `KeyError`, empty-dict
default). Feasibility defects **D1–D7** are all one bug wearing seven hats: a key that does
not match the registry is quietly replaced with a default, the engine keeps running, and it
prints a plausible, wrong number to a paying client. D1 (module-key mismatch → equal-weight
fallback, critical-module bottleneck always 0), D3 (α read from the wrong key → hardcoded
0.7, and the seed value 2.0 was not even in `[0,1]`), D4 (power-weight key mismatch → P = 0),
and D7 (subcomponent-loading keys matching nothing → all loadings default to 1.0) are the
canonical instances.

This ADR ratifies **one scale convention** and **one key registry** so that the entire class
of silent-fallback defects becomes a load-time crash instead of a wrong report.

## Decision

### 1. One scale system

- **Subcomponent maturity is an ordinal with a fixed numeric index** used only for
  computation, never shown to clients as a number (Methodology §3.1):

  | Level | Index |
  |---|---|
  | Basic | `0.2` |
  | Developing | `0.5` |
  | Advanced | `0.8` |
  | Frontier | `1.0` |

  These four values are the **only** legal subcomponent indices. Any other value is a
  contract violation, not a datum to be clamped or rounded.

- **Non-score states are first-class and never imputed** (Methodology §3.2):
  `Not Applicable` (removed from the denominator; sibling weights renormalise) and
  `Not Assessed` (never scored as zero, never averaged around; widens the uncertainty band
  and/or blocks a rating gate). The empty-module → `q_m = 0.0` behaviour of the prototype
  (defect **D9**) is prohibited: an unassessed subcomponent contributes to **no** score.

- **All continuous indices — `q_m`, `B`, `P`, `L`, `V` — live in the closed interval
  `[0, 1]` internally.** The display layer, and only the display layer, multiplies by 100 to
  present a `0–100` figure (e.g. "V = 61, range 55–68"). Score-points are dimensionless;
  they are never money (see ADR-0002).

- **Evidence strength is the ordinal `E1 < E2 < E3 < E4`** (Methodology §3.3). It drives
  uncertainty (§7), not the point score.

The scale vocabulary lives in exactly one place — `bcap_contracts.common` — as enums, and is
re-exported everywhere else. There is no second definition.

### 2. One key registry (ADR-0001 mechanism)

There is a **single registry** of the legal keys for every dimension the engine names:
modules, subcomponents, powers, and business metrics. It is the source of truth referenced by
`CLAUDE.md` non-negotiable #4 and Methodology §5.4.

- The registry is **data, loaded once at startup**, not scattered literals. Its canonical
  form is `packages/bcap_contracts/src/bcap_contracts/registry_data/*.yaml`; the loader is
  `bcap_contracts.registry`.
- **An unknown key is a refusal to score, not a default.** Every coefficient set, every
  rating, every metric is validated against the registry at load time. A key absent from the
  registry raises `UnknownKeyError`; a key present in the registry but missing from a
  coefficient set that must cover it raises `MissingKeyError`. Neither is ever swallowed.
- **No `.get(key, default)` on any path that reaches a score.** Lookups are `d[key]` (raising
  `KeyError`, re-raised as a typed registry error) or explicit membership checks that raise.
  This is enforced by review and by a lint rule; it is the single most important line in the
  repository's defence against D1–D7.
- The registry is **the same object** the contracts validate against and the (Loop 1) engine
  reads. There is no "engine copy" that can drift from the "contract copy" — drift *was* D1.

### 3. Coefficient invariants enforced at load

`CoefficientSet` is a contract type (`bcap_contracts.assessments.CoefficientSet`) with
validators that run when it is constructed, i.e. at load, i.e. before any client sees a number:

- **`Σθ = 1`** for the top-level value weights `(θ_B, θ_P, θ_L)`, within a tight tolerance
  (`1e-9`). Enforced (Methodology §5.4). Three conflicting θ sets summing to anything
  (methodology gap §5.1) cannot recur.
- **`α ∈ [0, 1]`** for every blend parameter (`α` per module, `α_L`). The prototype's seed
  value of `2.0` (defect **D3**) fails construction.
- **Every weight family is complete against the registry**: the modules named in `δ`, the
  subcomponents named in each module's `λ`, the powers named in `w_power`, the metrics named
  in `w_metric` must each be exactly the registry's set for that dimension — no missing key,
  no extra key.
- **Every coefficient carries a Weight Provenance Record** (Methodology §6): who set it, when,
  by what method, dispersion, review-due date. A coefficient without provenance is not
  loadable.

### 4. Display vs computation boundary

- Computation is always on `[0,1]` indices and ordinal ratings.
- Display multiplies indices by 100 and maps ordinals to labels.
- The two never mix in a stored value: a `ScoringRun` stores `[0,1]`; the `0–100` figure is
  derived at render time.

## Consequences

- **Positive:** D1–D7 are structurally impossible — a key mismatch cannot produce a plausible
  wrong number because it cannot produce a number at all. The scale ambiguity (D8) is closed.
  Contracts and engine share one registry, so they cannot drift.
- **Cost:** authoring discipline. Adding a module/subcomponent/power/metric means editing the
  registry data and every coefficient set that must cover it, or the load fails. This is the
  intended friction.
- **Scope note:** Loop 0 ships the *mechanism* (enums, registry loader, `CoefficientSet`
  validators, fail-loud errors) and the registry entries that are already fixed by the
  Methodology (the seven Powers, §8). The full 9 modules × 51 subcomponents and the business
  metric register are **content authored in Loop 1**; until they are populated the loader
  refuses to validate a coefficient set against an empty dimension (it does not pass it).

## Compliance tests (present from Loop 0)

- Unknown key → `UnknownKeyError` at load (never a default).
- `Σθ ≠ 1` → `CoefficientSet` construction fails.
- `α ∉ [0,1]` → `CoefficientSet` construction fails.
- A coefficient set missing a registered key for a populated dimension → `MissingKeyError`.
- No `.get(` on the scoring path (lint + review).
