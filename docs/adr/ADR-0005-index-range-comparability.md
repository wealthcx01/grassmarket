# ADR-0005 — Comparability of the B / P / L index ranges at composition

- **Status:** Proposed (awaiting John / elicitation panel)
- **Date:** 2026-07-04
- **Deciders:** Founder + engineering + elicitation panel (Loop 1)
- **Normative source:** `docs/ATLAS-Methodology-v1.md` §5.4, §6; ADR-0001.
- **Raised by:** review item B2.

## Context

`V = θ_B·B + θ_P·P + θ_L·L`. The three indices do **not** share an effective range:

- **L** floors at **0.2** — the maturity scale fixes Basic = 0.2 (ADR-0001, Methodology §3.1), so
  a module (and thus L) can never be below 0.2.
- **B** — the draft metric normalisation anchors also floor at **0.2**, so B ∈ [0.2, 1].
- **P** — the power-strength encoding floors at **0.0** (None = 0, ADR-0004), so P ∈ [0, 1].

With the **uniform draft θ = (0.30, 0.30, 0.40)** these unequal ranges distort V — a "zero" on P
costs more than a "zero" on B or L. Review B2 is correct that this must be resolved and documented.

## Decision

**Do not rescale the indices.** The range differences are absorbed by the θ-elicitation method the
Methodology already mandates: **swing weighting** (§6, Parnell & Trainor). Swing weighting elicits
each weight by ranking the *swing from worst to best on that criterion* — so a panellist weighting
B's swing (0.2 → 1) against P's swing (0 → 1) is pricing exactly these effective ranges. Range
sensitivity is the property swing weighting exists to capture; direct "importance" weighting is the
method that gets it wrong. Therefore:

1. The elicitation panel is **briefed with each index's effective range** (L: 0.2–1, B: 0.2–1,
   P: 0–1) when setting θ, and the resulting θ carries this in its Weight Provenance Record.
2. The Composite sheet **displays each index's effective range beside θ** (workbook change D6), so
   the range is visible wherever V is read.
3. The **uniform draft θ is explicitly non-range-aware** and is a placeholder only — the golden
   master's V under draft θ therefore carries the caveat that θ is un-elicited.

## Consequences

- No rescaling, so ADR-0001 (Basic = 0.2 immutable) is untouched and the indices keep their direct
  interpretation.
- The B2 distortion is real *only under uniform θ* and disappears once θ is swing-elicited — which
  is why the fixture is `draft-pending-ratification`.
- **Related:** whether to lift the metric bottom anchor off 0.2 toward P's 0.0 (to make B and P
  share a floor) is a separate, optional normalisation choice for the panel; this ADR does not
  require it, because swing weighting handles the difference either way.
