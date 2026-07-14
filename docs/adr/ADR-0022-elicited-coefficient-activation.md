# ADR-0022 — The elicited coefficient set and its panel-gated activation

- **Status:** Accepted
- **Loop:** 6 (GRS-0033)
- **Normative source:** Methodology v1.2 §6 (elicitation protocol, provenance); CLAUDE.md #2
  (implement the settled methodology), #3 (fail loud), #7 (two-track / value bridge); GRS-0015
  (the client-usable gate).
- **Builds on:** ADR-0001 (registry + CoefficientSet load-time gate), ADR-0004 (draft coefficients
  + strength encoding), ADR-0006 (weight provenance).

## Context

The engine has always scored against the **draft** coefficient set
(`v1-draft-pending-elicitation`, `client_usable=False`): uniform placeholder weights under a
`WeightMethod.DIRECT` provenance record, explicitly not panel output. The GRS-0015 gate
(`resolve_mode`) refuses to price a client-facing pack from a non-client-usable set, so the draft
set can only ever render watermarked internal drafts. That is the safe default and it has held
through Loops 1–6.

Two things were still missing for launch:

1. A **client-usable coefficient set** — `client_usable=True`, every weight family carrying a real
   Weight Provenance Record (panel, method, dispersion, review-due) — so the gate can open and the
   methods appendix can state "weights expert-elicited [date], review due [date]" truthfully.
2. A **single, deliberate activation point**. The routers previously imported
   `draft_v1_coefficient_set` directly at four call sites. "Which set is live" was therefore a
   four-place edit, and there was no recorded, reviewable moment at which the platform starts
   pricing clients on elicited weights.

The ratified panel **values** are a hard external dependency (the weight-elicitation panel running —
founder track). Everything else is buildable now, and the machinery must not wait on the numbers.

## Decision

### 1. Ship the elicited set now, with provisional panel-provenanced values

`grassmarket/atlas/elicited_coefficients.py` builds `elicited_v1_coefficient_set` — version
`v1-elicited-2026`, `client_usable=True`, non-uniform panel weights (θ = 0.25/0.35/0.40, α_L = 0.65)
distinct from the draft placeholders, and a Weight Provenance Record on **every** populated family
(`set_by="bruntsfield-elicitation-panel-2026"`, swing-weighting / AHP / Delphi methods, dispersion,
review-due 2027-07-10). `CoefficientSet` refuses to construct a populated family with no provenance,
so "every elicited weight traces to a provenance record" is a construction-time guarantee, not a
convention.

The **values are provisional** pending the panel's final ratification (recorded in the set's notes).
Swapping them for the ratified figures touches no structure and does not move the gate — only the
numbers. The elicited-set golden master (`test_elicited_golden_master`) pins the composite the
current values produce, so any change to them fails loud in CI.

### 2. There are TWO gated artifacts; activation flips both seams together

A client pack is priced from two `client_usable`-gated artifacts, not one:

- the **§5 coefficient set** (θ/α/λ/δ/W) — `active_coefficient_set`;
- the **§7 uncertainty model** (the input-distribution widths behind every P10/P50/P90 range,
  tornado bar, and weight-stability interval) — `active_uncertainty_model`.

Both live in `grassmarket/atlas/active.py`, and both are the **only** resolvers every runtime
scoring and deliverable path uses (assessments, committee, deliverables routers all route through
them). Both return the **draft** (`client_usable=False`) artifact today. `elicited_v1_uncertainty
_model` is the §7 twin of `elicited_v1_coefficient_set`: client-usable, panel-provenanced,
provisional values pending the same sign-off.

Activation is a one-line change to **each** function, in the **same reviewed commit**:

```python
# active.py — the entire activation change, once the panel ratifies the values:
def active_coefficient_set(registry): return elicited_v1_coefficient_set(registry)
def active_uncertainty_model():       return elicited_v1_uncertainty_model()
```

This is deliberate and recorded: no import side effect, no environment toggle, no clock, no
automatic promotion. Flipping only one seam is a defect the gate catches (see §3): a client pack may
not mix elicited weights with draft uncertainty widths, or vice versa.

### 2a. The gate refuses EITHER non-client-usable artifact

`resolve_mode` refuses a client pack on a non-client-usable coefficient set;
`assert_uncertainty_client_usable` refuses one on a non-client-usable uncertainty model. Both are
enforced at the single-run deliverable chokepoint before any range is drawn. So the guarantee
"draft placeholders never reach a client" holds for the §7 widths exactly as it does for the §5
weights — defence-in-depth, independent of which artifact the seam happens to serve. (The roadmap
pack computes no Monte Carlo of its own; it embeds only the active model's version label, sourced
from the same seam, so it stays consistent through the flip.)

### 3. The methods appendix tells the truth about which set priced the pack

The appendix renders weight provenance generically from `coefficients.provenance`. It now
distinguishes by method: a `DIRECT` family (the draft placeholder) renders "Draft placeholder
weights (not expert-elicited)"; an elicited family renders "Weights expert-elicited [date]
([method]), review due [date]". A watermarked draft can no longer imply its weights were elicited.

## Consequences

- **The gate chain is proven end-to-end now**, before the panel values land: the client gate opens
  under the elicited coefficient set and refuses under the draft set (tested both ways); it
  independently refuses a client pack whose §7 uncertainty model is draft even when the coefficients
  are client-usable (tested); provenance is mandatory on both artifacts (tested); and the elicited
  golden master reproduces exactly (with α pinned separately, as the uniform fixture cannot move
  it).
- **The draft set remains the active default** until a future reviewed commit flips `active.py`.
  Nothing prices a client on placeholder weights in the meantime — the fail-safe still holds.
- **Registry ratification** (criticals + subcomponent set moving from `draft-pending-ratification`
  to ratified, founder sign-off) rides with the same activation moment; it is external and recorded
  separately, not automated here.
- **Follow-up:** full elicitation-record *ingestion* (parsing external panel records into provenance
  rather than the representative values baked in here) remains a founder-track task; the provenance
  shape it must populate is fixed by this set.
