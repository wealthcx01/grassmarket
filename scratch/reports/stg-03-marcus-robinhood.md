# Marcus Bell — cold stress-test report

## 1. Task matrix
| Task attempted | Outcome (done / partial / blocked) | Notes |
|---|---|---|
| Dashboard onboarding read | done | 4-step getting-started overlay, clear flow map, skippable. |
| Add prospect (Robinhood) | done | Instant, card appears with 10% win probability + explanation. |
| Add whitespace-only prospect | done (blocked, correctly) | Submit button stays disabled for "   ". |
| Add emoji-only prospect (🚀🚀🚀) | done (accepted — bug) | "🚀🚀🚀" created as a real prospect, no validation, then polluted my conversion stats. |
| Rapid double-submit prospect | done (survived) | Button disables while in flight; no duplicate created. |
| Illegal stage jump (Prospect → Delivered) | done (blocked, correctly) | HTTP 409 + explicit message listing the only legal moves. Error banner never clears though. |
| Legal jump Prospect → Closed | done | Accepted in one move — and Workbench then showed "Pipeline conversion 50%" off my joke prospect. |
| Create assessment, RETAIL model | done | Typeahead tagged Robinhood "BROKER"; retail model default. |
| Hostile metrics (negative AUA) | done (caught) | Inline red error + sidebar callout "can't be below 0 GBP (got -5e+09)" — but invalid value persists and header says "All changes saved". |
| Hostile metrics (1,234,567,890% gross margin) | done (SILENTLY SWALLOWED) | No error anywhere; B score computed (82.0/100.0) with the absurd percent in place. |
| Rate 7 Powers (Benefit/Barrier + evidence grades) | done | Dropdown selects; "Established" etc. 2 selects per power + optional grades. Un-rating back to "unassessed" not possible from the control; unrated selects *display* "None" which is a real rating word. |
| Rate infrastructure subcomponents | done | 1 click per rating, ★ critical gates explained, "Not assessed" un-rates cleanly, anti-anchoring nudges per module. |
| Watch live score | done | V 60.2 (55.8–63.2) P50/P10–P90, coverage 5/51, uncertainty "Very High", provisional-bottleneck caveat. Genuinely honest. |
| Rate Customer Proposition + C score | done | 10 modules + Level-1 widget checklist (Direct custody & DRS, Gamification — properly retail-aware). C 61.9 live on the rail. |
| Finalise real assessment | blocked (correctly) | 409: "5 subcomponents are solo-rated — each needs a second independent rater… (Methodology §9)". |
| Finalise via sandbox | done | Sandbox assessment banner "NON-PRODUCTION, NOT CLIENT-FACING"; finalised solo, locked, watermarked .docx offered. |
| Score agreement (rail / summary / portfolio) | done | V 65.5 identical everywhere; lock disables all rating inputs (verified). Caveat: portfolio shows C for *unfinalised* assessments but hides V — two display policies in one row. |
| Product recommendations vs my weak areas | done | "RECOMMENDED TO SELL" ranks ConnectTrade against MY Trading Experience 20/BASIC, Brandfetch vs Front End — with "Not yet assessed (no claim made)" caveats. Not generic. |
| Scenarios / Upgrade Priority Index | done | Ranked my actual weak spot: Resilience & DR → Advanced, ΔV 5.07 (65.5 → 70.6), "what to fix first, not what it's worth". |
| Deliverables / engagements path | partial | Engagements empty ("Open one from a contracted prospect") — path legible but untested end-to-end without a contracted deal. Watermarked deliverable download offered on the finalised sandbox. |
| Earnings | done | £0 state legible; product commission schedule "read live… never a typed-in number"; "CLOSE THIS NEXT: Sell Benzinga" nudge is generic/illustrative, unlike the assessment-tied recommender. |
| Academy lesson + comprehension check | done | Recall-first: "Reveal model answer" disabled until you type ("Write your recall attempt first"); emoji answer accepted; model answer revealed. Lesson progress stayed 0/8 — unclear how a lesson counts as complete. |
| Practice arena / drills | partial | Arena scenario opens (retail-brokerage COO persona, line-by-line transcript builder, "Submit for scoring"); did not complete a scored session. Drills: "Nothing due". |
| Malformed URLs / /admin / other IDs | done (survived) | Unknown routes → branded 404 with recovery links; bad/foreign UUIDs → clean API 404 and bounce to portfolio (silent — no "not found" toast). |

