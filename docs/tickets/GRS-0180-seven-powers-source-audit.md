# GRS-0180 — 7 Powers mathematics adaptation: the normative document

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: In review (2026-07-24) — docs/ATLAS-7Powers-Adaptation.md authored, PR open; awaiting founder confirmation for._
**Loop:** founder-feedback remediation, Wave 1. Carries ADR-0046. Feeds GRS-0201 (wizard).

## Why

The Powers engine already implements Helmer's dual test (strength = min(Benefit, Barrier),
ADR-0007), but the product's Powers content is summary-grade because the source was
copyright-restricted. The founder now holds Helmer's personal permission to embed and adapt the
supplement's mathematics for our subject area — wealth platforms: wealth advisory firms,
brokerages, and exchanges. Helmer reviewing the result sets the bar: faithful where we embed,
explicit where we adapt, precise everywhere.

## Inputs

- The supplement: `7Powers.pdf` (87 pages, image-set — equations are figures, not text).
- The full-supplement extraction memo, committed in-repo at
  `data/reference/7powers-math-extraction.md`: the Fundamental Equation and its derivation; all seven Surplus Leader Margin
  formulas with every symbol defined; the Power Intensity Determinants; the Power Dynamics
  toolkit, graphical representation, and full glossary; and per-power first-pass ATLAS mapping
  notes with worked wealth-platform examples per segment. All 87 pages were read with no
  illegibility gaps. Two precision notes to confirm with Helmer are recorded in the memo's §5:
  (1) the p.7 derivation exponent indexing convention `(1+η)^{i+1}`; (2) the p.44 Branding
  logistic coefficient read as `(Z−1)` (matching the identical Process Power formula on p.60 and
  required by the `B(0)=1` normalisation) rather than the printed lowercase `(z−1)`. Verify each
  equation against the PDF before it enters the adaptation document.

## Scope

1. **Author `docs/ATLAS-7Powers-Adaptation.md`** (the single normative source for all Powers
   content), structured:
   - Front matter: the rights registration (grantor Hamilton Helmer; grantee John Gallagher;
     scope: the supplement's mathematics adapted for wealth platforms; date 2026-07-23;
     condition: Helmer reviews the output) and the standard attribution line.
   - §1 The Fundamental Equation of Strategy — the equation and derivation with every symbol
     defined, then its wealth-platform reading (what M0, g, s̄, m̄ mean for a brokerage, a
     wealth manager, an exchange).
   - §2 Per power (all seven): Helmer's definition; the Benefit; the Barrier; the Surplus
     Leader Margin formula with symbols; the intensity determinants; the time-window (Power
     Progression stage). Then, clearly marked as adaptation: what this power concretely looks
     like in each of the three segments, and how its intensity determinants translate into the
     ATLAS benefit/barrier rating anchors.
   - §3 The Power Dynamics mapping: how the progression stages relate to the ATLAS assessment
     moments (prospect → assessment → roadmap).
   - §4 The ATLAS correspondence table: engine concept ↔ supplement concept, including the
     places we deliberately extend beyond Helmer (B, L, C are ours) and the explicit statement
     that P scoring is unchanged by this document (ADR-0046 §4).
2. **Adaptation discipline:** embedded mathematics is transcribed faithfully (checked
   symbol-by-symbol against the PDF); adapted content is always introduced as such in the text
   so the review can tell them apart. Nothing outside the grant (narrative chapters, case-study
   prose) is reproduced.
3. **Cross-updates in the same PR:** ATLAS-Scoring-Explained.md (GRS-0179) §5 references the
   adaptation document instead of paraphrasing; the Methodology's §4 gains a source note
   pointing at it (no normative change).

## Test plan

- `tests/test_docs_powers_adaptation.py`: asserts the adaptation document exists, carries the
  rights front matter and attribution line, and contains a section for each of the seven powers
  (guards against partial authoring).
- Golden master suite unchanged and passing (no scoring surface is touched by this ticket).

## Out of scope

- Wizard/Guide embedding (GRS-0201). Any change to P scoring (future ADR + Methodology v1.7,
  only after Helmer's review). Academy course content.

## Acceptance

The adaptation document stands alone: every equation checked against the PDF, every adaptation
marked, all three segments covered per power, rights and attribution recorded. The founder
confirms it is ready to go into the Helmer review packet (assembled in GRS-0201).

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `30d0e8a` (GRS-0180: 7 Powers mathematics adaptation — the normative document).

This ticket carried no *What shipped* record; the commits above are that record.
