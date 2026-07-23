# GRS-0144b — Refuse-only bounds for every percent/bps metric (GRS-0144 completion)

**Status:** Done (2026-07-23). Staging-rerun finding (Marcus): a 1,234,567,890% gross margin was
accepted silently and fed B=82.0 — negative AUA refused loudly, so the machinery existed but
percent metrics had no upper bounds. **Loop:** rerun remediation.

## Fix

Registry DATA only (the ADR-0035 Phase-1 machinery is unchanged): all 14 percent/bps metrics
across the base + wealth + exchange registries now carry refuse-only `min_raw`/`max_raw` — bounds
that reject only values that cannot exist (a >100% gross margin, a <−100% growth rate), while
legitimately extreme real values (negative margins, outflow years, >100% NRR) stay in-domain.

Tests: the Marcus value refuses; negatives/extremes stay valid; every percent/bps metric in every
profile view asserts an upper bound. Golden master untouched.
