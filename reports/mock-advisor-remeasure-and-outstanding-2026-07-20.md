# Mock-advisor re-measure + UI/UX audit — synthesis & outstanding issues (2026-07-20)

Prepared for founder review. Five personas re-ran the platform **cold** (never reading source) on a
freshly-rebuilt production stack, plus a white-box every-route UX audit. This is what I changed, what
the numbers say, and — the part that needs **you** — what's left and why.

---

## 1. Scores — and why they moved

| Persona (segment) | Customer | This cold run | Prior full re-measure | Read |
|---|---|---|---|---|
| Marcus (retail) | Robinhood | **72** | 82 | Deepest retail journey; dup-prospects + AUA-vs-neobroker metrics |
| Elena (exchange) | Deutsche Börse | **68** | 78 | Exchange metrics/infra land; retail C-index + unlabeled band |
| Tom (wealth) | SJP | **58** | 63 | Wealth-native inputs strong; earnings/doctrine alien; no client doc |
| James (wealth) | Brewin Dolphin | **53** | 72 | Same as Tom + unauthored rubric + no viewable deliverable |
| Priya (exchange) | LSEG | **57** | 72 | Exchange-native; clearing/data under-modelled; no deliverable |
| **Mean** | | **~61.6** | ~73.4 | |

**The mean dropped, and that is not a regression.** This cold run went *deeper* than prior runs — every
non-retail persona reached the Customer-Proposition tab, tried to produce a deliverable, and probed the
"not client-usable" gate. They hit the **founder-gated ceiling** head-on, and scored it honestly. The
prior ~73 reflected shallower journeys. Read the drop as "the personas found the real ceiling," not
"something broke." No console/API errors or backend flakes were observed on any run.

**The ceiling is remarkably consistent.** Across four non-retail personas the same three things capped
the score, and they are the agenda for the rest of this document:
1. The Customer-Proposition (C) tab showed **retail** widgets to wealth/exchange firms. *(FIXED)*
2. A finalised assessment had **no route to a deliverable**. *(FIXED)*
3. Non-retail scores are **"draft / not client-usable"**, rubric anchors are unauthored, and the
   earnings/Academy layer reads as fintech-reseller — all **founder-scoped content & governance**.

---

## 2. What I fixed this session (shipped, self-merged on green)

| PR | Ticket | Fixes | Raised by |
|---|---|---|---|
| #175 | GRS-0152 | **C-dimension is profile-aware** — wealth/exchange no longer show retail neobroker widgets; the C step degrades honestly ("not yet modelled for this segment"). Dynamic module counts (no hardcoded "nine"). **Provisional "not client-usable" banner now travels with the score** on the live rail + Summary, not just the Overview step. | Elena, Tom, James, Priya (HIGH) |
| #176 | GRS-0153 | **P10/P50/P90 labels** on every uncertainty band (was an unlabeled range). **Inline metric-domain validation** — a negative/impossible value is flagged at entry, not saved silently. | Elena (quant) |
| #177 | GRS-0154 | **Assessment-level deliverable preview** — a finalised (incl. sandbox) assessment can now download its real, watermarked `.docx` with **no engagement required**. The solo/sandbox "see the real deliverable" promise finally pays off. | Priya, Elena, James (HIGH) |
| (earlier) | GRS-0151 | **Critical-control cap** on V — a broken CASS/clearing control can't be out-weighted by a low θ_L (operational-maturity guardrail). | founder-directed |

All four preserve the golden master, are fail-loud, and passed backend + frontend + E2E CI.

---

## 3. Outstanding — FIXABLE (engineering backlog, not blocked on you)

Ranked by trust impact. None require a founder decision; they just weren't in this session's cut.

1. **HIGH — Backend host:port leaks into user-facing error copy.** A network drop shows
   `Cannot reach API at https://…` verbatim; several write paths and the 409 refusal also expose an
   internal coefficient-set id. *Fix:* generic status-0 message in `lib/api.ts`; soften the 409 detail.
2. **MED — Silent permanent spinner when the API is down.** Several read paths treat a network error as
   a silent return → "Loading…" forever. *Fix:* a "Can't reach the studio — Retry" state.
3. **MED — Portfolio "Segment" column shows "—"** even when an operating model was chosen (it reads the
   free-text segment, not the profile). *Fix:* surface `operating_model` in the portfolio row.
