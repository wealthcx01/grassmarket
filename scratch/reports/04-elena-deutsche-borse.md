# Elena Rossi (Deutsche Börse / exchange) — cold stress-test report (methodology focus)

## HIGH findings (quant audit of the live score)
1. **Unrated infrastructure subcomponents imputed to ~50 and counted in L/V** (HIGH). Rated 7/50 subcomponents; all 9 modules still show scores ~50 (EMS Gateway 49.4, Market Data 49.8, Back Office 50.0, OEMS 50.0, App Server 52.0) feeding L=51.0. Reverse-engineered App Server: one Advanced (~70) among 6 unrated → (70+5×50)/6 ≈ 53. On-screen "unrated is never treated as zero" is kept only by imputing ~50 — a fabricated neutral prior. ~86% of L inputs invented. **Contradicts CLAUDE.md "Not Assessed never contributes" + fail-loud. VERIFY vs engine.**
2. **"Likely constraint / bottleneck" is a non-coverage artifact** (HIGH). EMS Gateway named weakest link with ZERO rated subcomponents — ranks weakest only because unlooked-at. "Fix the weakest critical part" advice sends advisor to the one system nobody assessed.
3. **Uncertainty band too tight for "Very High" / 14% coverage** (HIGH). V=71.4 range only 69.5–73.5 (±2). Imputed 50s carry a narrow assumed band. Coverage should blow the interval out.

## MED findings
4. **Business score from one unbenchmarked metric; undisclosed B benchmark + undisclosed V weights** (MED). AUA 250bn→100, AUA 1→20; no benchmark shown. V=0.30·B+0.40·L+0.30·P inferred but never displayed. Not reproducible from UI.
5. **Inconsistent missing-evidence treatment across engines** (MED). Ungraded Powers → labelled point ("uncertainty not modelled"); ungraded infrastructure → still gets a range. Same situation, two behaviours.
6. **Exchange mis-fit** — retail/wealth metrics only (AUA/ARPU/GBP), profile self-flagged "not client-usable".

Positives: ATLAS math internally consistent where inputs entered; weaker-side rule + P=mean(per-power min) confirmed monotonic; grades→uncertainty behaves as claimed; win-prob base rates transparent + monotonic.

## Confidence: 46/100
Top 5: (1) unrated imputed ~50 & counted; (2) bottleneck = coverage artifact; (3) uncertainty too tight at low coverage; (4) undisclosed benchmark/weights + single-metric B; (5) exchange mis-fit.