## 2. Friction & distrust log
- **Gross Margin of 1,234,567,890% accepted without a murmur — high.** Negative AUA gets a loud, specific refusal, so the machinery exists; percent metrics apparently have no upper bound. The platform then computed B = 82.0/100.0 and a headline V with that value in the data. For a product whose whole pitch is "fail loud, nothing fabricated", one silently swallowed absurd input undermines the promise everywhere else.
- **"All changes saved" while an invalid value is on screen — med.** The header banner says saved, the field says "can't be below 0 GBP". Both are true (it saved the bad value and flagged it) but a rushed advisor reads "saved" as "fine". Also, the sidebar echoes the value as "-5e+09" — scientific notation leaking into a client-adjacent UI.
- **Emoji/garbage prospect names accepted — med.** "🚀🚀🚀" became a full CRM record. Whitespace is blocked, so someone thought about validation and stopped early.
- **Stage semantics + conversion stat gamed in two clicks — med.** Prospect → Closed is a legal one-step move, and my Workbench then reported "Pipeline conversion 50%" off a joke prospect. Also "Closed" vs "Delivered" as separate terminal states is never explained on the board — which one is won?
- **Illegal-transition error banner never clears — low.** The 409 message stayed pinned at the top of the pipeline through subsequent successful actions and reads.
- **Power rating select shows "None" when a power is unrated — med.** "None" is a real rating (zero power) and it's also the face of the untouched control. The engine treats them differently ("unrated is never treated as zero" — good), but the widget visually conflates exactly the two states the methodology is most anxious to keep apart. And once rated, there's no obvious way back to "unassessed" (infra rows have "Not assessed"; powers don't).
- **Failed finalise replaces the live score with "Score unavailable" — low.** Explaining the dual-rater gate is right; wiping the previously displayed V 60.2 panel while doing it looks like the score vanished.
- **Portfolio row shows C (61.9) for an in-progress assessment but hides V ("A score appears once finalised") — med.** Two different publication policies in adjacent columns of the same row; a reviewer will ask why one live number is quotable and the other isn't.
- **B — Business hit 100.0 from just two metrics (AUA + client count) — med.** A saturated perfect score from a two-datapoint entry, labelled only "uncertainty not modelled". Every other lens gets a range and a coverage caveat; B gets false precision at the top of the scale.
- **Bad-ID deep links bounce silently — low.** /assessments/<garbage-uuid> lands you back on the portfolio with no "that record doesn't exist" message; feels like a mystery redirect.
- **Lesson completion opaque — low.** Answered the check, revealed the model answer, progress still 0/8 with no visible "what counts as done".
- What genuinely earned trust: double-submit protection everywhere, real input locking after finalise, one identical V across rail/portfolio/deliverable, uncertainty ranges with plain-English "read the range, not the point" coaching, provisional-bottleneck honesty at low coverage, the dual-rater finalisation gate, and a recommender that cites gap evidence and explicitly declines to claim anything about unassessed modules. This thing mostly survived me, and I hit it hard.

## 3. Missing features (for my segment: retail)
- **USD (or any non-GBP) metrics.** All scale metrics are hard-labelled GBP. My buyer is a US retail broker; entering AUA in GBP is a conversion nobody will do honestly. Currency selection per assessment is table stakes for a retail lens that name-checks Robinhood-style neobrokers in its own copy.
- **Retail activity metrics.** The metric set is AUA/clients/revenue/ARPU/margin/cost-to-serve. An execution-only retail broker lives on trades/day, DAU-MAU, options mix, PFOF revenue share, net deposit flow, churn. The AUA helper text itself admits "for an execution-only broker, trade volume matters more" — then doesn't ask for trade volume.
- **UK-centric wrapper assumptions.** "Tax wrappers (ISA/SIPP/…)" — a US retail assessment needs IRA/Roth/margin-account framing, or at least locale-aware wording.
- **Regulatory/conduct dimension for retail.** Post-2021 retail brokers get judged on gamification conduct, best-execution disclosure, and outage history. Gamification & rewards exists as a *feature* widget (scored as a differentiator); there's no place where it's assessed as a *risk*. An outage-history input under Resilience would speak directly to this buyer.
- **Un-rate affordance for Powers**, matching the infra "Not assessed" button.
- **A visible dual-rater request flow.** The gate told me I need a second rater; nothing on the page told me how to summon one (there's a "Rating requests" tab in the Workbench, but no link from the refusal).

## 4. Customer-side reaction (Robinhood)
- The scoring honesty would land well with their data-literate exec team: ranges instead of points, "only 10% assessed — provisional", evidence grades, and a locked, versioned number that matches everywhere. That's the opposite of consultant theatre, and a Robinhood CTO would notice.
- The C-side is credibly retail: time-to-first-trade, funding ease, fractional, Direct custody & DRS (a literally Robinhood-famous topic), gamification, PFOF-adjacent fee-transparency scoring. Whoever built the checklist has actually watched a neobroker.
- But the first metrics screen would cost credibility: GBP-only AUA, ISA/SIPP wrappers, and no trade-volume/DAU metrics says "built for UK wealth platforms, retail-skinned". Robinhood's team would clock that in a minute.
- The "RECOMMENDED TO SELL" panel is well-firewalled ("advisor-facing, never client-facing", watermarked internal deliverable) — but Robinhood is famously build-not-buy; a pitch that leads with reselling ConnectTrade/Brandfetch would get less traction than the diagnostic itself. The gap evidence, though, is exactly the kind of ammo an internal platform team would use in a planning cycle.
- The one number they'd challenge: B — Business 100.0 "uncertainty not modelled". Their analysts would ask how two inputs produce a perfect sub-score and why the input-validation net let a nine-digit gross margin through. If they find that hole, they'll question every other number.

## 5. Confidence score & Top-5 issues
Confidence: 74 / 100 — the scoring spine (honest ranges, locks, gates, evidence-tied recommendations) survived deliberate abuse impressively, but the input layer has holes (percent validation, emoji records, currency lock) that a hostile due-diligence pass would find in under an hour.

Top 5 issues (ranked):
1. **Percent metric with no range validation silently feeds the score** — high; Business Metrics step (Gross Margin 1,234,567,890% accepted, B computed). Fix: bound percent-unit metrics (0–100 or explicit allowed range) with the same loud inline refusal negative AUA gets.
2. **GBP-only, wealth-flavoured metric set for the retail model** — high; Business Metrics step. Fix: per-assessment currency and a retail metric pack (trade volume, active-trader DAU/MAU, PFOF share, net deposits) — the helper copy already promises this thinking.
3. **B — Business saturates at 100.0 from two inputs with no uncertainty treatment** — med-high; Summary/live score. Fix: coverage-aware shrinkage or at minimum a "based on 2 of 6 metrics" caveat like L gets, before an analyst-audience client sees it.
4. **Unrated Powers display as "None" and can't be returned to unassessed** — med; Powers step. Fix: placeholder text ("rate…") distinct from the None rating + an explicit un-rate option, mirroring the infra rows.
5. **Garbage CRM records and gameable stats** — med; Pipeline/Workbench (emoji prospect accepted; Prospect → Closed in one legal click then counted into "Pipeline conversion 50%"; 409 banner never clears). Fix: minimal name validation, clarify Closed-vs-Delivered semantics, exclude one-step closes from conversion, auto-dismiss stale error banners.
