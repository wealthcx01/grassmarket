# GRS-0236 — Demo deliverables ship with worked example reports

**Status:** OPEN (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-31, founder: "I can't seem to download example client reports")._
**Priority:** HIGH. **Loop:** first-time-user coherence. **Extends GRS-0159.** **Relates to:** GRS-0208, GRS-0211.

## Why

The founder tried to download example client reports and could not. Verified root causes, 31/07/2026:

1. **No seed writes report prose.** `src/grassmarket/demo/brokerage_showcase.py` seeds Revolut,
   Hargreaves Lansdown and WeBull with five deliverables each, but nothing writes
   `ClientReportProseORM` rows, so every demo report is in the "unwritten" state and the PDF and
   share-link paths refuse with the 409 naming six empty sections. The showcase was built before
   the prose requirement landed (GRS-0211 "Wired up", 2026-07-30) and was never revisited.
2. **Owner scoping hides the examples.** The showcase deliverables belong to the demo advisor, so
   `/deliverables` in the founder's own account lists almost nothing; the example flows are
   invisible exactly where the founder looks. (The account-structure half of this is GRS-0208;
   this ticket's job is that whoever CAN see a demo deliverable gets a complete example.)

The demo exists to show the product's best output. Today its best output is a refusal.

## Scope

1. **Author real example prose** for each showcase brokerage — six sections each, written to the
   GRS-0211 standard (business first, no undeclared numbers, appendix pointing at the run), in the
   product voice, distinct per firm. This is authored content, reviewed as content, not lorem.
   It lives in `brokerage_showcase.py` beside each `BrokerageSpec`.
2. **Seed it** via `Repository.save_report_prose` (or the `PUT /deliverables/<id>/report-prose`
   route, consistent with the script's style) after deliverable creation; idempotent by upsert, so
   re-running the showcase refreshes rather than duplicates.
3. **Out of the box, the example works end to end:** open the demo Platform Power Report's report
   page → sections are filled → Download the PDF succeeds (watermarked DEMO per ADR-0029) → a share
   link can be issued and renders the watermarked web page (GRS-0229).
4. **Run it on staging** once merged, and say in the PR that it was run — the GRS-0177 cleanup
   taught us a seed that exists but has not been executed reads as a broken product.

## Test plan

1. Seed test: after the showcase runs, each showcase deliverable's report assembles without
   `ReportNotAssembledError`, passes the content model's own gates, and renders a PDF.
2. Prose fixtures pass the declared-figure and section-order validators (they must, by
   construction — the test proves the authored content actually complies).
3. Manual: PDF for each of the three, attached to the PR.
4. Standing gate: pytest, pyright, ruff.

## Out of scope

- The demo/admin account structure and act-as (GRS-0208).
- AI drafting (GRS-0222) — this prose is hand-authored seed content.
- Deutsche Börse and other staging-only records not in the showcase seed.

## Acceptance

A first-time user opens any showcase deliverable, clicks Download the PDF, and holds a complete,
watermarked, well-written example client report thirty seconds into their first session.

---

## Status reconciliation — 2026-08-01

**OPEN.** Scheduled in the GRS-0229–0245 wave (see docs/BACKLOG.md for the build order).
