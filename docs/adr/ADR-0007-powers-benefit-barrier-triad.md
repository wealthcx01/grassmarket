# ADR-0007 — Powers carry Benefit + Barrier; the triad is derived; powers are never Not Applicable

- **Status:** Accepted (2026-07-04; folded into Methodology v1.1 §2, §8)
- **Date:** 2026-07-04
- **Deciders:** Founder + engineering + rating committee (Loop 1)
- **Normative source:** `docs/ATLAS-Methodology-v1.1.md` §2, §8; ADR-0002, ADR-0004.
- **Raised by:** review item B8 (triad not computable) and the ratification decision that powers are
  always in scope (superseding the earlier B4 "N/A for powers" proposal).

## Context

Helmer's test is dual and binary: a power exists only where there is **both** a Benefit (economic
advantage) **and** a Barrier (why rivals can't arbitrage it away). The prototype and the first
GRS-0003 draft stored a single strength per power, which made the Platform Power triad
**uncomputable** — §2 derives Perceived Value from the *Benefit* side of Branding/Switching Costs
and Defence Value from the *Barrier* side aggregate.

An interim draft (superseded here) let a structurally-weak power be marked **Not Applicable** and
dropped from P. On ratification John rejected that: N/A invites analysts to hide a weak power rather
than score it, and it makes P incomparable across firms (different denominators). **All 7 powers are
always in scope.** Absent-because-weak is a real reading, and Helmer's both-required test already
collapses a one-sided power to its (often None) weaker side without needing an N/A escape hatch.

## Decision

1. **Each power carries a Benefit strength and a Barrier strength** (both ordinal: None / Emerging /
   Established / Wide). The power's overall strength is the **weaker of the two** (a power is only as
   strong as its missing side — Helmer's both-required test). P uses that weaker strength via the
   ADR-0004 encoding.
2. **Powers are never Not Applicable.** All 7 powers are scored for every firm; P is the mean of the
   weaker-side strengths across **all 7** (no renormalisation, comparable denominators). A
   structurally-irrelevant power scores a real low level (typically None on its weaker side), not a
   dropped N/A. (Meridian: Network Economies and Counter-Positioning are Emerging-benefit /
   None-barrier → strength None — real and low, not absent.)
3. **The triad is derived from the split data (ordinal out, ADR-0002):**
   - **Defence Value** = the Barrier-side aggregate across **all 7** powers (the moat) — the literal
     §2 across-all-powers barrier reading.
   - **Perceived Value** = the Benefit-side of Branding + Switching Costs.
   - **Economic Value** = B's scale + unit-economics signal.
   Each numeric aggregate maps to an ordinal band by the thresholds below. The client sees only the
   ordinal `rating`; the numeric `score` is audit-only.

## Triad thresholds — nearest-named-level discretisation of the ADR-0004 encoding

The bands are **not** free parameters. A numeric aggregate in [0,1] is discretised to the **nearest
named strength level** under the ADR-0004 encoding (None 0.0 · Emerging 0.4 · Established 0.7 ·
Wide 1.0); the band thresholds are the **midpoints between adjacent encoded anchors**:

| Boundary | Midpoint of… | Threshold | Band above it |
|---|---|---|---|
| None ↔ Emerging | (0.0 + 0.4)/2 | **0.20** | Emerging |
| Emerging ↔ Established | (0.4 + 0.7)/2 | **0.55** | Established |
| Established ↔ Wide | (0.7 + 1.0)/2 | **0.85** | Wide |

So Wide ≥ 0.85, Established ≥ 0.55, Emerging ≥ 0.20, else None: a value ≥ 0.85 is closer to Wide
(1.0) than to Established (0.7), and so on. If ADR-0004's encoding is re-elicited, these thresholds
move with it (they are derived, not independently tuned).

## Band definitions — falsifiable by duration (§8)

Helmer's Power is about *persistence*, so each band carries a one-line falsifiable duration test
(how long the advantage has held / how long a well-resourced rival would need to erase it):

- **None** — no durable advantage; a competent rival could match it within a normal budget cycle
  (≲ 1 year). *Falsified if* the firm has held the edge for years while rivals tried and failed.
- **Emerging** — replicable by a well-resourced rival within ~1–2 years; not yet defensible across a
  full strategy cycle. *Falsified if* a rival matched it in months, or if it has already held 3+ years.
- **Established** — has persisted and would take a rival ~3–5 years (a full strategy cycle) and
  material investment to erode. *Falsified if* a rival replicated it inside ~2 years.
- **Wide** — structural; has held 5+ years with no credible replication path on any planning horizon.
  *Falsified if* any rival has closed the gap within ~5 years.

## Consequences

- The triad is a real, computed, client-facing output instead of narrative-only.
- P has a fixed 7-power denominator, so it is comparable across firms and across time (no N/A means
  no shifting base). It will read lower for incumbents whose origination/takeoff powers are genuinely
  weak — which is the honest result, and swing-elicited θ (ADR-0005) prices the range.
- **Open for ratification:** the per-firm Benefit/Barrier strengths (draft); whether Economic Value
  should also fold in take-rate durability explicitly (§2). Committee sign-off still governs any
  Established+ power or triad rating above None (§8).
- The `bcap_contracts.assessments.PowerAssessment` contract (which already holds Benefit/Barrier
  *evidence*) gains Benefit/Barrier *strengths* when the wizard is built (Loop 2).
