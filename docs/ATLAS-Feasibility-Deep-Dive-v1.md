# ATLAS — Deep Dive & Feasibility Assessment (v1)

**Bruntsfield Capital — CONFIDENTIAL — July 2026**

Source-level audit of the ATLAS prototype: what has been built, what it actually computes, and whether it can carry a paid advisory product. Retained in the repo primarily for the **defect register (§4)** — the scaffold and engine must make these defects structurally impossible.

---

## 1. Executive Summary

- **The architecture is genuinely good and the conceptual model is sellable.** The 5-level hierarchy (subcomponents → modules → L, alongside B and P → V), the bottleneck logic, config-driven versioned coefficient sets, manual override with mandatory reason, and the input-method-agnostic data model are design decisions a technical buyer would respect.
- **The implementation is a strong skeleton wired up wrongly in places, and the wiring failures are silent.** Key-name mismatches between the seed coefficients and the module enum mean that, as seeded, the critical-module bottleneck always reads 0, every module's value sensitivity κ computes to 0, and every scenario returns LV = −cost. The engine runs, renders plausible numbers, and is wrong.
- **Feasible as a diagnostic instrument now; not yet as a valuation instrument.** The currency-denominated Latent Value / ROI layer had a dimensional inconsistency at its core, a calibration cold-start problem, and the "Platform Power" triad existed in narrative but not in the data model. All three are resolved by ATLAS Methodology v1.

## 2. Inventory

| Artefact | What it is | Status |
|---|---|---|
| `bruntsfield_advisory_assessment_wizard_v2` | Git repo: FastAPI + SQLAlchemy + PostgreSQL backend, Next.js/MUI frontend, analytics pipeline | Canonical but behind; key files empty |
| `codespaces-blank` | Working copy AHEAD of v2: normalization implemented, coefficient seed script, 4 self-audit reports, has been run | Most complete iteration; not committed |
| `dpn / jcj / oqh / ryv / frontend` | Fragment folders from parallel generation attempts | Superseded; discard |
| `atlas_wizard_user_experience.md` | UX narrative draft (7-step wizard, live score panel, scenario UX) | Draft |
| `atlas_wizard_wireframes.md` | Structural wireframe spec — layouts, states, URLs, interaction rules | Implementable; pre-Figma |
| Grassmarket PRD §2.3 | Path A wizard + Path B meeting intelligence, one data model | Sound framing; scale conflict (1–5 vs 0.2–1.0) |
| `analytics/train_model.py` | Real OLS calibration pipeline (statsmodels): y ~ B + P + L | Runs only with finalised outcome data — i.e., not yet |

Process finding: the best code (codespaces-blank) was not in git; the git repo had empty files where the working copy had implementations; both lived on OneDrive.

## 3. The Model As Implemented (prototype)

- **L1→2:** `q_m = α_module · Σ(λ·s)/Σλ + (1−α_module) · min(s)`; s ∈ {0.2, 0.5, 0.8, 1.0}; missing loadings silently default to 1.0; empty module → q_m = 0.0 ("not assessed" = "catastrophic").
- **L2→3:** `L = α_L · Σ(δ_m·q_m)/Σδ + (1−α_L) · min(q_critical)`; α fallback 0.7.
- **L4:** `B = Σ w_k·normalize(metric_k)/Σw` — normalize() empty in v2, units-sensitive placeholder in working copy. `P = Σ w_j·power_j/Σw` over POWER_* metrics.
- **L5:** `V = θ_B·B + θ_P·P + θ_L·L` — three conflicting θ sets across three files; Σθ=1 unenforced.
- **L6:** `κ_m = θ_B·β_B·φ_m + θ_P·β_P·ψ_m + θ_L·β_L·δ_m`; `LV = κ·Δq/(1+r) − cost`; `ROI = LV/cost`; module LVs summed.

## 4. Defect Register

