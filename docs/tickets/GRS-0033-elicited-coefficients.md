# GRS-0033 — Elicited coefficients: ingestion + client-usable flip

- **Loop:** 6
- **Branch:** `grs-0033-elicited-coefficients`
- **Status:** Planned — **the launch bottleneck**
- **Normative source:** Methodology v1.2 §6 (elicitation protocol, provenance); GRS-0015 (client-usable gate).
- **Depends on:** the weight-elicitation panel having run (founder track — hard external dependency). Everything else in this ticket is buildable beforehand.

## Goal

Replace `v1-draft-pending-elicitation` with the real, client-usable coefficient set — and prove the whole gate chain opens correctly.

## Scope

1. Elicitation-record ingestion: per coefficient family (θ, W_g, w, λ, δ, α, α_L, criticals, strength encoding) — method (swing/AHP/Delphi/Cooke), panel composition, rounds, dispersion, stability intervals → Weight Provenance Records.
2. New CoefficientSet version with `client_usable=True`; activation is explicit and recorded (ADR).
3. Golden-master companion fixture recomputed under the elicited set (the draft-set fixture is retained — it tests the engine; the elicited fixture tests the production configuration).
4. Methods appendix now renders real elicitation dates, methods, and review-due dates.
5. Registry ratification lands with this ticket if not before: criticals + subcomponent set move from `draft-pending-ratification` to ratified (founder sign-off recorded).

## Exit criteria

- The GRS-0015 gate admits client packs under the elicited set and still refuses under the draft set (tested both ways).
- Every elicited weight traces to its provenance record; none load without one.
- Elicited-set golden master reproduces exactly.
- Full gate green; CI green.
