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

1. ~~`MeetingTranscriptORM` gains `prospect_id` and `workshop_id` beside `engagement_id`.~~
   **Done 2026-09-03 in GRS-0249** (migration `0045`), which could not work without it: a voice
   note recorded after a pitch has no engagement to hang off. `engagement_id` also became a real
   foreign key in the same migration — it was a bare `Uuid`, and leaving one of three parents
   unenforced is the dangling reference GRS-0246 made structurally impossible everywhere else.
   Note the at-least-one rule is deliberately **not** applied here, unlike `documents`: a
   transcript nobody has filed yet is a real state, and refusing it would refuse the pasted
   transcripts that already exist.
2. ~~Both ingest endpoints accept any of the three.~~ **Done 2026-09-03 in GRS-0249.**
3. **Still to do.** A re-parent path matching the documents one — **keep the original link**. A
   transcript recorded during pitching did belong to that prospect; rewriting that is the quiet
   edit this codebase refuses elsewhere. This is what is left of the ticket.

## Done when

A transcript can be ingested against a prospect with no engagement anywhere, and re-parents onto an
engagement later without losing what it was originally filed under.
