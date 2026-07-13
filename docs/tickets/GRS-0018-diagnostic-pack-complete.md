# GRS-0018 — Complete the Diagnostic pack + charts

- **Loop:** 4
- **Branch:** `grs-0018-diagnostic-pack-complete`
- **Status:** Merged to main (PR #18)
- **Normative source:** PRD §5 (the seven standard deliverables); Methodology v1.2 §3.2 (Not Assessed semantics), §7 (uncertainty rendering).
- **Depends on:** GRS-0015, GRS-0016.

## Goal

All seven PRD §5 deliverable types generate from a finalised scoring run.

## Scope

1. **Executive Summary** (3pp, board-ready).
2. **Infrastructure Heatmap**: module × subcomponent grid, colour-banded by rating gate; Not Assessed rendered visually distinct — never red, never conflated with Basic (Methodology §3.2).
3. **Technical Appendix**: auto-generated from methodology version + provenance records (extends the GRS-0015 methods appendix).
4. **Workshop Output** template (pre-engagement mode tolerated: partial data, wide uncertainty).
5. **Score Evolution Report**: multi-run comparison with deltas; annotates methodology/coefficient version changes between runs. Requires a two-run fixture.
6. Embedded charts: radar (modules), heatmap, evolution lines, tornado. Chart values deterministic from the run (fixed inputs → identical values).

## Exit criteria

- Every deliverable type generates from fixtures; Score Evolution correctly diffs two finalised runs including a version-change annotation.
- Not Assessed cells visually distinct in the heatmap (rendering test on document XML).
- Full gate green; CI green.