| # | Finding | Consequence |
|---|---|---|
| D1 | Seed coefficient module keys (FRONT_END, BACK_OFFICE, LIQUIDITY_CONNECTIVITY) ≠ ModuleKey enum (FRONTEND, BACKOFFICE, LIQ_CONNECT); scoring.py catches KeyError and passes | L weights silently ignored → equal-weight fallback. Critical-module bottleneck = 0.0 → L depressed by the full (1−α_L) share for every client |
| D2 | Same key mismatch in module_effects lookup in lv_roi.py (effects default {}) | φ=ψ=δ=0 → κ_m = 0 → LV = −cost and ROI < 0 for every scenario |
| D3 | Seed stores α under key "value"; scoring reads key "default" | Seeded α ignored; hardcoded 0.7 used (seed value 2.0 also invalid — α must be in [0,1]) |
| D4 | Seed power_weights keys (SCALE, …) vs expected metric keys (POWER_SCALE, …) | No weight matches any score → P = 0 for every assessment |
| D5 | normalization.py empty in canonical repo; units-sensitive placeholder in working copy | v2 cannot compute B (ImportError); working copy computes a units-dependent B |
| D6 | metric_weights.yaml empty in both copies | Intended config source for B/P weights doesn't exist |
| D7 | Seed subcomponent-loading keys match neither the YAML keys nor each other | All loadings default to 1.0, silently |
| D8 | Zero backend tests; 3 trivial frontend tests; no Alembic; all Pydantic schema files empty in v2 | Nothing would have caught D1–D7; pipeline never executed against a known-answer fixture |
| D9 | Empty module → q_m = 0.0 | Partially assessed platforms get artificially catastrophic L and phantom bottleneck flags |

**The pattern matters more than the instances.** Every defect is a silent fallback: `.get(key, default)`, caught KeyError, empty-dict default. Under SD3 standards (fail loud; contract-typed coefficients validated against the module registry at load; golden-master tests) D1–D7 become load-time crashes instead of wrong client reports.

## 5. Methodology Gaps Found (all resolved in Methodology v1)

1. V formula opacity — three conflicting θ sets, no written derivation → **§5–6 (registry, enforced Σθ, provenance records)**.
2. Latent Value dimensional inconsistency (score-points minus currency) → **§10 three-layer value bridge + Upgrade Priority Index**.
3. Single-period /(1+r) masquerading as NPV → **§10 lever-level risk-adjusted NPV with assumption register**.
4. Summing module LVs contradicts bottleneck aggregation → **scenario evaluation by full re-scoring**.
5. Calibration cold start (n=0 for OLS) → **§6 expert elicitation + §11 pre-registered staged validation (Stage 1 expert / Stage 2 benchmarked ≥10 / Stage 3 econometric ≥30)**.
6. Confidence captured but unused → **§7 evidence-grade-driven distributions, Monte Carlo ranges, Uncertainty Rating**.
7. Platform Power triad absent from data model → **§2 + §8 triad operationalisation with committee governance**.
8. Scale conflicts across docs (1–5 vs 0.2/0.5/0.8/1.0 vs 0–10 vs 0–100) → **ADR-0001 ratifies one convention**.
9. No rubrics / inter-rater mechanism → **§4 anchor library (204 anchors) + §9 calibration protocol (κ_w ≥ 0.75)**.
10. "Not assessed" conflated with zero → **§3.2 first-class N/A and Not Assessed states**.

## 6. Feasibility Verdict

| Question | Verdict |
|---|---|
| Structured diagnostic (maturity scorecard + bottleneck + prioritised roadmap)? | **Yes — near-term** |
| Currency-denominated valuation engine? | **Not yet** — fixable by design (value bridge), not debugging |
| Core IP of the Advisory pillar? | **Yes — with honesty staging** (Stage 1 expert-calibrated → Stage 2 benchmarked → Stage 3 econometric) |
| Existing code a viable harvest base? | **Partially** — harvest data model, coefficient governance, pipeline shape, wizard UX spec, auth; rewrite normalization, value layer, wiring, tests, schemas |
