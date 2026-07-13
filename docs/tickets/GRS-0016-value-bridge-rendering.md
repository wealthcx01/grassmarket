# GRS-0016 — Value-bridge rendering + Modernisation Roadmap

- **Loop:** 4
- **Branch:** `grs-0016-value-bridge-rendering`
- **Status:** Merged — PR #16
- **Normative source:** Methodology v1.2 §10 (value bridge); PRD §5; ADR-0002 (score/currency separation).
- **Depends on:** GRS-0006 (value layer), GRS-0015 (builder + client-usable gate).

## Goal

The flagship money pages of the Diagnostic pack — honest by construction. The Roadmap ranks by the Upgrade Priority Index; the value bridge prices beside it; the two are never divided into a single ROI number.

## Scope

1. Render the three-layer bridge from GRS-0006 outputs: cost model (Money), lever NPVs (Money, each with its full assumption register printed), strategic ordinal ratings (duration language only, never currency).
2. Modernisation Roadmap document: interventions ranked by Upgrade Priority Index (ΔV from full re-scoring), with the bridge alongside each entry.
3. Priority-vs-cost scatter chart; scenario comparison table (multiple named scenarios).
4. Every currency figure traces to a printed assumption; no currency figure appears without its register entry.
5. ADR-0002 AST guard must remain green: the document renders Score and Money side by side, but no function takes both.

## Exit criteria

- Roadmap generates from the golden-master run plus a worked scenario fixture.
- Assumption register renders complete for every lever NPV.
- Gate/watermark behaviour inherited from GRS-0015 (draft set → watermarked internal only).
- Full local gate green (ruff · pyright · pytest · pre-commit); CI green.
