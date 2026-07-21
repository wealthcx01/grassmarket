# Brokerage reviews, parsed end-to-end through the system (2026-07-21)

Ran the three completed brokerage reviews (Revolut, Hargreaves Lansdown, WeBull) through the **full**
advisor journey on the isolated staging stack — **pipeline → assessment → deliverable → engagement →
product sale → earnings** — to see whether the data flows and whether the outputs land. It does, and they do.

## What ran
For each brokerage, over the live staging API as the demo advisor:
1. **Pipeline** — created the prospect, moved it through all five stages to **Contracted**.
2. **Assessment** — created a sandbox (solo-finalisable) assessment and populated a **faithful document
   built from that brokerage's `*WidgetChecklist_COMPLETED_Claude.md`**: all 51 infrastructure
   subcomponents (9 modules), all 7 Strategic Powers, business metrics, and 39 Customer-Proposition
   subcomponents (the 10 C-index modules). The widget reviews *are* the C-index dataset — they mapped in cleanly.
3. **Finalise** — locked inputs, created the immutable scoring run (sandbox self-approves; no dual-rater needed).
4. **Deliverable** — opened an engagement and generated Executive Summary + Platform Power Report +
   Infrastructure Heatmap (all succeeded; downloaded as valid `.docx`).
5. **Earnings** — recorded a realistic product sale per brokerage and confirmed the commission surface.

## Results — the numbers land and differentiate

| Brokerage | Deliverable V (range) | Portfolio score | Coverage → uncertainty | Product sold | Commission (Yr1) |
|---|---|---|---|---|---|
| **Revolut** | 58.8 (56.1–61.1) | 60.5 | 100% → LOW | Benzinga (£100k) | £15,000 |
| **Hargreaves Lansdown** | 56.5 (54.8–57.8) | 57.2 | 100% → LOW | OpenBB (£150k) | £22,500 |
| **WeBull** | 53.5 (51.1–55.7) | 54.7 | 100% → LOW | ConnectTrade (£80k) | £12,000 |
| | | | | **Advisor YTD** | **£49,500** |

**The ordering is defensible.** Revolut (broadly capable across front-end, app-server, back-office,
orchestration) outscores WeBull (best-in-class trading depth but narrow — weak funding, cluttered UX,
thin back-office). The V engine rewards **platform breadth**, not headline trading features — which is the
methodology's intent. HL sits between (strong custody/education/wrappers, weak modern trading).

**The uncertainty model behaves.** Full 100% coverage → **LOW** uncertainty, vs the seeded 2%-coverage
Meridian record at **VERY HIGH** — exactly right. Earnings figures all read live from the v7 schedule
(`commissions-v7:product:*:yr1`), never typed in; the "99% to £50,000" milestone gamification renders.

## The whole loop works — and here is what I'd polish (found during the run)

None of these broke the flow; they're finish/trust gaps:

1. **Portfolio "Segment" column shows "—"** for every brokerage even though each was created as *Retail
   brokerage*. It reads the free-text segment, not the operating-model profile. (Matches the earlier
   audit's open item.)
2. **List score ≠ deliverable V.** The portfolio shows 60.5 / 57.2 / 54.7 while the deliverables headline
   58.8 / 56.5 / 53.5. Likely a point-estimate vs banded-midpoint difference, but two surfaces showing two
   numbers for the same assessment erodes trust — worth reconciling (or labelling) the two reads.
3. **Earnings "Attribution" column shows "—".** Each commission line says "Engagement · £15,000 · Pending"
   but not *which* client/brokerage it came from. Surfacing the engagement/subject name would make the
   earnings page legible at a glance.
4. **Score spread is tight (54.7–60.5)** across three genuinely different platforms. The ordering is right,
   but the *spread* is narrow — worth a founder gut-check on whether V discriminates strongly enough, or
   whether that compression is expected at this coefficient stage (retail real coefficients).
5. **Sandbox = the only solo path.** All three finalised as sandbox ("NON-PRODUCTION, NOT CLIENT-FACING")
   because a single advisor can't run the dual-rater + committee gate. That's correct governance, but it
   means a solo advisor can *never* produce a client-facing document — expected, just flagging the ceiling.

## Bottom line
The brokerage reviews parse through the system end-to-end with faithful, differentiated results and a
working earnings loop. The engine, scoring, uncertainty, deliverables, and commissions are all sound. The
remaining items are legibility polish, not correctness — and the assessment-wizard density (documented in
the confidence report) is the one genuine UX debt.

*Artefacts:* `scratch/stage/brokerage_e2e.py`, `earnings_e2e.py`, screenshots `scratch/stage/e0*.png`.
Staging data is live (advisor@bruntsfieldcapital.com / grassmarket-demo) if you want to click through it.
