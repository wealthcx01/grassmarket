# Tom Fielding — cold stress-test report

Persona: chartered financial planner, 22 years an IFA (Midlands, ex-restricted-network). Lens: **St. James's Place — WEALTH**. Staging instance, account tom.fielding@bruntsfieldcapital.com, 2026-07-22.

## 1. Task matrix
| Task attempted | Outcome (done / partial / blocked) | Notes |
|---|---|---|
| Dashboard onboarding + 4-step tour + Guide primer | done | Clear first-run path; Guide is genuinely good ("your judgement, made consistent, comparable, defensible") |
| Pipeline: add St. James's Place, open detail, move stages to Contracted | done | Win-probability is rule-based, explained ("Workshop Scheduled — 25% base") with a "would sharpen the estimate" list; full stage history kept |
| Start assessment — Wealth / investment management model, sandbox mode | done | SJP not in the company registry — saved as manual, unlinked subject |
| Business Metrics (10 wealth metrics, evidence-grade confidence, source field) | done | AUM £bn, adviser headcount, margin in bps with Consumer-Duty fair-value note, net new money "legitimately NEGATIVE" — properly wealth-framed |
| Rate all 7 Powers (benefit/barrier, E1–E4 grades, rationale) | done | Benefit-vs-barrier "engine takes the weaker side" explained on-page; ungraded powers "score as a labelled point, never a false-tight range" |
| Infrastructure Deep Dive — 26 subcomponents, 7 modules | done | COBS 9A, CASS, Consumer-Duty ongoing-service evidencing, PROD, MiFID II best execution — a credible wealth control set; ★ critical bottleneck gating explained |
| Customer Proposition step | blocked (by design) | Honestly skipped: "not yet modelled for the wealth operating model… does not affect your V" |
| Watch live score + uncertainty | done | V 55.4→56.1 as coverage rose; uncertainty High→Medium; always "P50 · P10–P90" labelled |
| Finalise solo (sandbox) | done | Worked — but the locked V (58.0) differs from the live V I watched (56.1); same range 53.1–59.1; no explanation shown |
| Score consistency: rail / summary / portfolio row / engagement / AI narrative | partial | Locked V 58.0 consistent everywhere; **B/P/L in the AI narrative (71.1/41.6/54.2) contradict the on-screen summary (70.4/37.4/53.2)**; "Coverage 51%" on portfolio row vs "26/26 (100% of applicable)" in summary |
| Engagement creation + link finalised assessment | done (with friction) | "Open engagement" and "Link" buttons disabled with no reason; engagement says "No assessment yet — Start an assessment" even when a linkable finalised assessment exists |
| Generate deliverable (internal draft) | done | Labelled DRAFT with timestamp; sandbox banner carried onto the deliverables card |
| AI narratives + approval | done | "AI proposes · a human approves"; per-section approve/edit; audit trail "Approved by 0f5c8717 at… · approved without edits"; pack blocked from client until all approved |
| Generate client-facing document | blocked (by design) | Refused with itemised reasons: each Established+ power and every triad rating "awaits Rating Committee sign-off". Exactly right |
| Scrutinise "Recommended to sell" | done | Commission disclosed, advisor-facing only — but the match itself is wrong-segment (see friction log) |
| Earnings | done | Transparent per-product schedule "read live from the Earnings schedule (never a typed-in number)"; illustrative deals labelled |
| Academy: lesson + comprehension check | done | Check-yourself free-text + model answer works; course still showed 0/8 lessons afterwards — completion mechanics opaque |
| Workshop scheduling | not attempted | Form present on prospect record; ran out of appetite after the engagement friction |

## 2. Friction & distrust log
- **The headline score changed when I finalised — 56.1 live became 58.0 locked, same range, zero explanation.** I watched 56.1 for the entire assessment; the moment I pressed "Finalise & lock inputs" the number I must defend became 58.0. If a client's technical adviser asks why my worksheet says 56 and my report says 58, I have no answer. Severity: **high**.
- **The approved AI narrative quotes different B/P/L than the screen it sits on.** AI Interpretation: "B=71.1, P=41.6, L=54.2". Summary rail directly above: B 70.4, P 37.4, L 53.2. P differs by 4.2 points. I approved a narrative that contradicts the numbers I was shown while approving it. This is the finalise-vs-live discrepancy leaking into client-bound prose. Severity: **high**.
- **"Recommended to sell" maps a retail gap onto my wealth assessment.** My Client Management & Suitability weakness is COBS 9A process and ongoing-service evidencing. The engine recommends a logo/brand API (Brandfetch) "a fix for content-management and front-end consistency gaps that cheapen the UI", citing "Not yet assessed (no claim made): UI & Navigation" — a subcomponent that doesn't exist in the wealth taxonomy. The panel's own claim — "ranked by the gap evidence only" — is false in spirit for this segment. Commission is disclosed and it is advisor-facing only, which saves it from being dangerous, but it torched my confidence in the matching engine. Severity: **high** (trust), even though compliance guardrails held.
- **Two meanings of "coverage/completeness".** Summary: "Coverage: 26/26 subcomponents (100% of applicable)". Portfolio row and engagement card: "Coverage 51%" / "Completeness 51%". Both describe the same finalised assessment. No reconciliation offered anywhere. Severity: **medium**.
- **Disabled buttons with no reasons.** "Open engagement" (needs a title — no hint) and "Link" (needs a selection — no hint) are just grey. I stop when a button is grey and nothing tells me why. Also the engagement's headline state says "No assessment yet. Start an assessment →" while a finalised, linkable assessment sits one dropdown below — the prominent CTA would have made me build a duplicate assessment from scratch. Severity: **medium**.
- **Tour copy says "9 infrastructure modules"; the wealth deep dive has 7.** Small, but I count things. Severity: **low**.
- **St. James's Place — the UK's largest wealth manager — is not in the company registry.** Saved as "Unlinked — manual subject". Severity: **low** (but telling for the segment).
- **Academy completion is opaque.** I answered a check and revealed the model answer; progress stayed 0/8 with no visible "complete" mechanic. Severity: **low**.
- **A finalised assessment flashes "Enter data to see a live score" while loading.** Two seconds of panic before hydration. Severity: **low**.
- What did NOT erode trust — worth saying: the sandbox banner is everywhere it must be (wizard, portfolio row, engagement card, deliverables card); every score is range-first with P50/P10–P90 labels; the client-facing refusal is itemised and principled; commission rates are never hidden.

