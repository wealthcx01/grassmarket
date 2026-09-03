# GRS-0254 — Recordings before an engagement exists

**Status:** PARTLY DONE (2026-09-03). **Priority:** HIGH. **Type:** Bug (wrong parent).
**Source:** Backend Requests **R2**. New gap **G13**.

## Why

A workshop is recorded while the client is still a **prospect**. `POST /transcripts/media` and
`/transcripts/text` accept only `engagement_id`, which does not exist yet at that stage — so the
one moment the recorder is for is the one moment it cannot file anything.

## Already done

**GRS-0247 solved this for documents.** The `documents` table takes `prospect_id`, `workshop_id`
**or** `engagement_id` (at least one, CHECK-enforced), and `POST /documents/{id}/engagement/{id}`
re-parents later while keeping the original link. Follow that shape exactly rather than inventing a
second one.

## Build

1. `MeetingTranscriptORM` gains `prospect_id` and `workshop_id` beside `engagement_id`, with the
   same at-least-one rule.
2. Both ingest endpoints accept any of the three.
3. A re-parent path matching the documents one — **keep the original link**. A transcript recorded
   during pitching did belong to that prospect; rewriting that is the quiet edit this codebase
   refuses elsewhere.

## Done when

A transcript can be ingested against a prospect with no engagement anywhere, and re-parents onto an
engagement later without losing what it was originally filed under.
