# Grassmarket Backlog — the single source of truth

Every ticket lives in `docs/tickets/` and carries a **reconciled status stamp** dated 2026-08-01.
This file indexes them; the ticket file is always the detail. Founder decisions live in
`docs/FOUNDER-DECISIONS-2026-08.md`.

## Where things stand

Reconciled 2026-08-01 by auditing all 243 ticket files against git history and the shipped code,
then brought forward on 2026-08-18 when this index finally landed on `main`.

| State | Count | Meaning |
|---|---|---|
| **DONE** | 202 | An implementing commit is on `main`, named in the ticket |
| **OPEN** | 26 | Genuinely unbuilt and schedulable — **3 of them partly built** (GRS-0208, 0234, 0243) |
| **BLOCKED** | 7 | Waiting on a founder decision (D1–D7) |
| **SUPERSEDED** | 8 | Replaced by a later ticket, named in the stamp |
| **Total** | 243 | |

**What the audit corrected.** 99 tickets carried a status that git contradicted — most of Loops 0–6
had no status line at all, GRS-0073–0077 (OAuth, Commission v7, profiles) said *Planned* while each
had its own implementing commit, and the whole GRS-0135–0149 wave still said *In progress* months
after merging. Two umbrella tickets (GRS-0147, GRS-0148) were found **partly** built with a
founder-gated residue and are now BLOCKED rather than silently DONE. GRS-0104 existed as two files,
one a stray What-shipped fragment while the ticket said *Planned*; they are folded into one.

**Why this index arrived seventeen days after its own date.** The reconciliation was written on
2026-08-01 and then sat on an unmerged branch while Phase 2 shipped ten tickets past it, editing the
same ticket files. The two sides conflicted, and until they were resolved `main` carried tickets that
said *Planned* above a *What shipped* record of their own delivery — and carried no founder-decision
file at all. Both are fixed here. The lesson is the ordinary one: a docs branch that indexes moving
work has to land before the work moves, or it becomes a second source of truth competing with the
first.

---

## Open work, in build order

### Phase 1 — shipped

