# GRS-0262 — Booking: calendar availability and the booking webhook

**Status:** OPEN (2026-09-03). **Priority:** MED. **Type:** Feature. **Source:** R10. Gap **G11**.
**Depends on:** GRS-0261 (same incremental-consent flow, calendar scope added).

## Why

"Book a workshop" offers three slots from real availability, adds a Meet link, and a client's click
moves the prospect to **Workshop scheduled** and stamps the timeline. `POST /workshops` takes
`scheduled_for` and nothing else — the advisor is expected to have arranged it all elsewhere and
then tell us about it.

## Build

- Cal.com API key per advisor (one `workshop-45` event type) **or** Google Calendar free/busy
  directly. Decide and record which; two calendar sources is a synchronisation problem nobody wants.
- A slot-offer record, so an offer that is never accepted is still a thing that happened.
- A booking-webhook receiver that creates the workshop, moves the stage, and appends to
  `comms_log`.
- `Workshop.location`, `Workshop.meet_url`, `Workshop.attendees[]`.

**Hold both sides.** A booking that moves our stage but not the advisor's calendar, or vice versa,
is worse than no integration.

## Done when

An advisor offers three real slots, the client picks one, and the workshop, the stage and the
timeline all move without anyone typing.
