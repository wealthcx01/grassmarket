# GRS-0261 — Gmail connection: drafts, and replies into the timeline

**Status:** OPEN (2026-09-03). **Priority:** MED-HIGH. **Type:** Feature (OAuth). **Source:** R9. Gap **G3**.
**Gates:** GRS-0262. **Founder decision needed:** OAuth scope expansion (D6, currently deferred).

## Why

The design's send path is: approve-and-send writes a draft into **the advisor's own Gmail**, they
send it, and replies stamp the case timeline. Nothing sends itself — that is the product's position,
not a limitation.

`/auth/google` is sign-in only. Day one shows "Gmail not connected" and the send button is dead,
which is the honest placeholder and also a new advisor's first impression.

## Build

- Incremental consent for **draft creation** plus thread read **on studio-initiated threads only**.
  Reading an advisor's whole mailbox is not on the table.
- Draft creation from an approved outreach message.
- Reply ingest into `comms_log` with `kind: email_in | email_out`.

## Founder gate

This expands OAuth scopes on the founder's Workspace, which is **D6 and currently deferred**. Do not
start until that is reopened — the build is cheap and the consent decision is not.

## Done when

An advisor approves a draft, finds it in their own Gmail outbox, sends it, and the reply appears on
the case timeline without anyone copying anything.