| Ticket | Title | Note |
|---|---|---|
| GRS-0218 | The Sales Egoist course | **DONE** 2026-08-01 (PR #232, merged 08-18). Eight sections, 177 slides, eight diagrams, every lesson citing `data/reference/sales-egoist/`. Resolves GRS-0239 scope 5 |

### Phase 2 — the GRS-0229–0245 wave (2026-07-31 first-time-user review)

Build order below is the wave's own priority: client-trust breaches, then first-run, then the
report workflow, then the rest. **All seventeen have landed or are in review**; the status column is the ticket's
own reconciled stamp, not a summary of it.

| # | Ticket | Title | Group | Status |
|---|---|---|---|---|
| 1 | GRS-0229 | The shared web report must carry the non-production mark | client trust | **DONE** (#233) |
| 2 | GRS-0245 | Founder sign-off covers everything that reaches a client | client trust | **DONE** (#234) |
| 3 | GRS-0236 | Demo deliverables ship with worked example reports | first run | **DONE** (#235, #237) |
| 4 | GRS-0243 | First-run orientation: every section says what it is for, and the home page finally gets reworded | first run | **DONE** (#236, #259, #260) — scope 2 measured moot |
| 5 | GRS-0230 | The report editor: feedback where you can see it, figures you can actually declare | report workflow | **DONE** (#243) |
| 6 | GRS-0231 | The report editor must name the client | report workflow | **DONE** (#244, #247) |
| 7 | GRS-0233 | Web report figures: label the bars, keep the story's order | report workflow | **DONE** (#245) |
| 8 | GRS-0232 | The appendix must not contradict the run | report workflow | **DONE** (#246) |
| 9 | GRS-0234 | PDF furniture: the filename, the subtitle, the footer, the precision | report polish | **MOSTLY DONE** (#248) — scope 4's sparse-page fix measured not to work and was reverted |
| 10 | GRS-0235 | Read tracking an advisor can read | report polish | **DONE** (#249) |
| 11 | GRS-0237 | The engine white paper: one document that answers "is this up to scratch?" | legibility & truthfulness | **DONE** (#250) — scope 3 corrected the record; the VALUES still need D1 |
| 12 | GRS-0238 | A Prospecting surface: browse the registry we imported | legibility & truthfulness | **DONE** (#251) |
| 13 | GRS-0239 | Lessons that teach before they test | legibility & truthfulness | **DONE** (#252, #258) |
| 14 | GRS-0240 | The earnings page explains how you get paid | legibility & truthfulness | **DONE** (#253) |
| 15 | GRS-0241 | Engagements: a list you can read, a link you cannot cross-wire | legibility & truthfulness | **PARTIAL** (#254) — scopes 4, 5 done; 1, 2, 3 open |
| 16 | GRS-0242 | The Workbench stops leaking internals and contradicting itself | legibility & truthfulness | OPEN |
| 17 | GRS-0244 | The Guide must describe the product that exists | legibility & truthfulness | **DONE** (#255) |

**Carried out of Phase 2, still open:** GRS-0208 scopes 3 and 4 (the demo tenancy proper, and the
account surfaces) — scopes 1 and 2 shipped in #239/#240/#242.

### Phase 3 — legacy open queue

| Ticket | Title |
|---|---|
| GRS-0158 | Academy content: seed it into production (the empty-Workbench fix) |
| GRS-0196 | Practice Arena v2: an AI client to practise against |
| GRS-0198 | Pipeline linkage: assessment & deliverable milestones on the pipeline |
| GRS-0199 | Bench honesty + Opportunity Radar wiring |
| GRS-0205 | Rewrite every string in the app, not just the screens we reviewed |
| GRS-0213 | Scenarios an advisor can actually drive, with a narrative assistant |
| GRS-0184 | Scenario workspace v2 |
| GRS-0214 | What the client gets free, and what they get when they engage |
| GRS-0222 | The narrative assistant: drafting against real scored data |
| GRS-0210 | Smart search has to know the firms an advisor will actually type |
| GRS-0224 | Repository-layer coverage for the dormant peer-governance code |

### Open, not yet scheduled

| Ticket | Title |
|---|---|
| GRS-0246 | Deleting an assessment leaves engagements pointing at nothing (found 2026-08-21; production clean, staging had 5) |
| GRS-0041 | Expose gated module rating words in the live-score contract |
| GRS-0049 | 2026-07-14 audit follow-up backlog |
| GRS-0192 | Content freshness watcher |
| GRS-0197 | Gmail + Google Calendar integration |
| GRS-0202 | Outreach message contract, approval gate, and suppression list |
| GRS-0203 | The thin outreach sequencer over the GTM registry |
| GRS-0204 | The outreach send path: Gmail scope escalation or own-domain SMTP |
| GRS-0206 | Rive as the diagram and motion system |
| GRS-0207 | Outreach and CRM platform: decide, then build the thin layer |
| GRS-0208 | One clean demo account, and a founder admin who can act as any advisor — **scopes 3 and 4 only**; 1 and 2 shipped |

---

## Blocked on a founder decision

Detail, options and recommendations in `docs/FOUNDER-DECISIONS-2026-08.md`.

| Ticket | Title | Decision |
|---|---|---|
| GRS-0067 | Earnings config: Commission Schedule v7 delta | D2 |
| GRS-0072 | House deliverable types (Outside Read Deck · Note · Primer · Strategic Assessment) | D3 |
| GRS-0132 | Admin/oversight — DEFERRED to Holy Corner (record only) | — (deferred, not a decision) |
| GRS-0147 | Segment fit — **residue only**: multi-currency + UK regulatory framing | D4 |
| GRS-0148 | Account surfaces — **residue only**: cert teeth, doctrine naming, disclosure | D5 |
| GRS-0201 | Wizard Powers step: embed the Helmer adaptation + review packet | D7 |
| GRS-0212 | Customer Proposition for exchanges: research it, model it, ship it | D1 |

## Superseded register

| Ticket | Title | Superseded by |
|---|---|---|
| GRS-0102 | Meeting-recording upload → AI prepopulation (Path B) | GRS-0197 |
| GRS-0109 | Screen-recording → AI video dissection → auto-populate the widget checklist | GRS-0197 |
| GRS-0112 | Native Gmail + Google Calendar integration | GRS-0197 |
| GRS-0113 | AI / MCP GTM enablement surface | GRS-0207 |
| GRS-0114 | LSEG influencer mapping (bcap-lseg) | GRS-0194 |
| GRS-0115 | Seed the target universe | GRS-0193 |
| GRS-0189 | Rebuild the deliverables to the story architecture | GRS-0211 |
| GRS-0191 | Academy content depth program (the 100x) | GRS-0215 |

---

## Done

190 tickets. Each names its implementing commit in its own
*Status reconciliation* section — that is the record, not this index. Broad shape:

| Range | Theme |
|---|---|
| GRS-0001–0034 | Loops 0–6: scaffold, ATLAS engine + golden master, wizard, pipeline, deliverables, workbench, earnings, Path B |
| GRS-0035–0065 | UI/UX + governance + onboarding series |
| GRS-0066–0086 | Estate reconciliation, OAuth, Commission v7, operating-model profiles, C-index Stage 1 |
| GRS-0087–0134 | Part 2 Advisor Studio UI/UX review |
| GRS-0135–0163 | Academy, trust-hardening, stress-test remediation, demo readiness |
| GRS-0164–0172 | The two-estimator fix (ADR-0040, one-number rule) |
| GRS-0173–0204 | Founder-feedback wave |
| GRS-0205–0228 | Staging-review wave: course rebuild, client report (content model, PDF, shared page), layout fixes |

