# Priya Nair — cold stress-test report

Ex-GS equities VP, LSEG (exchange) lens. Staging build, priya.nair@bruntsfieldcapital.com, 2026-07-22. ~14 driver runs, full journey: pipeline → exchange assessment → finalise (sandbox) → deliverable → engagement → earnings → Academy.

## 1. Task matrix
| Task attempted | Outcome (done / partial / blocked) | Notes |
|---|---|---|
| Dashboard first-run orientation | done | 4-step getting-started overlay, clear "what to do first"; nav matches the promised flow. |
| Add LSEG as prospect | done | Instant, board updates, expected-wins counter moves. |
| Read win-probability explanation | done | Rule-based, shows WHY (stage base %) + "would sharpen the estimate" checklist. Honest but purely stage-driven. |
| Edit prospect sector field | blocked (silent) | Typed sector into the detail panel; "No sector recorded" still shown at every later visit. No save affordance, no error. |
| Move stages to Contracted | done | Illegal transitions rejected with the legal moves listed (workshop_scheduled → qualified refused, 409). Guard is defensible and explained, but you cannot skip stages even for an inbound signed client. |
| Create assessment, EXCHANGE model | done | "Exchange / market infrastructure" offered. LSEG not in the company registry — saved as unlinked manual subject. |
| Business metrics entry | done | Exchange-native metrics (ADV, open interest, listings won, index & data revenue, take rate, recurring share) with per-metric confidence grading (audited → estimated) and explicit "Not assessed". Autosave visible ("Saving… / All changes saved"). |
| Rate 7 Powers (benefit/barrier + evidence grade) | done | Correct Helmer min(benefit, barrier) framing, E1–E4 evidence grading feeding uncertainty. Ergonomics poor — see friction log. |
| Infrastructure deep dive (24 subcomponents) | done | 8 genuinely exchange-native modules; one-click chips; modules collapse when complete; ★ critical gating explained. |
| Customer Proposition | n/a by design | Honestly skipped for exchange: "taxonomy has not been authored yet… does not affect your V". Right call, still a segment gap. |
| Live score rail | done | V appeared at 24/24 with P50 + P10–P90 + uncertainty word. But see the three-different-V problem. |
| Scenarios / Upgrade Priority Index | partial | ΔV ranking works and a no-op upgrade correctly shows ΔV 0.00 — but my scenario vanished on navigation (not persisted), and the panel's "Baseline V 69.5" disagreed with the rail's 67.4 on the same screen. |
| Finalise solo (sandbox) | done | One click, no confirmation dialog, locks instantly. Dual-rater/consensus gate correctly bypassed only in sandbox. |
| Deliverable preview (.docx) | done | "Generating…" then completes, watermarked internal-only. Content not inspected (binary). |
| Portfolio consistency after finalise | partial | Portfolio quotes the locked 69.5 (consistent) — next to "Completeness 47%" for an assessment the wizard calls "24/24, 100% of applicable". |
| Engagement → link assessment → generate client deliverable | blocked (silent) | Created engagement from contracted prospect fine. Linking my finalised (sandbox) assessment: Link click does nothing — no error, no hint. Generate also a silent no-op. If sandbox assessments are unlinkable by design, the UI never says so and still lists it in the dropdown. |
| Earnings | done | Clean empty state, live product commission schedule, downloadable statement. "CLOSE THIS NEXT: Sell Benzinga £15,000" nudge — see §2/§4. |
| Academy lesson + comprehension check | partial | Course reader is good; check-yourself (free recall + model answer reveal) works. But after completing a full check the course still reads 0/8 lessons, 0% — no visible way to complete a lesson, while Workbench nags "finish it to certify". |

