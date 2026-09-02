# GRS-0249 — Advisors update status by voice note

**Status:** OPEN (2026-09-02). **Priority:** MED-HIGH. **Type:** Feature.
**Loop:** post-wave. **Relates to:** GRS-0247 (storage), GRS-0030 (Path B extraction), non-negotiable #8.
**Depends on:** GRS-0247 — there is nowhere to put an audio file until that lands.

## Why

Founder request, 2026-09-02: advisors should be able to leave a voice note to update status,
citing Wispr Flow as the reference experience.

The real problem is that **status updates happen in a car park after a client meeting**, and our
current surfaces all assume a keyboard: stage changes, comms-log entries, checkpoint confirmations,
engagement notes. The pipeline is only as honest as the last time someone typed into it. This is
the same gap Path B addresses for assessments, one level down and far more frequent.

## Two designs, and they are not the same product

**A. Dictation (what Wispr Flow is).** Wispr Flow is an OS-level dictation app — Mac, Windows, iOS,
Android — that types into whatever field has focus, with no plugin or integration. Checked
2026-09-02: **its site documents no public API or SDK.** So we would not integrate it; the advisor
would install it and dictate into our existing text boxes. **This needs no engineering from us at
all** beyond making sure our textareas behave under dictation. Free tier is 2,000 words/week.

**B. Voice notes as first-class records (what the ticket is for).** The advisor records in
Grassmarket, the audio is stored, transcribed, and the transcript is proposed as a structured
update — stage change, next action, comms-log entry — which the advisor approves before it lands.

**Recommend telling advisors about (A) this week and building (B).** They are complementary: (A)
is a typing aid available immediately at zero cost; (B) is a record with provenance, which is what
the pipeline actually lacks.

## Scope (for B)

1. **Capture.** Browser `MediaRecorder` in the advisor UI; also usable on a phone browser, since
   that is where the car park is. No native app.
2. **Store** via GRS-0247 — owner-scoped, encrypted at rest, provenance recorded (ADR-0029). Audio
   of a client conversation is at least as sensitive as a transcript.
3. **Transcribe.** Decide the path: a hosted STT API (a network call and a data-processing question
   — the recording may contain client-identifying speech) versus local Whisper on the Railway
   container (no third party, but CPU cost and a large image). **Recommend hosted for v1 with an
   explicit data-processing note in the UI**, and record the decision as an ADR.
4. **Extract to a proposal, never straight to state.** Reuse the Path B pattern exactly: per-field
   confidence, advisor reviews and corrects, then confirms. **Non-negotiable #8 applies in full** —
   a voice note must never silently move a prospect stage. The recorded approval is the gate.
5. **Keep the audio and the transcript both**, linked. A corrected transcript that loses the
   recording is unauditable.
6. **Fail loud.** Transcription failure shows as failed, not as an empty note.

## Done when

An advisor records 30 seconds on a phone, sees a transcript, sees a proposed stage change and next
action, edits one field, confirms — and the pipeline shows the change with the voice note attached
as its source.

## Explicitly not in scope

Real-time transcription, speaker diarisation, and recording live client meetings (that is Path B
and carries consent obligations this ticket does not address).