4. **MED — No duplicate-prospect guard** — the same company can be added repeatedly and is summed into
   "Expected wins." *Fix:* case-insensitive check on add.
5. **MED — Prospect-detail & contact/inline-edit mutations fail invisibly** (no error handling on
   `updateProspect`/contact CRUD; a load failure dead-ends with no retry). *Fix:* try/catch + inline errors + Retry.
6. **MED — Bench "next actions" are mostly dead-end cards** (only `academy` has a link); Workbench tabs
   aren't URL-addressable. *Fix:* map each queue kind to a route; persist active tab in `?tab=`.
7. **MED — List-vs-detail score inconsistency on a finalised sandbox** (portfolio showed 59.4 while the
   detail said "0/26, not scoreable"). *Fix:* reconcile the portfolio `v_index` source with the detail
   read for sandbox rows. (Worth a focused look — possible data-integrity edge.)
8. **LOW — Header "Guide" pill mis-links to `/help`; `/guide` primer is orphaned**; Settings is a dead
   "coming soon" nav item (the working change-password could live there); raw enum tokens and raw
   consultant UUID ("Approved by 3f2a9b1c") leak in a few places; sandbox watermark uses non-dark-mode
   hex; course-editor has no unsaved-changes guard and can't author the active-recall check.

*(Full file-anchored inventory retained from the audit; happy to burn these down in a follow-up sweep.)*

---

## 4. Outstanding — FOUNDER-SCOPED (this is the real ceiling; I will not guess)

These are the bulk of what's holding the non-retail scores at ~55–70. Each is a **content or governance
decision**, not a bug — and per the non-negotiables (methodology is settled by elicitation, "AI proposes,
humans approve"), I've deliberately **not** fabricated content or flipped a gate. Your call on each:

1. **Phase-4 weight/critical elicitation → activation (the single biggest lever).** Wealth & exchange
   score on **draft** coefficients, so every non-retail assessment is honestly stamped "indicative, not
   client-usable" and can't produce a *client-facing* deliverable. The research-refined **starter**
   weights + the critical-control cap are wired and **gated off** (GRS-0150/0151), awaiting your + the
   panel's ratification. Ratifying them flips the segment client-usable — the lever from ~62 toward
   client-grade. *(Everything is staged; activation is one recorded commit once you sign off.)*
2. **Per-segment Customer-Proposition (C) taxonomy.** I made the C tab *honest* (it no longer asks an
   exchange about "first-deposit ease"); authoring a real wealth C model (advice quality, ongoing
   suitability, planning depth, fee value) and an exchange C model (member/ISV onboarding, FIX/API
   conformance, colocation, data-licensing) is a content build like the L/B taxonomy was (ADR-0025).
3. **Wealth & exchange §4 rubric anchors.** Guidance is honestly "not yet authored (draft profile)" —
   but a discretionary firm's IC calls an unanchored rating unauditable. Needs authored anchors (CASS,
   best-ex/COBS 11, PROD, suitability for wealth; clearing/CCP resilience for exchange).
4. **The commercial & Academy layer vs. the wealth/exchange buyer.** Both wealth personas flagged that
   Earnings (reselling Benzinga/OpenBB/Brandfetch) and the "Sales Egoist / zero-sum / Demo weapon"
   doctrine read as built for a fintech-distribution buyer and clash with a Consumer-Duty culture.
   Decision: segment-gate the commercial/doctrine content, or reframe it for regulated advice firms.
5. **Exchange depth: clearing/CCP + the data franchise.** For LSEG/Deutsche Börse, clearing (margin,
   default waterfall, resilience) and the post-Refinitiv data/analytics business are the majority of the
   company but are one module + two metric lines today. A dedicated clearing module and a data-platform
   module would make the exchange assessment representative.
6. **Retail neobroker metric set.** Retail defaults to AUA (a wealth frame); a neobroker lives on trade
   volume/DARTs, funded accounts, PFOF/net-interest. The helper text *says* this but there's no field.
   (Retail is the golden-master default, so this is a deliberate add, not a bug.)

---

## 5. Recommended order

**You:** decide #4.1 (activation) first — it's staged and unblocks the most. Then #4.2/#4.3 (C taxonomy +
rubric authoring) as the content that makes a non-retail score auditable and client-grade.
**Me (on your word):** burn down the §3 fixable backlog (host leak, retry states, segment column,
dup-prospect, bench routes) in a follow-up sweep, and wire whatever content you author.
