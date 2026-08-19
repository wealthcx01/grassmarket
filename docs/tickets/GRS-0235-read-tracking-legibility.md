# GRS-0235 — Read tracking an advisor can read

**Status:** DONE (2026-08-19). _Previously recorded as: Planned (2026-07-31, first-time-user review G7). **Priority:** LOW-MED._
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

**DONE** — shipped 2026-08-19, all three scopes.

## What the measurement found first

**Every number the ticket asks for was already being returned.** `read_summary_for_link` walks
`SECTION_ORDER` and returns `views`, `total_dwell_ms`, `first_viewed_at` and `last_viewed_at` per
section, and `SectionReadSummary` has carried all four fields since GRS-0220. So the ticket's test
plan item 2 — "backend: summary endpoint returns titles alongside keys" — needed no backend change
at all. **This shipped as a display-only build**, and the decision the ticket asks to be stated is:
*the frontend maps from the shared section registry.* Adding titles to the API would have put the
same six strings in a second place, which is the problem this ticket is about.

## The defect underneath the reported one

The titles were "one component away", as the ticket says. What the ticket did not know is that they
were **one component away in three different places**: `SharedReport.tsx`, the report editor page,
and two of the editor's own test files each carried a hand-written copy of the same six pairs.

They all agreed. Nothing made them agree. Worse, because two of the copies were *in tests*, those
tests compared a copy against a copy — they would have gone on passing after the product drifted.
That is the same shape as the defect GRS-0231 shipped to staging: a test asserting the right
property against an invented fixture.

## What shipped

**1 — Titles, in reading order, with the gaps visible.** `ReportReadDetail` lists all six sections
from the registry in the order a client reads them, with unread ones shown as unread rather than
omitted. The old display listed only what *was* opened, which hid the preparation signal the ticket
identifies: knowing a client skipped "What that is worth" is worth more than knowing they read the
rest.

**2 — Dwell, displayed with its limits attached.** Rounded to 10-second buckets so nobody compares
47s against 52s; "under 10s" rather than "0s" for a brief visit, because 0s beside a view count of 1
reads as a bug; an explicit "(at the cap)" marker when a figure has hit the six-hour ceiling, which
is the one case where the number is known to be wrong rather than merely imprecise. The caption
states all three limits plus the one the ticket does not mention: **a client who reads the PDF
instead of the link shows as unread**, so absence here is not proof they did not read it.

**3 — First and last opened, per link.** Computed across all sections rather than from one, because
a client rarely reads in order — the first section opened is usually not `business`. A single visit
renders as one moment; a return visit renders as a range.

**One registry, drift-tested by the side that owns the truth.** `frontend/lib/reportSections.ts` is
now the frontend's only copy, and `tests/test_report_section_titles_mirror.py` fails if it and
`bcap_contracts.client_report.SECTION_TITLES` disagree. The check is in **pytest, not vitest**,
deliberately: a TypeScript test can only compare the mirror to another TypeScript copy, which is the
failure being fixed. A fourth test fails if a second literal reappears anywhere — it caught the two
test-file copies on its first run, which is how they were found.

## Verified by mutation, not by green

Three deliberate breakages, each confirmed to fail the gate before being reverted:

| Mutation | Caught by |
|---|---|
| Render the raw key instead of the title (the shipped defect) | 2 vitest failures |
| Omit unread sections (the old display's behaviour) | 3 vitest failures |
| Drift one title in the frontend mirror | the pytest mirror test |

## Not done

Nothing in scope. Out-of-scope items stand: what is recorded is unchanged (GRS-0220's
narrow-by-construction rules), and notifications on first read remain unticketed.
