# GRS-0163 — Demo-polish sweep (legibility gaps found in the end-to-end run)

**Status:** Done (2026-07-22). Items 1–2 in PR #188; item 3 promoted to GRS-0164 (#184/#187); items 4–5
(generic network copy, no host:port leak; abort-vs-failure distinction so dead spinners surface a real
error) in the follow-up PR. Small trust/legibility fixes from the staging deep-dive + brokerage run.
**Priority:** MED. **Loop:** demo-readiness. Mostly frontend.

## Items

1. **Portfolio "Segment" column shows "—"** for every assessment even when an operating model was chosen
   — it reads the free-text segment, not the profile. Surface the operating-model profile in the column.
2. **Earnings "Attribution" column shows "—"** — a commission line says "Engagement · £15,000 · Pending"
   but not *which* client/brokerage. Show the engagement/subject name.
3. **Customer-Proposition (C) is scored but not surfaced — HIGH VALUE.** Correction to an earlier note:
   C *is* computed (Revolut 55.6, HL 41.0, WeBull 61.9 on staging) via the `c_index_of` path and shows in
   the live wizard rail — but `BrokeragePortfolioEntry` has no `c_index` field and the deliverable headline
   omits it, so the most-discriminating, most demo-relevant score is hidden. C's spread (41→62, ~21pts) is
   ~4× V's (54→59, ~5pts) and captures the customer-experience story V compresses. **Surface C next to V**
   in the portfolio list and the deliverable/executive-summary headline (reported alongside, not in V —
   ADR-0023 Stage 1). Add `c_index` to `BrokeragePortfolioEntry`. *(Consider promoting to its own ticket.)*
4. **Backend host:port leaks into user-facing error copy** — a network drop shows
   `Cannot reach API at https://…`; a 409 exposes an internal coefficient-set id. Generic status-0 copy in
   `lib/api.ts`; soften the 409 detail.
5. **Silent permanent spinner when the API is down** — several read paths treat a network error as a silent
   return → "Loading…" forever. Add a "Can't reach the studio — Retry" state.

## Acceptance

Each surface reads cleanly to a first-time viewer; no "—" where a real value exists, no raw internal
tokens, no dead spinners.
