# GRS-0050 — Bound the org-wide list endpoints (pagination)

- **Loop:** 0 / 6 (API hardening)
- **Status:** Fixed — from the 2026-07-14 audit backlog (GRS-0049, API finding #2).
- **Severity:** Medium — unbounded reads on append-only, org-wide tables are a latency/memory DoS.
- **Normative source:** CLAUDE.md #5 (all persistence through the repository layer).

## Problem

Every list endpoint returned the full result set (`.all()`). The two highest-exposure ones are
**org-wide and uncapped**, growing without bound as data accrues:

- `GET /benchmark` (`predictions.py`) — the entire de-identified benchmark population, to any
  authenticated user.
- `GET /compliance/audit` (`compliance.py`) — the entire append-only audit log (admin-only, but
  still unbounded).

## Change

- A capped pagination primitive in the repository layer: `DEFAULT_PAGE_LIMIT = 100`,
  `MAX_PAGE_LIMIT = 500`, and `_clamp_limit()` (unset → default; else clamp to `[1, max]`).
- `list_benchmark_rows` and `list_audit_events` take `limit`/`offset` and apply `.limit().offset()`
  in SQL. The audit log now orders **newest-first** so a capped page shows recent activity (its
  tests are order-independent).
- Both endpoints expose `limit` (`Query(ge=1, le=MAX_PAGE_LIMIT)`) and `offset` (`ge=0`) — an
  out-of-range `limit` is a clean 422; an unparameterised call is capped at 100, never unbounded.

## Scope note (deliberate)

This ticket bounds the **org-wide** endpoints — the genuine DoS surface. The per-consultant list
endpoints (assessments, transcripts, commissions, etc.) are naturally bounded by a single advisor's
data volume and are a lower-risk follow-up (tracked in GRS-0049). The pagination primitive added
here is the shared mechanism they will reuse.

## Exit criteria

- `/benchmark` and `/compliance/audit` cap their result set; an over-limit `limit` is 422; `offset`
  pages correctly; the audit page is newest-first. Pinned by `test_compliance.py`.
