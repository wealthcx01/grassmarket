# ATLAS Methodology v1.5

**Bruntsfield Capital — CONFIDENTIAL — July 2026**

The Bruntsfield Platform Power assessment method. This document is **normative** for the Grassmarket
scoring engine and **supersedes v1.4** for the uncertainty machinery only. It is a focused successor:
it amends **§7 only** — how the uncertainty engine treats **Not Assessed** inputs — and restates the
amended rule in full below. **All other sections are unchanged** and are incorporated by reference:
§5.1 four-index composition (v1.4), §3.3 evidence scales and the modelled-vs-unmodelled labelling
(v1.2), and §1–§6/§8–§12 (v1.1). **No coefficient value changes; the deterministic scores (§5) are
byte-identical to v1.1 (golden master V = 0.478565).**

---

## 1.1 Changelog: v1.4 → v1.5

v1.5 closes a defect in §7: the Monte-Carlo uncertainty layer **imputed a value for Not Assessed
subcomponents** (a uniform draw over all four maturity levels, included in every draw). This
contradicted the **D9** rule (ADR-0001) that an unassessed subcomponent contributes to *no* score,
and it manufactured a falsely-precise ~neutral band — and a phantom "likely constraint" — for modules
that had never been assessed. v1.5 makes the uncertainty layer honour D9 exactly as the deterministic
engine already does.

| Amendment | Section | ADR |
|---|---|---|
| **Not Assessed is excluded from Monte-Carlo draws, never imputed.** A Not Assessed subcomponent contributes to no draw; a fully-unassessed module has `q_m = None` in every draw and therefore **no band** in `module_qm` — it can never be named a bottleneck. | §7 | ADR-0034 |
| **Ignorance about the unmeasured is carried by coverage, not a fabricated band.** The coverage-driven Assessment Uncertainty Rating (zero coverage → VERY_HIGH) and the deterministic tornado (a Not Assessed input spans the full scale and tops the leverage ranking) express what is unknown — the band expresses only the uncertainty of what was *measured*. | §7 | ADR-0034 |
| **Optional critical-control cap on V.** A CoefficientSet MAY carry a floor κ; when present, `V = min(V_weighted, κ + (1−κ)·min(q_m over critical-for-L modules))`, so a broken critical control cannot be out-weighted by a low θ_L. Excludes fully-unassessed criticals (D9), only ever lowers V, is monotone, and is recorded on the result. **κ absent ⇒ V is byte-identical to §5.1** — the golden master and every un-capped set are unchanged; the cap is used only by the (gated-off) segment starter sets. | §5.1 | ADR-0038 |

### Version-stamping convention (v1.5)

§5 is unchanged, so the **deterministic engine, every CoefficientSet, and the ratified golden masters
retain their `1.1`/`1.4` methodology stamps** — the ratified numbers are untouched. Only the
**uncertainty model** carries the `1.5` stamp, because §7 is what this version amends. This mirrors
the v1.2 convention exactly.

## 7. Uncertainty (amended — the Not Assessed rule)

Monte Carlo **wraps** the deterministic kernel: each draw perturbs the *inputs* by their evidence
grade and re-runs `score()`, so the point estimate and every band come from one code path (v1.2 §7,
unchanged). v1.5 fixes how a **Not Assessed** input enters that process:

1. **A Not Assessed subcomponent is not sampled.** It passes through each draw unchanged (state = Not
   Assessed, level = None) and the kernel excludes it, exactly as it excludes a Not Applicable input.
   It therefore contributes to **no** module `q_m`, no L, and no V draw. (Previously it was imputed a
   uniform level and *included* — the defect.)

2. **A fully-unassessed module has no band.** Because none of its subcomponents are sampled, its
   `q_m` is `None` in every draw, so it does **not** appear in `module_qm`. Consequences: it cannot be
   ranked as the platform bottleneck, and no falsely-precise ~neutral band is shown for a module
   nobody assessed. This aligns the uncertainty layer with the deterministic engine, which already
   returns `q_m = None` for an empty module (D9, ADR-0001).

3. **A partially-assessed module bands over what was assessed.** Its `q_m` band reflects the evidence
   grades of its assessed subcomponents only — an honest range for the measured part.

4. **Ignorance is carried by coverage, not by the band.** What is *unknown* is expressed by (a) the
   Assessment Uncertainty Rating — confidence = coverage × mean-evidence factor, so low coverage reads
   VERY_HIGH — and (b) the deterministic tornado, where a Not Assessed input spans the full Basic↔
   Frontier scale and surfaces as the highest-leverage next assessment. The band never fabricates
   width to stand in for missing coverage.

5. **Honest labelling (v1.2, carried forward).** An input with no confidence grade is not modelled;
   its index band is a labelled point estimate (`modelled = False`), never a tight band. v1.5 does not
   change this — it only removes the imputation that made a *fabricated* band possible for the
   unassessed.

This supersedes the v1.2 §3-Consequences sentence "subcomponents always carry evidence grades, so V,
L and per-module q_m are always modelled": that was only true because the code force-imputed the
unassessed. Under v1.5, only modules with at least one assessed subcomponent carry a modelled band.
