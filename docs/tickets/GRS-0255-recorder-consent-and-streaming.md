# GRS-0255 — Recorder: consent, moment marks, speaker labels, streaming

**Status:** OPEN (2026-09-03). **Priority:** MED-HIGH. **Type:** Feature.
**Source:** Backend Requests **R3**. Replaces gap **G12**. **Depends on:** GRS-0249, GRS-0254.

## Why

The design shows a live transcript ~15s behind, speaker labels, "mark this moment", and a consent
line captured before anything is kept. Today the API takes one whole base64 file and returns text
later.

## The consent line is not decoration

**Founder-approved wording, 2026-09-03:**

> *"I'd like to record this session so I can write it up accurately. The recording stays in the
> Bruntsfield advisor system, is transcribed for my notes, and isn't shared outside the engagement
> team. Are you happy for me to record?"*

Store `consent_confirmed_at` **and `consent_wording`** — the exact text shown, not a reference to
it. Wording changes over time and a record that cannot say what was actually agreed is not a
record. **No consent, no recording kept**; the gate refuses rather than storing and flagging.

UK rules make participant consent the safe rule for confidential business meetings, and rules vary
by jurisdiction. Treat any change to this as a founder decision, not an engineering one.

## Build

- `consent_confirmed_at` + `consent_wording` on the transcript, required for a kept recording.
- `marks[]` — timestamps the advisor flagged live.
- `speaker` on segments.
- Chunked or streaming ingest returning partial segments.

**Ship order:** v1 is record → stop → upload → "transcribing…" → review (GRS-0249). The live view
switches on when streaming exists. The hosted Whisper API takes a whole file, so v1 cannot stream
and should not pretend to.

## Done when

A recording without consent is impossible to store, the stored consent says exactly what the client
agreed to, and marked moments survive into extraction review.
