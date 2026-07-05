# ADR-0004 — Numeric encoding of ordinal power strength for the P index

- **Status:** Accepted (2026-07-04; folded into Methodology v1.1 §5.4). The specific encoding
  *values* remain draft-pending-elicitation (ratified by the θ/α panel), carried with a Weight
  Provenance Record.
- **Date:** 2026-07-04
- **Deciders:** Founder + engineering + elicitation panel (Loop 1)
- **Normative source:** `docs/ATLAS-Methodology-v1.md` §2, §5.4, §8; ADR-0002.
- **Raised by:** GRS-0003, and review items A3/B5 (the encoding must be an ADR, not a script
  constant) and B2 (B/P range comparability).

## Context

The continuous Strategic-Power index is `P = Σ_j w_j·strength_j / Σ_j w_j` (§5.4), which needs a
*numeric* `strength_j`. But power/triad strength is an **ordinal** rating — None / Emerging /
Established / Wide — reported to clients as a rating, never a decimal (ADR-0002). The Methodology
uses `strength_j` numerically without fixing the ordinal→numeric encoding. The GRS-0003 fixture
picked one in a script constant; that decision must be an ADR.

## Decision

1. **The triad and per-power ratings remain ordinal** (ADR-0002 unchanged). This ADR governs
   *only* the internal numeric encoding used to compute the continuous P index that feeds V.
2. **Draft encoding (pending elicitation):**

   | Strength | Encoded value |
   |---|---|
   | None | 0.0 |
   | Emerging | 0.4 |
   | Established | 0.7 |
   | Wide | 1.0 |

   These values are **draft-pending-elicitation** — ratified by the same panel that sets θ and α
   (swing-weighting + Delphi, Methodology §6), and carried with a Weight Provenance Record.

## Open questions for the panel (do not freeze without them)

- **Encoding floor asymmetry (review B2).** The maturity scale floors at 0.2 (Basic), so B and L
  never go below 0.2, but this encoding floors P at 0.0 (None). With equal θ, B ∈ [0.2, 1] and
  P ∈ [0, 1] are **not on comparable effective ranges**, which distorts V. Resolved by ADR-0005
  (accepted): do not rescale — swing-weighted θ prices the ranges. Flagged here because it and the
  P encoding were decided together.
- **Incumbent drag (review B4) — RESOLVED by ADR-0007.** Most incumbent brokerages structurally lack
  the origination/takeoff powers, so a uniform mean pulls P down (Meridian P = 0.271). This is now
  the accepted, honest result: powers are **never** Not Applicable (all 7 in scope, comparable
  denominator), a weak power scores a real low strength, and swing-weighted θ (ADR-0005) prices the
  low-P range. The panel may still set non-uniform power weights `w_j` reflecting stage-achievable
  powers (§8), but N/A renormalisation is explicitly rejected.

## Consequences

- The category-error wall (ADR-0002) is untouched: ordinal in, ordinal out for client outputs;
  the encoding is an internal computation detail with provenance.
- Until the panel ratifies, any CoefficientSet carrying this encoding is `draft-pending-elicitation`
  and not client-usable.
