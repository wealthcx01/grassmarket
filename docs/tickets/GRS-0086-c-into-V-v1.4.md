# GRS-0086 — Fold C into V (Stage 2, v1.4)

**Status:** Shipped
**Loop:** Loop 7 — C-index (Customer Proposition)
**Depends on:** GRS-0080–0085, ADR-0023, ADR-0031, ATLAS-Methodology-v1.4
**Branch:** `grs-0086-fold-c-into-v`

## What shipped

The four-index composite `V = θ_B·B + θ_P·P + θ_L·L + θ_C·C` (Methodology v1.4), as an **optional
v1.4 path** driven by a new `theta_c` — so the v1.1/v1.3 three-index golden master (V=0.478565) is
byte-identical.

- **`CoefficientSet.theta_c`** (`assessments.py`) — `Score | None`. Σθ validator sums the three
  terms when θ_C is absent and all **four** when present. A new validator enforces **θ_C ⇒
  `scores_c`** (you cannot weight a C you do not compute). θ_C is never defaulted to 0.
- **`engine.py`** — `score()` folds `θ_C·C` into `v_value` **only when θ_C is present** (Stage 2);
  θ_C absent ⇒ the three-index V, C reported-alongside (Stage 1). The `c_value` from `_score_c` is
  now captured for the fold. `CompositeResult.c_index` is populated in both stages (reported), and in
  v1.4 it is also summed into `v_index`.
- **`draft_coefficients.py`** — `draft_v1_coefficient_set` parameterised (`theta`, `theta_c`,
  `methodology_version`); `draft_v1_4_coefficient_set` — the four-index draft (placeholder θ split
  0.25/0.25/0.35/0.15, `client_usable=False`, methodology `1.4`).
- **`docs/ATLAS-Methodology-v1.4.md`** + **ADR-0031** — the four-index §5.1, the fail-loud rule, and
  the draft-until-panel activation gate.

**Not activated live.** The platform's active set stays v1.1 three-index, so existing assessments
(no captured C) keep scoring. Activating the four-index V is the single-point flip in `active.py`,
gated on the θ_C panel's four ratified weights + C-capture coverage (ADR-0031).

## Acceptance / verification

`tests/test_atlas_engine_golden_master_v2.py` — the four-index V reproduces the hand-computed oracle
(`V = 0.25·B + 0.25·P + 0.35·L + 0.15·C`), the v1 three-index master is untouched (0.478565), V equals
the weighted four-index sum. `tests/test_c_engine.py` — θ_C without `scores_c` refused; the four-term
Σθ≠1 refused; C is **not** folded into V without θ_C (the load-bearing guarantee). Golden master v1
byte-identical; schema parity green; pyright + ruff clean.

## Why

Stage 2 completes ADR-0023's staged entry: C stops being reported-alongside and becomes the fourth
term in the headline composite, making V a four-index score (B/P/L/C) under a new
ATLAS-Methodology-v1.4. This is deliberately deferred and **gated**: changing the V equation is the
one change the staged design worked to avoid until the weighting is legitimate. It must not begin
until Stages 1 are done AND a θ_C elicitation panel has been convened — the launch-default reuse of
existing coefficients (ADR-0023 I-4) is explicitly *not* a basis for a headline-weight change.

## What to build

Files:
- `src/grassmarket/atlas/assessments.py` — add `theta_c` and extend the Σθ=1 validator
  (`assessments.py:108`) so B+P+L+C weights sum to 1; **the engine must REFUSE a four-index V when
  `θ_C` is absent — never default to 0.**
- `src/grassmarket/atlas/engine.py` — fold C into the composite at `engine.py:76-80`
  (`v_value = θ_b·B + θ_p·P + θ_l·L + θ_c·C`). `CompositeResult.c_index` moves from reported to summed.
- Re-elicit **all four** θ (B, P, L, C) via the θ_C elicitation panel — the four weights are set
  together, not C bolted onto frozen B/P/L weights.
- `tests/test_atlas_engine_golden_master_v2.py` (new) — cut a **golden-master v2** hand-computed
  against the four-index V and the new θ set; the v1 golden master (V=0.478565) is retired to a
  legacy/back-compat fixture, not deleted.
- `docs/ATLAS-Methodology-v1.4.md` — the methodology version that introduces the four-index V
  (per non-negotiable #2, a scoring change is an ADR + new methodology version, never a silent edit).

Reuse: `_score_c` and the C coefficients from GRS-0082; the Σθ validator structure; the
golden-master harness.

New: `theta_c`, the four-index V equation, golden-master v2, Methodology v1.4.

## Acceptance / verification

- With `θ_C` present and Σθ=1, V is the four-index composite and reproduces golden-master v2 exactly.
- With `θ_C` **absent**, the engine raises — it never defaults θ_C to 0 or silently drops C
  (fail-loud test; this is the load-bearing guarantee of this ticket).
- Σθ≠1 (including the four-term sum) is rejected by the validator.
- The retired v1 golden master is preserved as a legacy fixture and still documents the pre-v1.4 V.
- ADR + Methodology v1.4 landed alongside the code (no silent scoring edit).

## Gating (do not start until all true)

- Stages 1 complete: GRS-0080–0085 shipped.
- The θ_C elicitation panel has been convened and produced the four re-elicited weights.
- ADR-0023 Stage-2 trigger satisfied.

## Not in scope

- The θ_C elicitation exercise itself (an offline panel, not a code ticket).
- Any Stage-1 reporting behaviour — GRS-0082 through GRS-0085.
