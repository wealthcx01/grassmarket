# ATLAS Methodology v1.4

**Bruntsfield Capital — CONFIDENTIAL — July 2026**

**Status: Stage 2 of ADR-0023 (four-index V).** v1.4 completes the staged entry of the C-index: C
stops being reported-alongside and becomes the **fourth term of the headline composite V**. It amends
**§5.1 (the composite) only**; §13 (the C-index definition), §2, and everything else are carried
forward from v1.3 unchanged. Build ticket: GRS-0086.

v1.4 is a **deterministic change** and therefore ships with a new hand-computed oracle
(`tests/test_atlas_engine_golden_master_v2.py`). The v1.1/v1.3 three-index golden master (V=0.478565)
is **preserved untouched** — v1.4 is a new version, never an edit to the settled one (non-negotiable
#2).

---

## 1.1 Changelog: v1.3 → v1.4

| Amendment | Section | ADR |
|---|---|---|
| **§5.1 composite becomes four-index:** `V = θ_B·B + θ_P·P + θ_L·L + θ_C·C`, Σθ = 1 | §5.1 | ADR-0023, ADR-0031 |
| The four θ are **re-elicited together** (the v1.1 θ are not reused with a bolted-on θ_C) | §5.4 | ADR-0031 |

All other sections are incorporated by reference from v1.3.

---

## §5.1 The composite (amended)

Platform Value V is the θ-weighted sum of the four indices:

> **V = θ_B·B + θ_P·P + θ_L·L + θ_C·C**,  with  **θ_B + θ_P + θ_L + θ_C = 1**.

- **C** is the Customer-Proposition index defined in §13 (v1.3), computed on the L aggregation family
  over the ten Phase-E modules. Its construction is unchanged from Stage 1; only its **destination**
  changes — from reported-alongside to summed-in.
- **Score-domain only.** As in v1.1 §5.1, this equation combines the four continuous indices in the
  score domain; it never mixes score points with currency (ADR-0002).

### Fail-loud (the load-bearing guarantee)

- An engine asked for a four-index V **must carry an elicited θ_C**. A coefficient set that weights C
  into V (θ_C present) **must also compute C**; a set that computes C but has **no θ_C** stays
  three-index (Stage 1) and reports C alongside V. **θ_C is never defaulted to 0** and C is never
  silently folded (ADR-0001, ADR-0023 §4). Enforced at coefficient-set construction and in the
  engine (GRS-0086).

## §5.4 Weight elicitation (amended)

The four θ (B, P, L, C) are elicited **together** by the θ_C elicitation panel — the re-split makes
room for the customer lens rather than appending it. Until the panel convenes, any v1.4 coefficient
set is a **documented draft placeholder** (`client_usable=False`): it may compute and report a
four-index V internally, but it **may not price a client deliverable**. Activating the four-index V
for the live/client path is the single-point flip in `active.py`, gated on the panel's four
ratified weights (ADR-0023 §Gating).

---

## Golden master v2

The v1.4 oracle combines the **ratified Meridian B/P/L** (byte-identical to the v1 golden master) with
a fixed C rating pattern under the draft v1.4 θ split (0.25/0.25/0.35/0.15, placeholder). The
arithmetic identity `V = θ_B·B + θ_P·P + θ_L·L + θ_C·C` is the invariant asserted; the oracle is re-cut
when the θ_C panel ratifies the real four weights.
