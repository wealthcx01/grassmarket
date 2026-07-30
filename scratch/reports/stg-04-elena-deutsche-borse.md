# Elena Rossi — cold stress-test report

Persona: quantitative analyst / market-structure consultant. Customer lens: Deutsche Börse (exchange / market infrastructure). Environment: staging, full cold run through the exchange journey with a forensic number audit.

## 1. Task matrix
| Task attempted | Outcome (done / partial / blocked) | Notes |
|---|---|---|
| Dashboard onboarding read | done | Clear 4-step getting-started; primer offered; flow legible |
| Pipeline: add Deutsche Börse, open detail | done | Win-probability explained (10% base, "Cold", sharpening factors listed) |
| Move prospect through stages to Contracted | done | Illegal jumps rejected loudly ("Illegal pipeline transition prospect → contracted; legal moves are…") — had to walk the legal path; 90% at Contracted |
| Create assessment, EXCHANGE operating model, sandbox | done | Exchange-native modules (Matching Engine, Clearing & Settlement, Member Connectivity…); `/assessments/new` throws a visible 422 before recovering |
| Business metrics with confidence grades | done | 8+ exchange metrics (ADV, open interest, listings, index/market-data revenue, take rate…), per-metric confidence (audited/management/self/estimated) + source/as-of field; autosave |
| Rate 7 Powers with Benefit/Barrier + E1–E4 evidence grades | done | Weaker-side rule stated up front; per-power "How to assess" |
| Rate 24/24 infrastructure subcomponents | done | Rubric Guidance per row; ★ critical gating explained; live V appeared |
| Audit the numbers across surfaces | done | **Found real discrepancies — see below** |
| Scenarios / Upgrade Priority Index | done | Ranked ΔV works; but its baseline V contradicts the live rail |
| Finalise via sandbox | done | One click, no confirmation dialog; **headline V changed on finalisation** |
| Recheck every surface for locked score | done | Rails/portfolio/engagement consistent at 64.9/65 post-lock — but locked ≠ live score |
| Deliverables: link assessment, generate reports | done | Linked; 3 internal drafts generated; .docx content not inspected (download-only) |
| Client-facing audience gate test | partial | Radio present; my driver misfired the click; all outputs emerged internal-draft with sandbox banner — gate not conclusively exercised |
| Recommended-to-sell vs my actual ratings | done | Cited gap "BRANDING · ESTABLISHED/EMERGING" **matches my actual rating** — honest; but products/taxonomy are retail, not exchange |
| Earnings arithmetic | done | All rates recompute cleanly against a £100k illustrative deal |
| Academy lesson + comprehension check | done | Sales Egoist L1; check-yourself + model answer + mark-complete works |

## 2. Friction & distrust log
- **The headline V changed at finalisation with zero input change: live 63.1 → locked 64.9.** For an assessor who has been quoting "63, range 60–66" all afternoon, the lock button silently adds +1.8. Nothing on screen explains that the live number is a Monte-Carlo P50 and the locked number is (apparently) the deterministic engine score. Severity: **high** — this is the number the client sees.
- **Three different V values are visible for the same inputs before finalising:** 63.1 (rail + summary headline, P50), 63.2 ("How Platform Value builds up" chart: 0.30×61.2 + 0.37×59.5 + 0.33×69.1 = 63.18), and 64.9 (Scenarios "Baseline V 64.9 → 65.4"). I verified 63.1 is the geometric mean of B/P/L (63.13) while the chart claims an additive build-up — two decompositions, no reconciliation note. Severity: **high**.
- **The locked point is not the centre of its own band.** Post-finalise display reads "64.9 (60.3–65.7) P10–P90" — the band was computed around P50 63.1, so the quoted point sits at roughly the 85th percentile of its own distribution, and the "P50" label was silently dropped. The narrative even rewrote itself from "sits at 63" to "sits at 65" against the same 60–66 range. Statistically incoherent as displayed. Severity: **high**.
- **L is not reproducible from the displayed weights.** The Module breakdown table publishes κ weights and q_m per module ("x is the module's weight share in the L blend"), but Σκ·q_m = 73.2 vs displayed L = 69.1. Presumably a bottleneck term — it is not disclosed, so the one table that invites recomputation fails recomputation by ~4 points. Severity: **med-high**.
- **"Coverage" means two different things on two surfaces.** Summary: "Coverage: 24/24 subcomponents (100% of applicable)". Engagement card + portfolio row: "Coverage 47%" / "Completeness 47%" on the same finalised assessment. A reviewer sees a finalised report claiming both 100% and 47% coverage. Severity: **med**.
- **Scenario ΔV label vs value scale.** "Ranked by ΔV (score points ×100)" yet ΔV 0.46 corresponds to the displayed 64.9→65.4 (= 0.5 points). The value is in points; the "×100" annotation is wrong or meaningless. Severity: **low-med**.
- **Finalise & lock is a single un-confirmed click** for an irreversible action (sandbox at least). Severity: **med**.
- Module scores themselves ARE reproducible (a genuine positive): with Developing=50 / Advanced=80 / Frontier=95 anchors, every module matched mean-capped-at-(min+15) exactly (65/65/65/65/80/80/85/85). The critical-bottleneck story told in the UI is the story in the numbers. This is what earned back some trust.
- Bands are labelled (P50, P10–P90), asymmetric in the right direction (P 59.5 with 52.7–62.6 — long left tail, consistent with weaker-side logic), and the live point sits inside its band. Good.
- Deliverables table: Audience column shows "—" on every row; three identical drafts can be generated with no dedupe warning. Severity: **low**.
- Drawer stage-history is stale (shows only "Created in Prospect" after five moves) while the full record shows the complete history. Severity: **low**.
- `/assessments/new` produces a visible HTTP 422 + console error before bouncing to the list. Severity: **low**.
- Earnings: engagement panel shows "Yr-1 3.8%" for a product the Earnings schedule lists at 3.75%. Rounding on a commission rate is exactly the kind of thing an advisor gets challenged on. Severity: **low**.
- I could not verify the deliverable .docx contents (download only, no in-browser preview of the numbers inside) — so whether the report quotes 63.1, 63.2 or 64.9 is untestable from the UI. That opacity is itself friction for a reviewer. Severity: **med**.

