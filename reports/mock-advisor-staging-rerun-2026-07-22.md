# Mock-advisor staging rerun — 2026-07-22

Five personas cold-drove the **deployed staging build** (main `4ed1d52`: GRS-0159/0162/0163/0165/0166
live) end-to-end. Same hard rules (no source access, browser-only); briefs steered them to probe
score consistency, the new sell panel, and rating ergonomics. Raw reports: `scratch/reports/stg-*.md`.

## Scores

| Persona (segment) | 07-19 orig | 07-20 full remeasure | **This run** |
|---|---|---|---|
| Priya — LSEG (exchange) | 48 | 72 | **58** |
| Tom — SJP (wealth) | 55 | ~70 | **56** |
| Marcus — Robinhood (retail) | 68 | 82 | **74** |
| Elena — Deutsche Börse (exchange) | 46 | 78 | **58** |
| James — Brewin (wealth) | 68 | ~75 | **58** |
| **Mean** | ~57 | ~75 | **60.8** |

The drop vs the remeasure is NOT regression: this cohort audited **number coherence** forensically
(the briefs pointed there) and found a seam the earlier runs never probed. Retail (Marcus) — where
every recent fix targets — went UP under deliberate abuse.

## What the recent fixes verifiably bought (personas confirmed)

- **Post-finalise consistency (GRS-0166):** locked V identical across rail/summary/portfolio/
  engagement — verified by Marcus (65.5), Elena (64.9), Tom (58.0), James (50.1).
- **Sell-from-report (GRS-0162) is evidence-honest in-segment:** Marcus — recommendations matched
  his actual rated weak modules; Elena — cited gap matched her actual BRANDING rating.
- **Input abuse survival:** double-submit protection, finalise input-locking, branded 404s,
  negative-AUA refusal, dual-rater gate, watermarks/sandbox banners everywhere (Marcus, James).
- **Wizard density (GRS-0165):** infra one-click chips + collapse praised (Priya: "1 click per row
  and modules self-collapse"); the CONTRAST now makes the Powers step feel worse (see #5).
- **Honesty engineering praised across the board:** range-first display, provisional-bottleneck
  caveat, C-skip transparency, AI approval audit trail, client-facing refusal reasons.

## THE finding — one assessment, two estimators (5/5 personas, top severity)

Live surfaces headline the **Monte-Carlo P50**; the scenario baseline, build-up chart, AI
narrative, and (since GRS-0166) every locked surface headline the **deterministic score**. So the
number *changes at the finalise click* with no input change (67.4→69.5, 56.1→58.0, 63.1→64.9,
49.6→50.1), the pre-finalise screen shows up to three V values at once, the locked point sits at
~P85 of its clamped band, and an approved AI narrative quotes B/P/L that contradict the summary
beside it (71.1/41.6/54.2 vs 70.4/37.4/53.2). Every technical persona called this disqualifying.

**Fix (GRS-0167, ADR-0040): the one-number rule.** The quoted point is ALWAYS the deterministic
engine score, on every surface, live or locked; Monte Carlo supplies the range only (labelled
"modelled range", not P50). Scenario baseline, waterfall, narrative and locked surfaces already
quote deterministic — this brings the live rail/summary in line with them, and the finalise click
stops moving the number.

## Confirmed defects → build list

1. **GRS-0167 — one-number rule** (above). HIGH, 5/5.
2. **GRS-0168 — portfolio "Completeness" denominator**: uses the FULL registry (51 subs) for
   profile-scoped assessments → "47%/51%" beside the wizard's "100% of applicable" (4/5).
   Confirmed in source (`list_brokerage_portfolio` → `total_subs` from full registry).
3. **GRS-0169 — sell-from-report segment scoping** (3/5): (a) C fit-targets resolved against the
   FULL registry, so wealth/exchange reports list retail C-modules as "not yet assessed"
   (confirmed in source — the portfolio uses the profile view; opportunities didn't); (b) the
   catalogue is retail-only, so wealth/exchange get Brandfetch-off-a-power pitches ("laughed out
   of the room" — Tom/Elena/James). Per-product profile applicability + honest empty state.
4. **GRS-0144 completion — percent-metric bounds** (Marcus): GROSS_MARGIN / CLIENT_GROWTH_RATE /
   NET_REVENUE_RETENTION lack max bounds → 1,234,567,890% fed B silently. Registry data.
5. **GRS-0170 — Powers step honesty + ergonomics** (3/5): unrated powers RENDER as "None" (a real
   rating — the exact conflation D9 exists to prevent), no un-rate affordance, 4-6 dropdowns per
   power vs the infra chips.
6. **GRS-0171 — finalise confirmation** (4/5): one-click irreversible lock, no dialog, no
   statement of what the solo/sandbox path skipped.
7. **GRS-0172 — trust-polish sweep** (assorted, 1-3 votes each): LockedScore "P10–P90MEDIUM"
   spacing run-on; stale 409 banner on pipeline; ΔV "(score points ×100)" mislabel; duplicate
   deliverable generation unwarned + Audience column "—"; bad-id deep-link bounces silently;
   whitespace-blocked but emoji-accepted prospect names; engagement disabled-button hints +
   lead-with-Link when a linkable assessment exists; module table missing min-term footnote
   (Σκ·q_m ≠ L unexplained); commission rate rounding 3.8% vs 3.75%.

## Founder-gated (flagged, not buildable here)

- **Wealth/exchange §4 rubric anchors unauthored** — James's #1: "without anchors my ratings are
  opinion"; guts defensibility for the segments the weights were just activated for.
- **C taxonomy for wealth/exchange** (all 5, both segments) — "measured everything except what
  we're best at."
- **Sales Egoist branding + incentive-first earnings nudges** (James, repeat finding) — the
  "CLOSE THIS NEXT: Sell Benzinga £15,000" strip has no disclosure language.
- **Segment product shelf** (wealth/exchange vendors), **peer benchmarking** (all 5), **regulatory
  overlays** (PFMI/DORA for exchange; FCA sourcebook annex for wealth), **B saturation
  methodology** (100.0 from 2 metrics), **currency/locale** (GBP-only, US dates), **registry
  coverage** of major venues/wealth firms.

## Verdict

The honesty spine holds under hostile audit — what fails is estimator coherence (one fix away) and
segment depth (founder-scoped). Retail is demo-ready by this cohort's own behaviour; wealth and
exchange demos should lead with the taxonomy and NOT open the sell panel until GRS-0169 lands.
