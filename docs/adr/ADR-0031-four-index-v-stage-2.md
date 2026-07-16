# ADR-0031 — Four-index V: fold C into the composite (ADR-0023 Stage 2, Methodology v1.4)

- **Status:** Accepted (2026-07-16). Founder greenlit Stage 2 ("GRS-0086 is a go, fold C into V").
- **Date:** 2026-07-16
- **Deciders:** Founder + engineering
- **Normative source:** `docs/ATLAS-Methodology-v1.4.md`; ADR-0023 §4 (staged entry) + §Gating.
- **Implements:** GRS-0086 (fold-c-into-v).

## Context

ADR-0023 staged the C-index into V to protect the ratified numbers: **Stage 1 (v1.3)** defined,
scored, and **reported** C alongside V with §5.1 untouched (the golden master and the `1.1`
deterministic stamp survived); **Stage 2 (v1.4)** folds C into the headline composite. Stage 1
(GRS-0080–0085) is shipped. The founder has greenlit Stage 2.

The one risk the staged design worked to avoid is changing the V equation on illegitimate weights.
Two forces shape this decision: (1) folding C in is a **deterministic** change — it needs its own
hand-computed oracle and must not edit the settled one (non-negotiable #2); (2) the real four θ come
from a **θ_C elicitation panel** that re-splits the weights together — the launch-default reuse of
existing coefficients (ADR-0023 I-4) is explicitly *not* a basis for a headline-weight change.

## Decision

1. **Four-index composite (Methodology v1.4 §5.1):** `V = θ_B·B + θ_P·P + θ_L·L + θ_C·C`, Σθ = 1.
2. **θ_C is a first-class, optional headline weight.** `CoefficientSet.theta_c`: **present** ⇒
   four-index V (Σθ over four = 1) and the set MUST score C; **absent** ⇒ three-index V (Stage 1),
   so v1.1/v1.3 sets are byte-identical. Both invariants are enforced at construction (Σθ validator +
   `θ_C ⇒ scores_c`), and the engine adds the θ_C·C term only when θ_C is present.
3. **Fail-loud, never a default.** A four-index V is impossible without an elicited θ_C — the engine
   never defaults θ_C to 0 and never silently folds C. A set weighting C into V without computing C
   is refused (ADR-0001, ADR-0023 §4).
4. **Golden master v2.** `tests/test_atlas_engine_golden_master_v2.py` pins the four-index oracle; the
   v1 three-index master (V=0.478565) is preserved untouched.
5. **Draft until the panel convenes.** The shipped v1.4 coefficient set
   (`draft_v1_4_coefficient_set`) uses a **placeholder** θ split (0.25/0.25/0.35/0.15) and is
   `client_usable=False`. It computes/reports a four-index V internally but **cannot price a client
   deliverable**. Activating the four-index V for the live/client path is the single-point flip in
   `active.py`, gated on the panel's four ratified weights **and** on assessments having C captured.

## Consequences

- **Capability shipped, activation gated.** The four-index V is real, tested, and available under
  v1.4; the platform's live path stays on the v1.1 three-index composite (so existing assessments
  without captured C keep scoring) until the θ_C panel ratifies the weights and C-capture coverage is
  in place. That flip is one reviewed change to `active.py`.
- **No regression.** The settled three-index V and its golden master are untouched; v1.4 is additive.
- **Provenance honesty.** A draft-weighted four-index V is watermarked-internal only, exactly as the
  draft three-index V is today — the client-usable gate (ADR-0022) is unchanged.
