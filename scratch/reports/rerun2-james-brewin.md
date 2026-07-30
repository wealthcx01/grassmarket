# James Okafor (Brewin Dolphin/wealth) — RE-MEASURE after GRS-0147d. Confidence 58/100 (was 58 metrics-only, 68 original)

**GRS-0147d WORKED (both confirm):** "the core wealth-fit problem is genuinely fixed — metrics AND the full infrastructure deep dive now describe a wealth manager." 9 wealth modules named properly; criticals (★) on Suitability (COBS 9A) + Custody (CASS); MiFID II best-ex, MPS, IHT/tax, Consumer-Duty vulnerable-client all present. "A real step up from a retail-brokerage frame." No "coming soon" pages.

Held flat at 58 by NEW real bugs (regressions from the wealth taxonomy):
1. **Rubric Guidance errors on new wealth subs (HIGH)** — clicking Guidance on WEALTH_PRICING_DATA / WEALTH_RISK_PROFILING / WEALTH_ORDER_EXECUTION shows raw "No such subcomponent" error. I added 26 wealth subs with NO rubric anchors → guidance endpoint errors. FIX: graceful "no guidance authored yet" (or author anchors).
2. **Finalised sandbox shows no score/deliverable (HIGH)** — portfolio lists it 59.4 but Summary reads "0/26, not scoreable, inputs locked." Locked finalised document not rendering its score. INVESTIGATE (real vs stale-build artifact).
3. **Power-name casing STILL broken (MED)** — Overview panel raw snake_case (BRANDING, CORNERED_RESOURCE…); Summary "BRANDING" all-caps. Twice-flagged (James+Marcus). Clean fix: route every panel through the Powers-tab formatter.
4. Gate copy "App Server, Back Office, or OEMS" in wealth — FIXED in PR #165 (profile-aware).
5. Portfolio Segment column blank (LOW). Peer benchmarking / evidence provenance in outputs (missing).
