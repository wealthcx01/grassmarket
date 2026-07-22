# Mock-advisor FULL re-measure — before/after (2026-07-20)

All 5 personas re-drove the **complete** rebuilt stack cold: input validation, scoring-integrity
(no phantom bottleneck), routing/not-found, sandbox discovery, bottleneck-honesty caveat, the full
**wealth AND exchange** operating models (segment-native metrics + infrastructure taxonomies),
profile-aware gate copy, graceful guidance, power-name casing, and self-service change-password.
Raw reports in `scratch/reports/full2-*.md`.

## The numbers

| Persona (segment) | Original | Re-run 1 (partial) | **Full re-measure** | Δ vs original |
|---|---|---|---|---|
| Priya — LSEG (exchange) | 48 | 58 | **72** | **+24** |
| Elena — Deutsche Börse (exchange) | 46 | 52 | **78** | **+32** |
| Marcus — Robinhood (retail) | 68 | 72 | **82** | **+14** |
| Tom — St. James's Place (wealth) | 55 | 46 | **63** | **+8** |
| James — Brewin Dolphin (wealth) | 68 | 58 | **72** | **+4** |
| **Mean** | **57.0** | **57.2** | **73.4** | **+16.4** |

**Mean confidence 57.0 → 73.4 (+16.4).** Every persona is up vs their original; the exchange personas
(Elena +32, Priya +24) moved most, because the exchange taxonomy *and* the scoring-integrity fix both
landed for the quant lens.

## What the personas confirmed working (their words)

- **Segment fit (the biggest lever) — both models land.** Priya: "the exchange re-skin is real and
  well-executed across BOTH Business Metrics and Infrastructure Deep Dive; the prior 'retail OEMS for
  an exchange' defect is gone." James: "a wealth firm described by someone who knows wealth — the
  critical markers sit exactly where a regulator would put them (CASS, suitability, resilience)." Tom:
  "SJP now sees its own language." Elena: "reads like it was written by someone who understands a
  venue, not a retail app."
- **Scoring integrity (GRS-0146).** Elena: the bottleneck at low coverage is now honest — "unassessed
  modules excluded from the ranking… 'PROVISIONAL · Only X% assessed'. Confirmed on both retail and
  exchange." No phantom ~50 modules.
- **Input validation (GRS-0144).** All confirmed the fail-loud negative-metric gate ("can't be below 0").
- **Routing + change-password + casing + guidance + gate copy.** Marcus: "noticeably hardened…
  remaining issues are polish, not breakage." James verified all four of his prior blockers fixed.

## The one universal ceiling
**"Indicative, not client-usable"** — flagged HIGH by all 4 non-retail personas. The wealth/exchange
weights & criticals are still draft, so no non-retail assessment can produce a client-grade score.
This is **Phase-4 elicitation** (founder/panel-gated, non-negotiable #2) — the single lever that would
move ~73 toward 95.

## Real bugs / clean follow-ups the full run surfaced
1. **Internal-draft deliverable generation fails for a wealth assessment** (Tom, HIGH) — `POST
   /engagements/.../deliverables` (Internal draft) → network error / "Cannot reach API"; the
   client-facing branch returns a clean 409, so the docx-generation path specifically breaks on a
   wealth assessment (likely the deliverable builder assuming retail module/subcomponent keys).
   **The top new defect — investigate + fix.**
2. **C-index / Customer-Proposition tab still retail** (Elena; Tom prior round) — "time-to-first-trade,
   KYC friction" in an exchange/wealth assessment. The C dimension (ADR-0023) wasn't touched by the
   L/B taxonomy work; extend the same mechanism to C.
3. **Rubric §4 anchors unauthored for wealth/exchange** (James, Tom) — graceful "not yet authored" is
   correct, but content-empty; author anchors or soften the tab copy.
4. **"Nine modules" copy vs 7 (wealth) / 8 (exchange) shown** (James) — a generic hardcoded string;
   make the count profile-aware.
5. **Operating-model defaults to Retail and resets when Sandbox is ticked** (Priya) — a UX trap for
   non-retail clients; force a choice and stop the reset.
6. Sandbox/finalised deliverable not viewable (Priya, James, Tom); duplicate prospects (Marcus);
   portfolio rows not clickable + no coverage badge; P10/P50/P90 labels hidden (Elena).

## Bottom line
The remediation program moved the mean **+16.4 (57 → 73)**, and the personas' own words confirm the
segment models, scoring integrity, and finish/trust fixes all landed. Reaching **95** now needs: (a)
the **Phase-4 elicitation** (founder-gated — the ceiling for 4 of 5), plus (b) the buildable follow-ups
above, led by the wealth deliverable-generation bug and the C-index taxonomy.
