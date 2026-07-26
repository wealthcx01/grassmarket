# James Okafor — cold stress-test report

## 1. Task matrix
| Task attempted | Outcome (done / partial / blocked) | Notes |
|---|---|---|
| Read dashboard onboarding + Guide + Help | done | Literate, candid copy; Helmer provenance declared; Help documents a "Consensus & sign-off" production path I never got to experience as a solo advisor |
| Add RBC Brewin Dolphin to pipeline, enrich record | done | Sector/notes updated win probability with explained "+3pp" deltas; contact form properly disabled until valid |
| Test illegal stage jump (Prospect → Contracted) | done | Rejected with an explicit message listing the legal moves — exemplary guardrail (HTTP 409 surfaced politely) |
| Move prospect through all stages to Contracted | done | Per-stage base probabilities explained at every step; stage history fully recorded |
| Create assessment, WEALTH operating model, sandbox | done | "SANDBOX — NON-PRODUCTION, NOT CLIENT-FACING" banner persistent everywhere the assessment appears |
| Business metrics entry | done | Genuinely wealth-native: AUM, adviser headcount, revenue margin bps with a Consumer-Duty fair-value ceiling note, cost/income |
| Rate all 7 Powers with evidence grades + rationale | done | Benefit/Barrier with "engine takes the weaker side"; E1–E4 evidence grades drive uncertainty, not score; anti-sloppiness nudge appeared when my benefit/barrier diverged |
| Infrastructure deep dive (26 subcomponents) | done (24/26) | Wealth modules incl. "Custody, Settlement & CASS", "Accessibility & vulnerable-client support (Consumer Duty)" — but rubric Guidance reads "not yet authored for this subcomponent (draft profile)" |
| Customer Proposition step | blocked (by design) | Honestly disclosed: C "not yet modelled for the wealth operating model", step skipped rather than mis-scored |
| Finalise solo (sandbox path) | done | One click, no confirmation dialog, immediately "Finalised · locked"; no at-the-moment statement of what the solo path skips vs production |
| Score agreement across surfaces | partial | Portfolio, engagement and summary all quote the locked 50.1 — but the live score was 49.6 seconds before finalising, under a label claiming "the same number"; "Completeness 47%" sits beside "Coverage 24/26 (92%)" with no reconciliation |
| Generate deliverable (internal draft) | done | Watermarked DRAFT with timestamp; AI narratives panel gated "AI proposes · a human approves" |
| Generate client-facing deliverable from sandbox | blocked (by design) | The Client-facing option simply cannot be selected — structural block, but silent: no worded refusal explaining why |
| Review "Recommended to sell" surface | done | Conflict handling labelled ("ranked by gap evidence only; commission shown for information; never client-facing"; "Not yet assessed (no claim made)") — but the products/copy are retail-brokerage flavoured |
| Earnings review | done | Clean, states commission is "read live from the Earnings schedule (never a typed-in number)"; empty-state milestones push "Sell Benzinga and earn £15,000" |
| Academy — Sales course tone review | done | "Sales Egoist" doctrine: "zero-sum pipeline", "weapons". Mechanics are competent and wealth-aware; branding is a compliance liability |
| Workbench (certification, calibration) | done | Calibration empty; certification ladder shows raw keys ("brandfetch_distribution product"); my level says "Certified Lead" while "Exam: Not taken" |
| Profile / Settings | done | Profile has working password change; Settings is an honest stub ("nothing to configure yet") |

## 2. Friction & distrust log
- **Finalised score differs from the live score (49.6 → 50.1) under a label that says "the same number your portfolio and the deliverable quote".** I watched 49.6 all afternoon; the lock produced 50.1 with no explanation of the re-run. If a client's CTO asked me why, I could not answer. Severity: **high**.
- **Wealth rubric anchors not authored.** The row-level Guidance says "Guidance not yet authored for this subcomponent (draft profile)". The Guide's core promise is "two advisors reach the same score from the same facts" — without anchors my ratings are opinion, and the finalised 50.1 rests on it. Disclosed honestly, but it guts defensibility for my segment. Severity: **high**.
- **"Sales Egoist" / "zero-sum pipeline" / "weapons" branding in a mandatory course.** If a client, journalist, or the FCA saw a wealth adviser's mandatory training titled "Sales Egoist", it reads as evidence of a sales-first culture — the opposite of Consumer Duty. The content underneath is defensible; the label is not. Severity: **high** (reputational).
- **Earnings empty-state: "CLOSE THIS NEXT — Sell Benzinga and earn £15,000.00 in year one."** Incentive-first framing with no accompanying conflict/disclosure guidance. The recommended-to-sell panel handles the conflict better than this milestone strip does. Severity: **med-high**.
- **One-click finalisation with no confirmation.** An immutable, input-locking action executed instantly. I expected a dialog stating consequences and the sandbox-vs-production difference. Severity: **med**.
- **"Completeness 47%" (portfolio, engagement) vs "Coverage 24/26 subcomponents (92% of applicable)" (wizard).** Two unexplained, apparently contradictory figures for the same assessment. Severity: **med**.
- **Client-facing generation is refused silently** — the option just can't be picked. The surrounding sandbox banner implies why, but a professional product should say so at the point of refusal, in words I could repeat to a colleague. Severity: **med**.
- **Duplicate deliverable generation with no warning** — I ended up with three identical "Platform Power Report — DRAFT" rows in five minutes. Severity: **low-med**.
- **US date formats throughout** ("7/22/2026", an mm/dd/yyyy date picker) on a sterling-denominated UK advisory platform. Small, but clients notice, and it makes the polish look imported. Severity: **low-med**.
- **Recommended-to-sell copy is retail-brokerage language for a wealth client** — "enriched ticker pages", "keep clients in-app", "merchant surfaces" pitched against RBC Brewin Dolphin. I would not repeat any of it in a Brewin meeting. Severity: **med**.
- **Status incoherences**: "Level: Certified Lead" beside "Rubric exam: Not taken / Coursework: Outstanding"; "Pipeline conversion 100%" with zero completed engagements; dashboard onboarding still says "Starting fresh?" after a full working day. Severity: **low**.
- **Cosmetics**: "P — POWER 37.4 (30.3–37.4)" — a range whose top equals the point looks wrong even if statistically explicable; "P10–P90HIGH" missing a space; "Review AI|Download" pipe run-on; raw keys ("brandfetch_distribution") in the certification list. Severity: **low**.
- **Disabled buttons with no stated reason** (Open engagement until a title is typed; Add contact until fields valid). Correct behaviour, but silent. Severity: **low**.

