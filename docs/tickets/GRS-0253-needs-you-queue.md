# GRS-0253 — One needs-you queue: `GET /queue`

**Status:** PARTLY DONE (2026-09-03) — `GET /queue` built with the live sources; the `rate`
kind has no live source to merge. **Priority:** HIGH. **Type:** Feature (read model).
**Source:** Advisor Studio design, Backend Requests **R1**. Replaces gap **G5**.
**Blocks:** the desk, the Needs-you screen, the rail badge, the pocket — four surfaces, one list.

## Why

Everything waiting on an advisor is one idea to them and three endpoints to us:
`/assessments/rating-requests`, `/committee/queue`, `/founder-review/queue`. Nothing covers items
**to send** at all. The frontend composes the three lists itself as a stopgap, which means four
screens each re-implement the same merge and the rail badge can disagree with the page it links to.

## Build

One read model per advisor, oldest first, each item carrying:

- `kind: send | rate | approve`
- `became_actionable_at` — the clock the UI shows as a waited-time
- the target id, and a one-line `reason` in the product's voice

**Do `requested_at` on rating requests first.** It is the cheapest half of this and the waited-time
is unbuildable without it — today the queue cannot say how long anything has waited.

## What the ticket assumed, and what is actually there (2026-09-03)

**Two of the three endpoints named above are retired.** Checked against live production:

| Endpoint | Status |
|---|---|
| `/assessments/rating-requests` | **410 Gone** — retired under ADR-0041 |
| `/committee/queue` | **410 Gone** — retired under ADR-0041 |
| `/founder-review/queue` | live |

Peer rating and Rating Committee sign-off were built for a network larger than this one; the
founder signs what goes out instead (`src/grassmarket/web/retired.py`). So there is no three-way
merge to replace — there is one live source, plus the `send` kind that never existed.

**`requested_at` on rating requests needs no column.** The ticket calls it the cheapest half. It is
cheaper than that: `assign_rater` creates the rater's empty draft row *at assignment*, so
`module_rating_drafts.created_at` already **is** the request time. Nothing to migrate — and nothing
to expose yet either, because the route answering that question is retired.

**There was also no client-side merge to delete.** The frontend has methods for all three endpoints
but only calls `founderReviewQueue`, in the Workbench panel. The merge the ticket describes belongs
to the redesign's needs-you screen (GRS-0267), which is unbuilt. This ticket's job is to make sure
0267 never has to write one.

## Built

`GET /queue` → `NeedsYouQueue`: items oldest first, each carrying `kind`, `target`, `target_id`,
`subject`, `became_actionable_at` and a one-line `reason` in the product's voice. Derived on every
read, never stored, so the badge and the page cannot disagree.

- **`send` — new, and the only kind most advisors will ever see.** A client report the founder has
  signed at its *current* prose hash, with no live share link. That is the quietest way for work to
  stall: it looks finished everywhere it appears, because it is — it just never left. Sending it
  clears it; revoking the link puts it back, because the advisor has un-sent it; editing the prose
  moves it back to the founder, because an approval is a fact about a hash.
- **`approve`** — from the live founder-review queue, assessments and client reports alike.
- **`rate`** — reported as **dormant, in words, with the ADR**. Omitting it silently would make
  "that source is switched off" look identical to "you are up to date", and only one of those means
  the advisor can stop looking. This is the design contract's no-dead-UI rule applied to an empty
  list.

**A source the caller has no role in contributes nothing; it does not refuse the request.** The
founder-review queue 403s anyone but the founder. That refusal is caught, not propagated — a plain
advisor asking what is waiting on them should be told "nothing to approve", not handed a 403 for
the whole queue.

## Settled: peer rating stays off (founder, 2026-09-03)

The redesign's frontend cut (GRS-0271) lists **blind rating** among the Workbench surfaces, while
ADR-0041 has peer rating dormant. The founder confirmed: **it stays off.** There is no blind/peer
rating surface, no committee queue and no calibration session to design.

So the `rate` kind has no source by decision, not by oversight, and the queue says so in words
rather than showing an empty category. `_dormant_sources()` in the repository is the single place
that changes if that is ever revisited.

**`docs/API-SURFACE.md` now says this up front**, because that is the document a designer reads.
The 15 retired routes still appear in the OpenAPI spec, so a design or a generated client will
find them and assume they work — the surface doc lists them together at the top and marks each
one **RETIRED (410 Gone)** inline. The marking is derived from the app's own dependency graph by
`scripts/dump_api_surface.py`, so it cannot claim a route is live after someone retires it, or
keep calling one retired after it is switched back on.

## Done when

`GET /queue` returns every item waiting on the caller, oldest first, and the frontend deletes its
client-side merge. The rail badge and the queue page read the same number from the same place.
