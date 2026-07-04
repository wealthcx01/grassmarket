# ADR-0007 — Powers carry Benefit + Barrier; the triad is derived; powers can be Not Applicable

- **Status:** Proposed (awaiting John / committee)
- **Date:** 2026-07-04
- **Deciders:** Founder + engineering + rating committee (Loop 1)
- **Normative source:** `docs/ATLAS-Methodology-v1.md` §2, §8; ADR-0002, ADR-0004.
- **Raised by:** review items B8 (triad not computable) and B4 (no N/A for powers; incumbent drag).

## Context

Helmer's test is dual and binary: a power exists only where there is **both** a Benefit (economic
advantage) **and** a Barrier (why rivals can't arbitrage it away). The prototype and GRS-0003
stored a single strength per power, which (a) made the Platform Power triad **uncomputable** —
§2 derives Perceived Value from the *Benefit* side of Branding/Switching Costs and Defence Value
from the *Barrier* side aggregate — and (b) forced every structurally-irrelevant power to score
None = 0, dragging P down for incumbents (Meridian P = 0.271 despite an Established switching-costs
moat).

## Decision

1. **Each power carries a Benefit strength and a Barrier strength** (both ordinal: None / Emerging
   / Established / Wide). The power's overall strength is the **weaker of the two** (a power is only
   as strong as its missing side — Helmer's both-required test). P uses that weaker strength via
   the ADR-0004 encoding.
2. **Powers support a Not Applicable state.** A power that is structurally irrelevant to the
   business's model (e.g. Network Economies / Counter-Positioning for a non-marketplace retail
   brokerage) is marked N/A with a rationale, **dropped from P, which renormalises** — the same
   §3.2 discipline subcomponents already use. "N/A" ≠ "None": absent-because-irrelevant is not
   absent-because-weak. (Whether a given firm's powers are N/A is an analyst/committee judgement.)
3. **The triad is derived from the split data (ordinal out, ADR-0002):**
   - **Defence Value** = the Barrier-side aggregate across all *applicable* powers (the moat).
   - **Perceived Value** = the Benefit-side of Branding + Switching Costs.
   - **Economic Value** = B's scale + unit-economics signal.
   Each numeric aggregate maps to an ordinal band by draft thresholds (Wide ≥ 0.85, Established
   ≥ 0.55, Emerging ≥ 0.2, else None) — **draft, to be ratified**. The client sees only the ordinal
   `rating`; the numeric `score` is audit-only.

## Consequences

- The triad becomes a real, computed client-facing output instead of narrative-only.
- P stops being dragged to zero by structurally-irrelevant powers (Meridian P 0.271 → 0.38 after
  marking Network Economies and Counter-Positioning N/A).
- **Open for ratification:** the N/A classification per firm; the triad numeric→ordinal thresholds;
  whether Economic Value should also fold in take-rate durability explicitly (§2). Committee
  sign-off still governs any Established+ power or triad rating above None (§8).
- The `bcap_contracts.assessments.PowerAssessment` contract (which already holds Benefit/Barrier
  *evidence*) gains Benefit/Barrier *strengths* when the wizard is built (Loop 2).