## 3. Missing features (for my segment: wealth)
- **A wealth Customer-Proposition (C) model.** The step honestly self-skips, but a wealth platform report with no client-proposition lens (advice relationship quality, reporting, client outcomes, Consumer-Duty outcomes evidence) is missing the dimension a wealth buyer cares most about.
- **A wealth-relevant product shelf.** Everything sellable (Benzinga, OpenBB, Brandfetch, ConnectTrade) is retail-brokerage fintech. Nothing addresses the gaps this assessment actually surfaces for a wealth firm — suitability evidencing tooling, CASS reconciliation, periodic-review automation.
- **UK wealth registry coverage** (SJP, Quilter, Rathbones, Evelyn…) with pre-filled public metrics.
- **Peer benchmarking.** The Guide promises "comparable — this platform against its peers"; there is no visible wealth-cohort comparison anywhere.
- **A regulatory cross-reference annex.** The taxonomy already name-checks COBS 9A, CASS, PROD, MiFID II — an exportable mapping of findings to FCA sourcebook references would be a genuine differentiator for a compliance-led buyer.
- **A visible route from the client-facing refusal to the committee.** The refusal lists what "awaits Rating Committee sign-off" but offers no button to request it; dual-rating co-rater assignment exists on the summary but isn't connected to that refusal.

## 4. Customer-side reaction (St. James's Place)
- **The infrastructure taxonomy would land.** COBS 9A suitability, ongoing-service evidencing (Consumer Duty), CASS controls, PROD governance — this is SJP's actual language, and "ongoing-service evidencing" as a weak spot is their lived history (the ongoing-advice evidence provision). A COO would recognise the diagnosis as informed, not generic.
- **The Consumer-Duty framing of revenue margin ("an unexplained-high margin is a liability, not pure quality") is precisely the conversation SJP has been through** on charge restructuring — credible and slightly uncomfortable in the right way.
- **They would find the number inconsistencies.** SJP's technical due diligence would put the 56.1/58.0 and the narrative-vs-screen B/P/L side by side and ask which is the number. That single question undoes the "defensible" promise.
- **The Brandfetch recommendation would get laughed out of the room** — a brand-asset API pitched against a suitability-process gap — and it would retroactively taint the report's "evidence-based" claim.
- **The absent client-proposition dimension undersells them.** SJP's whole thesis is the advice relationship; a platform-value report that says "your client proposition is a different construct (not yet authored)" reads as "we measured everything except what you're best at".
- **Their compliance function would, however, be genuinely reassured** by the watermarking, the sandbox labelling, the AI approval audit trail, and a system that refuses to produce a client document without committee sign-off.

## 5. Confidence score & Top-5 issues
Confidence: **56 / 100** — the assessment spine, honesty engineering and governance gates are the best I've seen in this class, but a headline score that changes at finalisation, narrative numbers that contradict the screen, and wrong-segment sell recommendations are exactly the defects a wealth buyer's due diligence will find.

Top 5 issues (ranked):
1. **Finalisation silently changes the headline V (56.1 → 58.0, identical range)** — high; wizard Summary & Interpretation → everywhere the locked score propagates; either freeze the live number at lock or show a one-line explanation of the locked-run recompute right where the number changes.
2. **Approved AI narrative quotes B/P/L that contradict the on-screen summary (71.1/41.6/54.2 vs 70.4/37.4/53.2)** — high; engagement Review AI panel; make every surface quote the single locked run — an approver must never sign prose whose numbers differ from the screen they approved it on.
3. **"Recommended to sell" maps retail-taxonomy evidence ("UI & Navigation") onto wealth modules and prices commission off it** — high; engagement + assessment rail; suppress or segment-filter product matching when the product's gap taxonomy has no counterpart in the assessed operating model.
4. **"Coverage 51%" vs "Coverage: 26/26 (100% of applicable)" for the same assessment** — medium; portfolio row, engagement card vs wizard summary; one definition, one label, or show both with their denominators.
5. **Disabled buttons with no reason + the buried "Link a finalised assessment" flow** — medium; prospect record and engagement page; add enable-hints ("enter a title to open"), and when a linkable finalised assessment exists, lead with the Link action instead of "Start an assessment →".
