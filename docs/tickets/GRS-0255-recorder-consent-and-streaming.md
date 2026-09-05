# GRS-0255 — Recorder: consent, moment marks, speaker labels, streaming

**Status:** PARTLY DONE (2026-09-03) — the consent gate shipped with GRS-0249; marks, speaker
labels and streaming are still open. **Priority:** MED-HIGH. **Type:** Feature.
**Source:** Backend Requests **R3**. Replaces gap **G12**. **Depends on:** GRS-0249, GRS-0254.

## Why

The design shows a live transcript ~15s behind, speaker labels, "mark this moment", and a consent
line captured before anything is kept. Today the API takes one whole base64 file and returns text
later.

## The consent line is not decoration

**Founder-approved wording, 2026-09-03:**

> *"I'd like to record this session so I can write it up accurately. The recording is stored in the
> Bruntsfield advisor system and sent to OpenAI to be transcribed. Beyond that it isn't shared
> outside the engagement team. Are you happy for me to record?"*

Store `consent_confirmed_at` **and `consent_wording`** — the exact text shown, not a reference to
it. Wording changes over time and a record that cannot say what was actually agreed is not a
record. **No consent, no recording kept**; the gate refuses rather than storing and flagging.

UK rules make participant consent the safe rule for confidential business meetings, and rules vary
by jurisdiction. Treat any change to this as a founder decision, not an engineering one.

**Settled 2026-09-04 (founder): the wording now names OpenAI.**

The first version told the client the recording "stays in the Bruntsfield advisor system" and
"isn't shared outside the engagement team". Both were untrue — the transcriber is hosted OpenAI
Whisper (GRS-0251), so the audio leaves our infrastructure. The advisor-facing screen had said so
since GRS-0249, so whoever pressed record was not misled; the client was.

The revision changes only the false part: it states that the recording is sent to OpenAI to be
transcribed, and narrows the sharing promise to "beyond that", which is true.

**Consents already given are untouched.** A stored `consent_wording` is the text that was actually
read to *that* client. Migrating old rows to match a newer promise would destroy the only thing the
field exists for — the record could then say what we would tell someone today, not what that person
agreed to. `tests/test_voice_notes.py::TestChangingTheWordingDoesNotRewriteHistory` pins both
halves: an old wording still reads back, and it can no longer be used for a *new* recording.

## Build

- ~~`consent_confirmed_at` + `consent_wording` on the transcript, required for a kept recording.~~
  **Done 2026-09-03 in GRS-0249** (migration `0045`, PR #274). It could not wait: the recorder
  shipped in that ticket, and shipping a record button with no gate in front of it was not an
  option. What landed goes further than this line asked:

  - The advisor states **who was in the room** before anything records. A *voice note* is the
    advisor alone and carries no consent, because there was nobody to ask; a *recorded session*
    has somebody present and cannot be stored without both fields. Applying this client-facing
    wording to a solo car-park note would have made the advisor attest to a conversation that
    never happened.
  - **Both directions are refused** — a session with no consent, and a voice note claiming consent
    nobody gave. Enforced in the contract, the repository, and a table CHECK, so it holds with the
    application bypassed entirely.
  - The wording is served by `GET /transcripts/consent-line`, so exactly one copy exists in the
    system, and an upload carrying different text is refused. A test compares the constant to this
    ticket file byte for byte: editing the string in code fails the suite.

- **Still open:** `marks[]` — timestamps the advisor flagged live.
- **Still open:** `speaker` on segments.
- **Still open:** chunked or streaming ingest returning partial segments.

**Ship order:** v1 is record → stop → upload → "transcribing…" → review (GRS-0249). The live view
switches on when streaming exists. The hosted Whisper API takes a whole file, so v1 cannot stream
and should not pretend to.

## Done when

A recording without consent is impossible to store, the stored consent says exactly what the client
agreed to, and marked moments survive into extraction review.
