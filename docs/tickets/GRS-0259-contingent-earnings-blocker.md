# GRS-0259 — Contingent earnings: name the blocker

**Status:** OPEN (2026-09-03). **Priority:** MED. **Type:** Feature. **Source:** R7. Replaces **G8**.
**Best built after:** GRS-0253 (each blocker joins to a queue item).

## Why

The design says *"£4,200 contingent on Meridian finalising"*. Today a timeline row carries
`window_end` and nothing that says **what unlocks the pound**. An advisor reading their earnings
can see money they cannot have and not what to do about it — which is the difference between a
statement and a to-do list.

## Build

`blocked_on: {kind, id, label}` per contingent line, joined to its GRS-0253 queue item so the
earnings row links straight to the thing that would release it.

## Done when

Every contingent row names its blocker in the advisor's words and links to the action that clears
it. No row says only "contingent".