## 2. Friction & distrust log
- **Three different V numbers before finalise, and the locked score is not the one you watched.** Live rail: 67.4 (P50). "How Platform Value builds up" chart on the same summary page: 18.7+24.1+25.1 = 67.9. Scenario panel: "Baseline V 69.5". On finalise the headline becomes 69.5 — a 2.1-point jump from the number displayed all session, with zero explanation of which V is which (MC median vs deterministic, presumably — but I shouldn't have to presume). If I'd told the client "67" on Tuesday and the locked report says "69.5" on Wednesday, that's my credibility, not the tool's. **Severity: high.**
- **Point estimates sitting at the edge of their own uncertainty bands.** P — Power: 65.0 with range (58.8–65.0); finalised V: 69.5 with range (64.9–69.6). A point at its own P90 looks like a bug even if it's an artefact of min() capping; any quant reviewer stops trusting the bands on sight. No explanation offered. **Severity: high.**
- **"Completeness 47%" on a locked assessment the wizard itself calls 100% covered.** The two claims sit one click apart. Presumably 47% counts unfilled rationale boxes/profile fields — but "Finalised · locked · 47%" reads as "half-done and signed off". **Severity: medium-high.**
- **Silent no-ops everywhere at the edges.** (a) Engagement "Link" with a sandbox assessment — nothing happens, no message; (b) "Generate" deliverable unlinked — nothing; (c) scenario built then lost on tab navigation despite the wizard's "autosaves" promise; (d) prospect sector field typed and never saved. Every one of these is a fail-quiet, which is exactly what the product's own copy promises never to do about scoring. **Severity: high (pattern), medium (each).**
- **Finalise & lock is one click with no confirmation.** For an action whose whole point is irreversibility, no "are you sure", no summary of what locks. **Severity: medium.**
- **Powers rating ergonomics are a slog.** Per power: 2 rating dropdowns + 2 grade dropdowns + 2 free-text rationale boxes = 4–6 pointer interactions × 7 powers, no keyboard-first flow, no chip buttons (the infra tab proves they can do chips — 1 click per row and modules self-collapse; the contrast makes Powers feel worse). Powers cards don't collapse. **Severity: medium.**
- **Academy progress opaque.** Did the comprehension check, revealed model answer — 0/8 forever. Workbench says "finish it to certify" with no legible definition of "finish". **Severity: medium.**
- **Win probability never uses the sharpeners.** The panel lists "no contact / no sector / no notes" as things that would sharpen the estimate, but the estimate is a flat stage base (10/25/70/90%). Honest labelling, thin model — expected-wins ("0.9") on my board is really just a stage lookup. **Severity: low-med.**
- **LSEG not in the company registry.** The flagship UK market-infrastructure group, on a platform with a dedicated exchange operating model, is an unlinked manual subject. **Severity: low, but telling.**
- Cosmetic: maturity-radar spoke labels clipped at the viewport edge ("tching Engine", "ectivity"). **Severity: low.**

## 3. Missing features (for my segment: exchange)
- **No member/participant proposition index.** C is honestly skipped, but for an exchange the member-experience construct (onboarding of members, conformance testing cycle time, API developer experience, data licensing friction) is assessable today and is what LSEG's COO would ask about first.
- **No peer benchmarking.** A 69.5 means nothing to an exchange without "versus Euronext / Deutsche Börse / ICE / Nasdaq" context — even a coarse quartile band per module would transform the deliverable.
- **No regulatory-alignment overlay.** CPMI-IOSCO PFMI, DORA / UK operational-resilience, MiFIR RTS — the taxonomy touches these (reg reporting, resilience) but nothing maps module scores to the compliance frameworks an FMI board actually reports against.
- **Product shelf is 100% retail-data tools** (Benzinga, Brandfetch, OpenBB, ConnectTrade). There is literally nothing on the shelf an exchange-segment advisor could plausibly sell to an exchange; the earnings engine and Academy product courses are dead weight for this segment.
- **Registry coverage of major venues** (LSEG, Euronext, DB1, ICE, CME, Nasdaq) so exchange assessments link to real entities.
- **Scenario programs.** Single-subcomponent, single-step scenarios only, and they don't persist. Real modernisation cases are multi-year, multi-module bundles.

## 4. Customer-side reaction (LSEG)
- **The taxonomy would earn respect.** Matching engine determinism, latency equalisation/data fairness, drop-copy, conformance certification, colocation, cover-2 clearing risk, MiFIR/RTS reporting — this is real FMI vocabulary, not a retail template with the labels swapped. The bottleneck framing (Trading Ops & Controls capped the whole at 65 because I marked incident response Developing) matches how LSEG actually thinks post-incident.
- **The uncertainty discipline would land well — until the numbers disagree.** "Quote the range, not the point" is exactly the right posture for a technical audience. Then their strategy team recomputes the build-up chart, gets 67.9 vs the locked 69.5 vs the watched 67.4, notices two point-estimates pinned to their own P90, and the whole quantitative apparatus is discounted to theatre. Exchanges employ people whose day job is exactly this arithmetic.
- **The commercial layer must never reach them.** "CLOSE THIS NEXT: Sell Benzinga and earn £15,000" is advisor-side and labelled illustrative — fine internally — but it is ranked purely by commission, is segment-blind, and if an LSEG stakeholder ever glimpsed it the perceived conflict of interest (assessment as a wedge for commissioned product sales) would end the engagement. Nothing post-finalise recommends by client fit; recommendations exist only on the earnings page, ranked by what pays the advisor most. Honest placement, wrong ranking principle.
- **They would ask who rated it.** The dual-rater/consensus machinery visible in Summary is genuinely reassuring governance — and the sandbox path that bypasses it is clearly watermarked. That part is done right.

## 5. Confidence score & Top-5 issues
Confidence: 58 / 100 — the exchange assessment engine is credible and unusually honest by design, but score-consistency defects and silent-failure edges are exactly the flaws a Goldman-trained reviewer (or an LSEG quant) finds in the first hour.

Top 5 issues (ranked):
1. **One assessment, three V values, and a score jump at finalisation** — high; assessment summary/scenarios/finalise. Reconcile deterministic vs Monte-Carlo V into one quoted number (or label both explicitly everywhere: "V(MC-P50) 67.4 · V(det) 69.5"), and never let the locked number differ from the watched number without an on-screen explanation.
2. **Point estimates at the boundary of their own P10–P90 bands** (P 65.0 of 58.8–65.0; V 69.5 of 64.9–69.6) — high; live score rail + finalised header. Either explain the asymmetry inline (min-capping) or fix the band computation; a point at P90 reads as broken.
3. **Silent no-op pattern at workflow edges** — high; engagement Link/Generate with sandbox assessment, scenario non-persistence, prospect sector field. Every dead click needs feedback ("Sandbox assessments can't be linked to engagements — finalise a production assessment"), and scenarios need the same autosave the rest of the wizard has.
4. **"Completeness 47%" vs "Coverage 100% of applicable" contradiction on a finalised assessment** — medium-high; portfolio table. Define completeness, exclude non-applicable sections (C for exchange), or show the same coverage number the wizard shows.
5. **Powers-step input ergonomics** — medium; wizard step 3. Replace the four dropdowns per power with the chip pattern the infrastructure tab already uses, add keyboard flow and per-card collapse; at 7 powers × 2 sides this is the highest-friction screen in the product's core loop.
