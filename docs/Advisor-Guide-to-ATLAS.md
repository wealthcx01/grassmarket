# The Advisor's Guide to ATLAS

**Bruntsfield Capital — Advisory Network — July 2026**

*This is your working guide to the ATLAS framework and the Advisor Studio tool. It's written for advisors, in plain language. The formal rulebook is `ATLAS-Methodology-v1.1.md` — if anything here seems to disagree with it, the rulebook wins. This guide is part of your certification coursework.*

---

## 1. What ATLAS is, in one paragraph

ATLAS is how Bruntsfield turns what you learn about a client's platform into scores, ratings, and a modernisation plan a board can trust. You gather evidence; ATLAS structures it into three questions — **what does this business achieve** (B), **why is that defensible** (P), and **can the technology carry it** (L) — combines them into one headline Platform Value (V), and tells the client which fix is worth doing first and roughly what it's worth. Your judgment is the input. The framework's job is to make your judgment consistent, comparable, and defensible.

## 2. The three lenses and the headline

**B — Business.** Hard numbers: accounts, revenue, margins, growth, acquisition costs. Answers "what does this platform achieve economically?"

**P — Strategic Power.** Helmer's 7 Powers — scale economies, network effects, switching costs, branding, cornered resource, process power, counter-positioning. Answers "what stops a competitor taking this away?"

**L — Infrastructure.** The deep dive: 9 modules, 51 subcomponents, from the front end to liquidity connectivity. Answers "is the plumbing an asset or a constraint?"

**V — Platform Value** combines all three. But the number clients remember is usually not V — it's the **bottleneck**: "your constraint is Back Office, here's the evidence, here's what fixing it unlocks."

On top of these, the client sees the **Platform Power triad** — three plain-English ratings: **Economic Value** (does value compound with scale?), **Perceived Value** (do customers feel it?), and **Defence Value** (what prevents parity — the moat). These come out as words (None / Emerging / Established / Wide), never decimals.

## 3. How an engagement flows through the tool

1. **Set up** the assessment in Advisor Studio (client, scope, period).
2. **Gather evidence** — meetings, documents, demos, dashboards. You can type inputs directly into the wizard (Path A) or upload meeting transcripts and let the AI draft inputs for you to review and correct (Path B). Both end up in exactly the same place; the AI never scores anything you haven't confirmed.
3. **Rate** — business metrics, the 7 powers, and the infrastructure subcomponents (§4–6 below).
4. **Review** — the live score panel shows B, P, L, V as you go, always as ranges, with the current bottleneck flagged.
5. **Scenarios** — set target levels for chosen subcomponents; the tool re-scores and ranks upgrades by impact, and builds the value bridge (§8).
6. **Finalise** — inputs lock, the scoring run is recorded permanently, and the deliverables generate from it.

## 4. Rating infrastructure: the four levels

Every subcomponent gets one of four levels. Learn these cold:

| Level | The one-line test |
|---|---|
| **Basic** | It barely exists. Manual, unreliable, or absent; people feel the pain regularly. |
| **Developing** | It exists but you wouldn't trust it under pressure. Gaps, workarounds, single points of failure. |
| **Advanced** | It reliably does its job. Automated, monitored, documented. Still improvable. |
| **Frontier** | It's a competitive weapon, not just adequate. |

Three rules that make you a good rater:

**Rate against the rubric, not your gut.** Every subcomponent has a written anchor for each level — what it looks like, what evidence must exist, and the traps (e.g. "vendors demo dynamic routing that's disabled in production — check the prod config"). If your rating can't point to the anchor, it isn't a rating yet.

**Frontier is not the goal.** Each rubric says which kinds of firm actually need Frontier. A single-market wealth platform doesn't need flow-trader order routing. Never present Frontier-everywhere as the target — it reads as either naive or self-serving.

**Use the two special states honestly:**
- **Not Applicable** — genuinely out of scope for this business model (say why). It drops out of the maths entirely.
- **Not Assessed** — in scope, but you didn't get evidence. This is *never* treated as a bad score, but it caps how high the module's headline rating can go and widens the uncertainty range. Marking things honestly as Not Assessed is a mark of professionalism, not failure.

## 5. Evidence grades: how sure are you?

Every rating carries an evidence grade:

| Grade | What it means |
|---|---|
| **E1** | The client told you, and that's all you have |
| **E2** | You probed it in a structured interview with the owner |
| **E3** | You saw the artifact — document, dashboard, config, metric |
| **E4** | You watched it work / inspected it yourself |

This isn't bureaucracy — it directly drives the output. E1 ratings make the score ranges wide; E4 makes them tight. A report full of E1s will say, visibly, "high uncertainty." Push for artifacts. The difference between a £25k assessment and a £75k one is largely the evidence grade you achieve.

## 6. Scoring the 7 Powers: benefit AND barrier

For each power you record two things, with evidence for each:

- **Benefit** — is there a real economic advantage here? (e.g. scale genuinely lowers their unit costs)
- **Barrier** — what stops a competitor copying or neutralising it?

**The power's strength is whichever side is weaker.** A brilliant benefit with no barrier is worth None — competitors will just copy it. This is Helmer's own test, and it's the most common thing new advisors get wrong: they score the benefit and forget to ask what defends it.

Strength comes out as: **None** (matchable within a year), **Emerging** (a serious rival could replicate in 1–2 years), **Established** (3–5 years and real money to erode; more likely than not to persist 5+ years), **Wide** (structural; no credible replication path).

