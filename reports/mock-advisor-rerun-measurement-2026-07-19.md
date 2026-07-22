# Mock-advisor re-run — before/after measurement (2026-07-19)

The same 5 personas re-drove the **rebuilt production stack** (all remediation PRs merged: GRS-0142/
0143/0145/0146/0149 + ADR-0035 Phases 1–3 = input validation, per-profile metrics, wealth model)
cold, to measure the confidence lift. Raw re-run reports in `scratch/reports/rerun-*.md`.

## The numbers

| Persona (segment) | Before | After | Δ |
|---|---|---|---|
| Priya — LSEG (exchange) | 48 | **58** | **+10** |
| Elena — Deutsche Börse (exchange) | 46 | **52** | **+6** |
| Marcus — Robinhood (retail) | 68 | **72** | **+4** |
| Tom — St. James's Place (wealth) | 55 | **46** | **−9** |
| James — Brewin Dolphin (wealth) | 68 | **58** | **−10** |
| **Mean** | **57.0** | **57.2** | **+0.2** |

**The mean is essentially flat — well short of the 95 target.** But the split is the finding.

## What worked (confirmed live by the personas)

The integrity / robustness / UX fixes landed and were explicitly noticed — they lifted the **exchange
and retail** personas:
- **GRS-0146** (no phantom bottleneck): Elena — "unassessed modules excluded from the weakest-first
  list rather than shown at ~50 … a real improvement over the 'confident 50 for a module you never
  touched' behaviour."
- **GRS-0144** (input validation): all three of Priya/Marcus/Elena hit "Assets Under Administration
  can't be below 0 GBP" — fail-loud, no silent clamp.
- **GRS-0145** (low-coverage caveat): bottleneck now labelled "PROVISIONAL."
- **GRS-0143 / 0149** (routing + sandbox discoverability): dead routes redirect; "Preview in sandbox"
  is found.

## What backfired — the key lesson

**Shipping the wealth model metric-deep only made the wealth personas MORE critical, not less** (Tom
−9, James −10). Both *praised* the wealth metrics (AUM, adviser headcount, bps margin, the
Consumer-Duty fair-value ceiling — "exactly the language an FCA wealth manager lives in"). But:
- The **infrastructure + customer-proposition modules — the bulk of the 49 scored subcomponents —
  are still retail-broker** (OEMS, App Server, time-to-first-trade, watchlists). Root cause: the
  wealth profile *adds* 6 wealth subcomponents but doesn't *remove* the retail ones from its selected
  modules, so it reads as "a retail template with a wealth cover sheet."
- The wealth score self-declares **"indicative, not client-usable"** (Phase-4 elicitation, founder-
  gated), so the headline workflow can't finish for the segment.
- The **sandbox-promised watermarked deliverable is not reachable** (3 personas) — finalising in
  sandbox doesn't surface a viewable/downloadable report.

A *partial* segment model scores worse than *no* segment model for that segment's persona, because it
raises expectations then breaks them. **The takeaway for 95: segment models must ship complete —
metrics + infra taxonomy + client-usable elicitation — or not at all.**

## The path to 95 (ranked)

**Founder-gated (the real ceiling for wealth/exchange personas — 4 of 5):**
1. **Complete the wealth + exchange models**: author segment-native *infrastructure & customer-
   proposition* taxonomies (drop retail subs on the selected modules; add custody/portfolio-mgmt/
   adviser-desktop/reporting for wealth; matching-engine/market-data/clearing for exchange). The
   per-profile-metric mechanism (GRS-0147b) already proves the pattern; this extends it to modules.
2. **Phase-4 elicitation** — run the weight/critical panels so non-retail profiles flip
   `client_usable`, retiring the "not client-usable" banner (per non-negotiable #2, ADR-0035 Phase 4).

**Buildable now (clean, surfaced by the re-run):**
3. **Sandbox → visible deliverable** (3 personas): surface/link the watermarked report from a
   finalised sandbox assessment, or stop promising it in the copy.
4. **Power-name casing** (James, Marcus): the Overview live-score panel renders raw snake_case
   (`BRANDING, CORNERED_RESOURCE…`) and the Summary shows "BRANDING" all-caps — one humanised label
   map. *(Never fixed; flagged in the first run too.)*
5. **GRS-0143b** (shipped, PR #163): `/engagements|/workshops/<bad-id>` no longer leak raw "422".
6. **Change-password + real Profile/Settings** (ADR-0036 Item 2 — Tom/Marcus/James): the compliance
   persona weights this heavily.
7. Metric upper-bound plausibility (AUA 10^15 accepted); silent duplicate-prospect warning.

**Methodology (uncertainty layer — Elena, the quant):**
8. **Coverage-aware uncertainty band** — the P10/P90 width still tracks evidence-grade dispersion of
   the *rated* items, not coverage, so 14% coverage still shows ±5 (the known remaining half of
   GRS-0146). Founder-gated (methodology-version bump).
9. **Per-pillar RNG-stream isolation** — verified the deterministic P is independent of infra (Δ=0),
   but changing the assessed-input count shifts the shared Monte-Carlo RNG stream, so the P *band's*
   p50 wobbles ~1.5pts — cosmetic, but a quant notices ("cross-pillar coupling").

## Honest bottom line
The remediation program fixed what it targeted (integrity, validation, routing, solo-path discovery)
and those gains are real and confirmed. The mean didn't move because the wealth model was shipped
half-complete, which cost the two wealth personas more than the fixes gained elsewhere. Reaching 95 is
now a well-scoped but larger effort dominated by **completing the segment models (infra + elicitation)
— which is founder/panel-gated content work, not autonomously self-mergeable** — plus the buildable
polish above.
