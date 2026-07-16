# GRS-0112 — Native Gmail + Google Calendar integration

**Status:** Planned
**Loop:** Part 2 — Pipeline / GTM engine (one program)
**Depends on:** ADR-0027 (Pipeline / GTM engine); ADR-0024 (Google OAuth, GRS-0073)

## Why

For the pipeline to be a real GTM engine, advisers must book workshops and manage prospect
correspondence without leaving the Advisory app. Today workshop scheduling ties to nothing and there
is no email context on a prospect. This ticket adds native Gmail + Google Calendar integration:
workshops booked straight into Google Calendar, emails tied to prospects/deals, all controlled inside
the app. It **extends the existing Google OAuth (GRS-0073 / ADR-0024)** with Gmail + Calendar scopes
and a connected-accounts area. This is **greenfield — EliteVault has no Google integration to port**
(only dormant `email_log` / `meetings_events` schema); Grassmarket's `CommsLogEntry` is the better
starting primitive to attach synced emails and meetings to.

## What to build

- Extend the Google OAuth flow (GRS-0073, ADR-0024) to request Gmail + Calendar scopes, with a
  **connected-accounts area** where an adviser links/unlinks their Google account and sees scope
  status.
- Workshop scheduling writes an event into **Google Calendar** and links it back to the prospect/deal
  so the pipeline stage reflects a real booking (closing the "scheduling ties to nothing" gap from
  GRS-0111).
- Attach synced emails and calendar events to prospects/deals by extending the existing
  **`CommsLogEntry`** primitive rather than reviving EliteVault's dormant schema, so the activity
  timeline in the detail panel shows real correspondence and meetings.
- Keep owner-scoping absolute: an adviser sees only their own linked-account data.

## Acceptance / verification

- An adviser links their Google account via the extended OAuth flow and the connected-accounts area
  shows the granted Gmail + Calendar scopes.
- Booking a workshop creates a Google Calendar event tied to the prospect; the booking appears on the
  prospect timeline.
- Emails/meetings surface against the prospect as `CommsLogEntry` items, scoped to the owner.

## Not in scope

- The CRM card/panel/win-probability rebuild (GRS-0111).
- Running GTM/prospecting MCP skills (GRS-0113); LSEG influencer maps (GRS-0114/0115).