Two more rules: **every power gets scored, always** — "not applicable" doesn't exist for powers; a power that's irrelevant to this business is simply weak, and that's information. And **the stage filter**: young firms plausibly have counter-positioning or a cornered resource, mature firms have branding and process power — if a claimed power doesn't fit the firm's life stage, the tool will challenge it and so should you.

## 7. What the outputs mean (and don't mean)

**Scores are ranges, not points.** The report says "V = 61 (range 55–68)", and each module carries an uncertainty rating. Never quote a bare point score to a client — the range *is* the honest answer.

**Numbers rank; words rate.** The continuous scores (q_m, L, V) are for prioritisation — which module is weakest, which upgrade moves the needle. The headline words (Basic/Developing/Advanced/Frontier per module) come from rules, not arithmetic: a module can't be called Advanced if a critical part is Basic, and can't be Frontier if *anything* assessed in it is Basic. So a module can have a decent-looking number and still be rated Developing — that's the design, not a bug. The words are what you defend in the boardroom; the numbers are how you decide what to fix first.

**Some ratings need sign-off.** Any power rated Established or above, any triad rating above None, and any module rated Frontier goes to the Rating Committee before it reaches a client. Big claims get peer challenge. Budget for it in your timeline.

## 8. Talking about money: the value bridge

This is where ATLAS differs most from what you may have done elsewhere. **We never say "your score gap is worth £X."** Scores and pounds live in separate worlds:

1. **Cost** — what the upgrade costs (estimates, quotes). Hard currency.
2. **Cash-flow levers** — what it changes in *their* numbers: engineering time freed from maintenance, project overruns avoided, incident losses reduced, capacity unlocked. Each is an NPV built on the client's own baselines, with every assumption written down in the report.
3. **Strategic value** — moat and durability implications, stated in words ("more likely than not to sustain X for 5+ years"), never converted to pounds.

Alongside this, the **Upgrade Priority Index** ranks interventions by how much they move V. The index says *what first*; the bridge says *what it's worth*. Keep them side by side and never divide one by the other. If a client pushes you to collapse it into a single ROI number — and they will — the answer is: "the ranking is robust, the pounds depend on your baselines, and here's the assumption register so you can pressure-test both."

## 9. Working practices that keep us credible

- **Two raters per module.** Your solo rating is a draft. Consensus (with recorded dissent) makes it a deliverable.
- **Calibration sessions.** Quarterly, everyone rates the same case vignettes; we measure agreement statistically and rewrite any rubric people read differently. The vignettes double as your practice material in the Workbench.
- **The certification ladder.** Trained → Shadow (2 assessments) → Observed Lead → Certified Lead. Frontier and Wide ratings require a Certified Lead. Your progression is tracked in the Workbench, and bench time between engagements is for exactly this.
- **Predictions get checked.** Every engagement logs what we said would happen ("incidents down 30% within 18 months"). We re-contact clients at 12 and 24 months and score ourselves. This is deliberate: it's what will eventually let us prove the method works — so only predict what you'd bet on.

## 10. The mistakes that get assessments rejected

1. Scoring from memory instead of the rubric anchor.
2. E1 evidence dressed up as certainty — wide ranges are fine; false precision is not.
3. "Not Assessed" avoided by guessing. Guessing is the one thing the framework cannot survive.
4. Powers scored on benefit alone, barrier unexamined.
5. Frontier presented as the universal target.
6. Quoting point scores without ranges.
7. Converting score gaps to pounds directly — the one sentence that fails technical due diligence instantly.
8. Skipping committee on a Wide/Frontier call because the client meeting is tomorrow.

## 11. Glossary

| Term | Meaning |
|---|---|
| **B / P / L / V** | Business, Power, Infrastructure indices; V = the composite Platform Value |
| **Module / subcomponent** | The 9 infrastructure areas and their 51 rated parts |
| **q_m** | A module's continuous quality score |
| **Bottleneck** | The weakest element dragging a module (or the platform) down; ATLAS weights it deliberately |
| **Rating gate** | The rules that turn scores into headline words (Basic→Frontier) |
| **Triad** | Economic / Perceived / Defence Value — the Platform Power ratings |
| **Benefit / Barrier** | The two sides of every power; strength = the weaker one |
| **E1–E4** | Evidence grades, self-reported → observed |
| **N/A vs Not Assessed** | Out of scope (drops out) vs not evidenced (caps ratings, widens ranges) |
| **Uncertainty Rating** | Low/Medium/High/Very High — how solid the assessment is |
| **Upgrade Priority Index** | Ranking of interventions by re-scored impact on V |
| **Value bridge** | The three-layer money story: cost / cash-flow levers / strategic |
| **Coefficient set** | The versioned weights behind the maths, with recorded provenance |
| **Rating Committee** | Peer sign-off for high-stakes ratings |
| **Golden master** | The hand-computed reference assessment the engine must reproduce exactly |

## 12. Where to go deeper

- `ATLAS-Methodology-v1.1.md` — the normative rulebook (certification exam material).
- `ATLAS-Methodology-Guide.md` — the formal foundations: the mathematics, the properties, the literature, the limitations. Read it before your Certified Lead assessment — and before any engagement where the client will put a CTO or a PE diligence team across the table.
- The Workbench — rubric library, practice vignettes, drills, and your certification progress.
