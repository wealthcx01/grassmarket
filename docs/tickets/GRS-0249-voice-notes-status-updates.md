# GRS-0249 — Advisors update status by voice note

**Status:** OPEN (2026-09-02). **Priority:** MED-HIGH. **Type:** Feature.
**Loop:** post-wave. **Founder request:** 2026-09-02, citing Wispr Flow as the reference experience.
**Depends on:** **GRS-0251** (production transcription is a test double — hard blocker) and
**GRS-0247** (nowhere to keep the recording).
**Relates to:** GRS-0029/0030 (Path B), GRS-0198 (pipeline linkage), ADR-0009.
**Non-negotiable in play:** **#8 — AI proposes, humans approve.**

## Why

The real problem is that **status updates happen in a car park after a client meeting**, and every
surface we have assumes a keyboard: stage changes, comms-log entries, checkpoint confirmations,
engagement notes. The pipeline is only as honest as the last time someone typed into it. This is
the gap Path B closes for assessments, one level down and far more frequent.

## The ask splits in two, and they are different products

**A. Dictation — what Wispr Flow actually is.** An OS-level dictation app (Mac, Windows, iOS,
Android) that types into whatever field has focus, no plugin or integration. Checked 2026-09-02:
**its site documents no public API or SDK**, so there is nothing to integrate. Advisors install it
and dictate into our existing text boxes. **This needs no engineering from us** beyond confirming
our textareas behave under dictation — worth ten minutes of testing on the comms-log and engagement
note fields, since a controlled React input can drop or reorder dictated text.
Free tier: 2,000 words/week. 100+ languages. SOC 2 Type II / ISO 27001 / HIPAA.

**B. Voice notes as first-class records — what this ticket builds.** The advisor records in
Grassmarket; the audio is stored, transcribed, and proposed as a structured update the advisor
approves before it lands.

**Recommendation: tell advisors about (A) this week, and build (B).** They are complementary. (A) is
a typing aid available immediately at zero cost. (B) is a record with provenance and an approval
trail, which is what the pipeline lacks.

## What already exists (checked 2026-09-02 — more than expected)

`POST /transcripts/media` already accepts base64 audio, caps size before decoding, scans, encrypts
and stores owner-scoped with a retention date. Path B extraction already turns a transcript into
per-field proposals with confidence, reviewed and confirmed by the advisor. `field_provenances`
already records where a confirmed value came from.

So roughly **half of (B) is built.** What is missing is a recorder, a place to keep the audio, a
transcriber that works, and a mapping from transcript to *pipeline* fields rather than assessment
fields.

## Blockers, stated plainly

**GRS-0251 is a hard blocker.** Production "transcription" is `EchoTranscriber` — it decodes the
bytes as UTF-8 with `errors="replace"` and returns 201. Shipping a record button on top of that
would take an advisor's voice and store replacement characters as their meeting note, silently.
**Do not build the recorder until a real transcriber refuses to be a stub.**

**GRS-0247 is a soft blocker.** Media bytes are discarded after transcription today. A corrected
transcript whose recording was thrown away cannot be re-checked when the extraction is disputed —
and disputes are the whole reason to keep provenance.

## Scope

1. **Capture.** Browser `MediaRecorder` in the advisor UI, and it must work on a phone browser,
   because that is where the car park is. No native app. Show a level meter and the elapsed time;
   a silent failed recording is the obvious way to lose the note.
2. **Store the audio** via GRS-0247 — owner-scoped, encrypted at rest, provenance per ADR-0029,
   linked to the transcript it produced. Keep both, always.
3. **Transcribe** via the provider GRS-0251 selects. Do not make this decision twice.
4. **Extract to a proposal, never straight to state.** Reuse the Path B pattern exactly: per-field
   confidence, advisor reviews and corrects, then confirms. **Non-negotiable #8 in full — a voice
   note must never move a prospect stage on its own.** The recorded approval is the gate.
   Target fields: stage change, next action + date, comms-log entry, engagement note.
5. **Fail loud.** A failed transcription shows as failed. It never becomes an empty note, and it
   never becomes mojibake (see GRS-0251).
6. **Offline tolerance.** A recording made with no signal should queue and upload later rather than
   vanish — the car park has one bar. Decide whether v1 does this or explicitly does not.

## Explicitly not in scope

Real-time transcription, speaker diarisation, and recording live client meetings — that last is
Path B's territory and carries consent obligations this ticket does not address.

## Done when

An advisor records 30 seconds on a phone, sees a transcript, sees a proposed stage change and next
action, edits one field, confirms — and the pipeline shows the change with the voice note attached
as its source, audio and transcript both retrievable.