## 3. Missing features (for my segment: exchange)
- **No exchange-relevant represented products.** Recommended-to-sell offers Brandfetch (a logo API) / Benzinga / OpenBB — retail-brokerage catalogue — to a market-infrastructure operator, and cites "UI & Navigation", a retail taxonomy module that does not exist in the exchange deep dive. The gap-evidence honesty is right; the catalogue is not.
- **Customer-Proposition Index (C) is unauthored for exchanges.** The skip is transparently explained (genuinely good), but a member/participant-experience construct (connectivity onboarding, conformance cycles, protocol docs, incident comms) is exactly what an exchange client would ask about.
- **No peer benchmarking.** An exchange buyer's first question is "versus Euronext/ICE/Nasdaq?". Scores float with no venue reference class, and the metric fields have no benchmark ranges.
- **No regulatory dimension.** DORA operational-resilience, MiFID II RTS 7/8/9 system-capacity, CSDR settlement discipline — the deep dive covers surveillance/reporting rows, but nothing frames results against the regimes an exchange is audited under.
- Latency figures are qualitative only (Basic→Frontier); a venue assessment without microsecond-class quantitative capture fields will read as soft to an exchange CTO.
- No dual-datacentre / capacity-event scenario modelling in Scenarios — the only scenario type is "raise one subcomponent one level".

## 4. Customer-side reaction (Deutsche Börse)
- Group Strategy would recognise the taxonomy as genuinely exchange-native — Matching Engine, latency determinism, data-fairness/latency equalisation, clearing risk & margin, listings franchise, index/market-data revenue. That is rare and would earn a hearing.
- The uncertainty discipline ("quote the range, the point alone loses a technical audience") is precisely the correct register for this buyer — and then the buyer's analyst recomputes the build-up chart, finds 63.2 vs 63.1 vs a locked 64.9, and the meeting becomes about the arithmetic instead of the platform. For an organisation that clears trillions and runs on reconciliations, one unexplained reconciliation break disqualifies the report.
- The recommended remediation (a brand-asset API at 7.5% commission) would be received somewhere between puzzling and insulting for a €50bn market-infrastructure group; it exposes that the sell-side catalogue was built for retail brokers.
- The bottleneck finding itself (market-data dissemination / data-fairness lagging an otherwise Frontier-class core) is a credible, defensible conversation for this company — the engine found the right thing with honest inputs.
- The C-skip note ("we won't score you on questions that don't fit") would actually build trust — it reads as methodological integrity rather than absence.

## 5. Confidence score & Top-5 issues
Confidence: 58 / 100 — the exchange journey is complete end-to-end and the module math is exactly reproducible, but the platform shows three different headline V values for one set of inputs and changes the score at lock, which a quantitative buyer treats as disqualifying until explained.

Top 5 issues (ranked):
1. **Locked score ≠ live score (63.1 → 64.9, +1.8 at finalisation, no input change)** — high; assessment summary + every downstream surface. Fix: lock the same estimator shown live, or display both explicitly ("deterministic 64.9 · MC P50 63.1") before and after lock — never swap silently.
2. **Point/band incoherence after lock** — high; "64.9 (60.3–65.7) P10–P90" quotes a point at ~P85 of its own band with the P50 label silently dropped (plus a "P10–P90MEDIUM" text run-on). Fix: re-centre or re-label; a point quoted against a band must state which quantile it is.
3. **The two decompositions don't reconcile with the headline or each other** — high; build-up chart sums to 63.2 vs headline 63.1 (additive vs geometric story), and Σκ·q_m = 73.2 vs L = 69.1 with the bottleneck term undisclosed. Fix: one footnote per panel giving the exact formula, so every displayed table recomputes.
4. **"Coverage 47%" vs "Coverage 24/24 (100%)"** — medium; portfolio row + engagement card vs summary. Fix: rename the portfolio metric (it appears to count optional fields) and never reuse the word "coverage" for two denominators.
5. **Exchange sell-side gap: retail product catalogue + retail taxonomy leak ("UI & Navigation") on an exchange report** — medium; recommended-to-sell panel. Fix: segment-scope the catalogue and the gap-matcher; suppress the panel for segments with no matched products rather than showing a logo API to an exchange.
