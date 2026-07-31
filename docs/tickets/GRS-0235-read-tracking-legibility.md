# GRS-0235 — Read tracking an advisor can read

**Status:** OPEN (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-31, first-time-user review G7). **Priority:** LOW-MED._
**Loop:** client-report hardening. **Extends GRS-0220.**

## Why

The tracking pipeline works — verified end to end on staging 31/07/2026 — and then the advisor sees:

> Read: business, advantage, constraint, actions, value, appendix

Internal section keys, comma-joined. The titles the client actually read ("The business", "Where
the advantage sits"…) exist one component away. And dwell time — the half of GRS-0220 scope 5 that
"changes how an advisor prepares for a meeting" — is recorded, capped and batched with real care,
then never displayed anywhere.

## Scope

1. **Section titles, not keys**, in reading order, with unread sections shown as unread (what was
   *not* read is the preparation signal).
2. **Dwell, displayed honestly.** Per-section dwell and last-opened time on the deliverable's link
   table, rounded coarsely (nearest 10s) so it informs without inviting over-reading; the six-hour
   cap and batching semantics stated in a caption so an advisor knows what the number can and
   cannot tell them.
3. **First-opened / last-opened per link**, replacing the bare "not opened yet"/section-list binary.

## Test plan

1. Vitest: link table renders titles from the section metadata (no raw key appears), unread state,
   and dwell formatting including the cap.
2. Backend: summary endpoint returns titles alongside keys (or the frontend maps from the shared
   section registry — one source, state which in the PR).
3. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- What is recorded (unchanged; the narrow-by-construction rules in GRS-0220 stand).
- Notifications on first read (future, unticketed).

## Acceptance

Before a follow-up call the founder can see, in plain words, which sections the client read, which
they skipped, and roughly how long they spent where.

---

## Status reconciliation — 2026-08-01

**OPEN.** Scheduled in the GRS-0229–0245 wave (see docs/BACKLOG.md for the build order).
