# GRS-0237 — The engine white paper: one document that answers "is this up to scratch?"

**Status:** Planned (2026-07-31, founder: "I am not sure if the engine calculator behind the
assessment wizard is up to scratch — need a white paper on this"). **Priority:** HIGH.
**Loop:** first-time-user coherence. **Relates to:** GRS-0179, GRS-0180, GRS-0150, GRS-0223, ADR-0046.

## Why

The founder cannot currently answer a due-diligence question about the engine with one document.
The material exists but is scattered and part-stale:

- `docs/ATLAS-Methodology-Guide.md` is already ~80% of a white paper (formal model, behavioural
  properties, elicitation design, reliability programme, limitations, prior-framework comparison) —
  but it declares v1.1 normative and predates v1.4–v1.6, the founder gate (its governance section
  still describes the retired Rating Committee), the C-index, the critical-control cap and the
  one-number rule.
- `docs/ATLAS-Scoring-Explained.md` (advisor explainer) and `docs/ATLAS-7Powers-Adaptation.md`
  (Helmer packet, ADR-0046 still Proposed pending his review) serve different audiences and neither
  is framed as validation.
- The validation evidence that exists is genuinely strong — golden master (V = 0.478565, every
  intermediate pinned), ~140+ engine/coefficient tests, property tests, the dispersion analysis —
  and the gaps are equally real: **retail coefficients are uniform draft placeholders; the
  wealth/exchange "elicited" sets are engineering starter values activated by founder direction
  (ADR-0037) whose provenance records name a panel that has not run**; no systematic weight
  sensitivity beyond the θ/α variant grid; no outcome evidence; reliability machinery dormant with
  zero measurements.

A white paper that hides those gaps fails its own purpose. One that states them, with the roadmap
to close them, is what survives a sceptical reader — the same honesty doctrine the product itself
runs on (non-negotiable #3).

## Scope

1. **`docs/ATLAS-White-Paper-v1.md`**, one document, external-reader audience (a client's CTO, an
   acquirer's DD team, Helmer's office). Structure: what the engine computes (the full chain,
   subcomponents → q_m → B/P/L(/C) → V, with the actual formulas and the min()/bottleneck
   semantics); why each design choice (two tracks, fail-loud, uncertainty by evidence grade); the
   7 Powers derivation and its boundary (what is Helmer's, what is Bruntsfield's — per ADR-0046);
   worked example (the golden-master firm end to end); validation evidence with counts and file
   references; **a limitations register that names the coefficient status plainly**; the closure
   roadmap (elicitation panel, calibration data, outcome register thresholds from Guide §1.2).
2. **Re-baseline the Methodology Guide** to v1.6 as part of the same pass, or fold it into the
   white paper and retire it — decide and state which; two documents claiming different normative
   versions is worse than either choice.
3. **Correct the elicited-set provenance records** (`elicited_coefficients.py`) so they say what
   happened — founder-directed starter values, panel pending — rather than naming
   "bruntsfield-elicitation-panel-2026" with method strings for a session that has not occurred.
   A provenance record that overstates its evidence is a D-class defect in our own terms.
4. **Add the missing sensitivity exhibit:** a one-off analysis (committed under `docs/analysis/`)
   sweeping λ/δ/W_g/strength-encoding perturbations and reporting rank-stability of module ordering
   and V across the three showcase firms — the question a reviewer asks that the θ/α grid does not
   answer.
5. **Surface it.** The Guide and the report appendix link to the white paper; the wizard's
   "How the maths works" link points at the explainer which points at the white paper.

## Test plan

1. Doc-structure test (pattern: `tests/test_docs_powers_adaptation.py`): required sections present,
   version pinned to Methodology v1.6, no stale "Rating Committee" governance language.
2. Provenance-record tests updated to the corrected wording; nothing else in scoring changes —
   golden master byte-identical.
3. The sensitivity notebook/script is committed and re-runnable (`tools/` or `docs/analysis/`),
   seeded, offline.
4. Standing gate: pytest, pyright, ruff.

## Out of scope

- Running the elicitation panel (GRS-0150 owns the values).
- Changing any scoring behaviour whatsoever.
- The Helmer review itself (GRS-0201 packet; ADR-0046 ratification).

## Acceptance

The founder hands one PDF/markdown document to a sceptical technical reader and it answers what the
engine does, why, how it is tested, what is not yet proven, and when that closes — without a single
claim the repo cannot back.
