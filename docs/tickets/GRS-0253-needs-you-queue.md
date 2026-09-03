# GRS-0253 — One needs-you queue: `GET /queue`

**Status:** OPEN (2026-09-03). **Priority:** HIGH. **Type:** Feature (read model).
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

## Done when

`GET /queue` returns every item waiting on the caller, oldest first, and the frontend deletes its
client-side merge. The rail badge and the queue page read the same number from the same place.
