# GRS-0260 — The pocket's one push event

**Status:** OPEN (2026-09-03). **Priority:** LOW. **Type:** Feature. **Source:** R8. New gap **G15**.
**Depends on:** GRS-0253.

## Why

The pocket sends **exactly one** notification: *you became the blocker*. That restraint is the
design decision — a studio that pushes more than that gets muted, and then the one message that
mattered is muted too. No push channel exists.

## Build

Web Push subscription storage per advisor, and one event fired when a GRS-0253 queue item is created
for them. Nothing else may use this channel without a founder decision; write that into the ticket
that tries.

## Done when

An advisor who becomes the blocker gets one notification on their phone, and no other event in the
system can send one.
