# GRS-0236 — Demo deliverables ship with worked example reports

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-31, founder: "I can't seem to download example client reports")._
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

**DONE.** Example PDFs in `docs/reviews/GRS-0236-demo-example-reports/`.

## What shipped

**Authored example prose for all three showcase brokerages** — six sections each, in
`src/grassmarket/demo/showcase_reports.py`, distinct per firm and written to the GRS-0211 standard.
Revolut is a distribution-led neobank whose constraint is execution depth; Hargreaves Lansdown is an
incumbent whose franchise is defended against the wrong attack; WeBull is a technology-led
challenger with a distribution problem rather than a product one. Three variations on "a strong
platform with room to improve" would have told a reader the assessment says nothing.

**Seeded for EVERY showcase deliverable, not only the Platform Power Report.** A first-time user
opens whichever of the five they land on, and finding that four refuse would teach them the product
is broken. Upsert, so re-running refreshes rather than duplicates.

**A spec without prose now fails the seed loudly**, naming what to add. Adding a fourth brokerage
without an example report would otherwise reintroduce this exact defect silently — the seed would
succeed and the demo would refuse.

**No numerals in the body.** The content model refuses undeclared figures, but the deeper reason is
that this prose is bound to a scoring run whose numbers move when coefficients are re-elicited.
Prose quoting a score would go stale and start contradicting the appendix beside it.

## Evidence

One PDF per brokerage, rendered from the seeded demo records:
`revolut-`, `hargreaves-lansdown-` and `webull-platform-assessment.pdf`. Six pages each,
`DRAFT — not client-usable / NON-PRODUCTION DATA` on **every page**, provenance `demo`.

## The test that matters

`test_every_showcase_deliverable_has_a_worked_example_report` asserts the report **assembles**, not
that prose rows exist. A seeded row that still failed the content model would be the same broken
demo with more data behind it.

## Production seeding — decided 2026-08-01, deliberately not done

Scope 4 asked for the seed to be run **on staging**, and it was (11/11 demo deliverables download,
0 refused). Running it on **production** was considered separately and the founder decided against
it for now.

Production was measured read-only first, and it is not what an earlier note in this thread assumed:
it holds 2 consultants, 3 prospects, 4 assessments, 1 engagement and **zero deliverables**. The
showcase has never been seeded there, so this would have been a fresh creation rather than a prose
backfill.

Three reasons it waits:

1. **It would not achieve the goal.** Showcase records are owned by the demo advisor and
   deliverables are owner-scoped, so the founder would not see the examples in their own account —
   which is this ticket's *own* finding 2, explicitly handed to **GRS-0208**. Seeding before that
   lands means doing it twice.
2. **It creates a real login on the live instance** — `advisor@bruntsfieldcapital.com` with a
   password published in this repository.
3. **It puts ~£49,500 of illustrative commission on the live earnings page.** Demo-provenanced, but
   money-shaped numbers on a page about money.

**Do it after GRS-0208**, in one pass, once there is an account structure that makes the examples
visible to whoever opens them.