## 3. Missing features (for my segment: wealth)
- **A Customer-Proposition model for wealth.** The product says C's wealth taxonomy "has not been authored yet" and skips the step. For a wealth manager the client proposition — advice relationship, planning, reporting — *is* the business. Until C exists for wealth, the assessment reads as a technology audit with the heart missing.
- **Authored §4 rubric anchors for the wealth profile.** Every subcomponent I opened said guidance was unauthored. This is the single biggest gap between the product's promises and what a wealth advisor can defend.
- **Wealth-relevant represented products.** The catalogue (Benzinga, Brandfetch, OpenBB, ConnectTrade) is brokerage-flavoured. A wealth advisor expects planning tools, client-portal, CRM/suitability and custody-integration vendors to recommend against wealth gaps.
- **Client-disclosure support for the commission conflict.** The internal labelling is good; what's missing is anything I could hand a client — a disclosure paragraph, a "how we are remunerated" statement tied to the recommendation.
- **A visible peer-review/consensus experience (or a clear in-product explanation) for the production finalisation path.** Help describes consensus and sign-off; the product only let me experience the sandbox. At the moment of finalising, nothing told me what the production path would have added.
- **UK locale**: DD/MM/YYYY dates, at minimum.
- **Peer benchmarking for wealth** — nothing tells me whether V=50 is good or poor against comparable wealth platforms.

## 4. Customer-side reaction (RBC Brewin Dolphin)
- **They would respect the method's honesty.** "Read the range, not the point", the bottleneck logic, evidence grades, and the refusal to score unrated items are exactly the temperament a Brewin investment committee likes. The vocabulary — CASS, Consumer Duty fair-value ceiling, vulnerable-client support — earns real credibility; someone wrote this who knows UK wealth regulation.
- **Their due diligence would break the spell at the anchors.** The first technical question — "what standard were these ratings scored against?" — currently answers "a draft profile with unauthored guidance". For a firm that would put this report in front of an RBC risk function, that ends the conversation until the rubric exists.
- **They would ask why their client proposition wasn't scored.** Telling a wealth manager "your client proposition isn't modelled yet, but your custody plumbing is" inverts their view of what matters.
- **The product recommendations would misfire.** Pitching a ticker-news feed and a logo API against a discretionary manager's gaps would read as tone-deaf, and the year-one commission figures displayed alongside would sharpen their scepticism about whose interest the recommendation serves.
- **If they ever saw "Sales Egoist"** — in a screen-share, a leaked deck, an FOI-adjacent moment — the relationship damage would outlast any report. Brewin's brand is 250 years of discretion; they buy advisers who don't look like they're being trained to treat them as a "zero-sum" position.

## 5. Confidence score & Top-5 issues
Confidence: 58 / 100 — the method, honesty and guardrails are genuinely impressive and mostly kept the promises the Guide makes, but for the wealth segment the scoring floor (unauthored rubric, missing C), the two-score finalisation wobble, and the sales-culture tone mean I could not yet put my name to it in front of Brewin and the FCA.

Top 5 issues (ranked):
1. **Wealth rubric anchors unauthored ("draft profile")** — high; Infrastructure Deep Dive guidance panels; author the §4 anchors for the wealth profile before selling into wealth, or label the headline score itself as provisional, not just the row guidance.
2. **Finalised score ≠ last live score (49.6 → 50.1) under a "same number" label** — high; Summary & Interpretation at finalise; either freeze the exact displayed run at lock or state plainly "finalisation re-runs the engine; your live figure may shift within the range".
3. **Sales doctrine tone + incentive-first earnings nudges** — high (reputational); Academy "Sales Egoist" course and Earnings "CLOSE THIS NEXT" strip; rename the doctrine, keep the mechanics, and pair every sell-nudge with client-disclosure language a regulated adviser can use.
4. **No Customer-Proposition model for wealth** — med-high; wizard step 5 and portfolio C column; ship the wealth C taxonomy (advice relationship, planning, reporting) — the current skip is honest but leaves the segment's core construct unmeasured.
5. **Finalisation UX: one-click irreversible lock, no confirmation, and "Completeness 47%" vs "Coverage 92%" unreconciled** — med; assessment wizard and portfolio; add a confirm dialog that states consequences and the sandbox-vs-production difference, and use one completeness figure (or explain both) everywhere.
