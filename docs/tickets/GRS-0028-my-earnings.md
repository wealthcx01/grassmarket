# GRS-0028 — My Earnings

**Status:** DONE (reconciled 2026-08-01).

- **Loop:** 6
- **Branch:** `grs-0028-my-earnings`
- **Status:** In review
- **Normative source:** PRD §7 (rates are configuration, never code); CLAUDE.md #9.
- **Depends on:** GRS-0011–0013 (pipeline/engagements). Commercial dependency: commission rates decision (founder track) — build with placeholder config, flagged not-final.

## Goal

Transparent, self-scoped earnings for every consultant.

## Scope

1. Commission config model: tier × attribution (self-sourced / Bruntsfield-sourced / co-sourced) → rate; versioned with provenance-style audit on every change.
2. Engagement-level commission calculation from attribution + tier at time of engagement (rate changes never retroactive without an explicit recorded decision).
3. Workshop Recovery Fee lifecycle: eligible → claimed → paid; 12-month attribution window enforced by dates, not judgment.
4. Payment status tracking (earned / invoiced to Bruntsfield / paid out / pending); YTD summary; projection from active pipeline and contracted engagements.
5. Statement export via the report stack (docx/pdf).

## Exit criteria

- Hand-computed commission fixtures reproduce exactly (golden-master discipline).
- Recovery-fee window edge cases tested (day 364, day 366, conversion on the boundary).
- All views scoped to self; admin aggregate is Holy Corner scope, not this ticket.
- Full gate green; CI green.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `7102e8f` (GRS-0028: my earnings — commission config, immutable lines, self-scoped views).

This ticket carried no *What shipped* record; the commits above are that record.
