# GRS-0257 — Admin network ledger: `GET /network/ledger`

**Status:** OPEN (2026-09-03). **Priority:** MED. **Type:** Feature (admin aggregate).
**Source:** R5. Replaces gap **G7**. **Best built after:** GRS-0253 (it aggregates that queue).

## Why

The admin screen is one table: every advisor with level, pipeline weight, needs-them count and
oldest age, fees this month, connection health. Nothing aggregates across advisors today, and
earnings are owner-scoped, so fees cannot be read without acting as each advisor in turn.

## Build

An **admin-only** aggregate over GRS-0253's queue, `/pipeline/forecast`, `/certification/{id}` and
earnings. Until it lands, admin shows the founder-review queue only — which is the shipped
placeholder state, not a bug.

**Scoping note.** This is the first endpoint that deliberately reads across owners, so it is the
first place non-negotiable #9 is relaxed by design. Guard it by role at the repository layer, not
the router, and test that a non-admin gets a 404. An aggregate is exactly where a scoping mistake
would be least visible.

## Done when

An admin sees every advisor in one read; a consultant calling it gets a 404.
