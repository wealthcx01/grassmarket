# GRS-0033 — Elicited coefficients: ingestion + client-usable flip

- **Loop:** 6
- **Branch:** `grs-0033-elicited-coefficients`
- **Status:** In review — machinery + gate chain delivered; ratified panel VALUES pending (external). See ADR-0022.
- **Normative source:** Methodology v1.2 §6 (elicitation protocol, provenance); GRS-0015 (client-usable gate).
- **Depends on:** the weight-elicitation panel having run (founder track — hard external dependency). Everything else in this ticket is buildable beforehand.

## Goal

Replace `v1-draft-pending-elicitation` with the real, client-usable coefficient set — and prove the whole gate chain opens correctly.

## Delivered vs external dependency (see ADR-0022)

- **Delivered + tested:** the client-usable elicited set (`elicited_v1_coefficient_set`,
  `v1-elicited-2026`, `client_usable=True`, non-uniform panel weights, a Weight Provenance Record on
  every populated family — mandatory at construction) AND its §7 twin
  (`elicited_v1_uncertainty_model`, the client-usable input-distribution widths behind the ranges);
  two activation seams (`atlas/active.py::active_coefficient_set` / `active_uncertainty_model`,
  routed through by every scoring/deliverable path) so activation is a one-line, reviewed,
  panel-gated flip of both together; the GRS-0015 gate proven both ways for coefficients (opens under
  elicited, refuses under draft) AND independently for the uncertainty model (a client pack refuses
  on a draft model even when the weights are client-usable); elicited golden master pinning the
  composite (α pinned separately — the uniform fixture cannot move it); the methods appendix now
  stating honest provenance (draft placeholder vs expert-elicited) with a per-family method column.
- **External dependency (founder track — the actual bottleneck):** the weight-elicitation panel
  ratifying the numeric VALUES, and registry ratification (criticals + subcomponent set). Swapping
  the provisional values for the ratified ones touches no structure and does not move the gate; the
  golden master fails loud if they change. Activation = flip `active.py` to return the elicited set,
  in a reviewed commit, once the panel signs off.

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
