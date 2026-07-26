# Elena Rossi (Deutsche Börse/exchange) — RE-RUN. Confidence 52/100 (was 46, +6)

**CONFIRMED FIXES:** unassessed modules EXCLUDED from weakest-first (no phantom ~50) — GRS-0146; bottleneck "PROVISIONAL" + low-coverage warning — GRS-0145; negative metric fail-loud with full score suppression — GRS-0144; monotonicity clean both directions; perfect reproducibility (seeded MC). "A real improvement over the 'confident 50 for a module you never touched' behaviour."

NEW/deeper methodology findings (she dug deeper now surface is fixed):
1. **Cross-pillar coupling (HIGH)** — setting an Infra subcomponent N/A shifted P (Power) 42.9→41.4; restoring → exactly 42.9. VERIFY: real deterministic bug vs MC RNG-stream artifact (changing input count shifts RNG draw order → power band p50 moves).
2. **Uncertainty range ignores coverage (HIGH)** — ±5 at 14% coverage; band tracks evidence-grade dispersion of rated items, not the 86% unmeasured. This is the KNOWN remaining half of GRS-0146 (make coverage widen the band) — methodology/founder-gated.
3. Retail rubric on exchange, self-flagged "not client-usable" (HIGH, segment — exchange metric set not built).
4. Single-metric B; AUA=1 accepted (min_raw:0 allows it); zero-width B range, no coverage caveat (MED-HIGH).
5. "of applicable" denominator doesn't drop on N/A; loose "weakest link" on tied-high modules (LOW).
