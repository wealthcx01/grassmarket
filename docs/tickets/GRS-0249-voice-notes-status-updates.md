# GRS-0249 — Advisors update status by voice note

**Status:** DONE (2026-09-03) — all six scopes built. **Priority:** MED-HIGH. **Type:** Feature.
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

## Where this got to (2026-09-03)

Both blockers cleared first: GRS-0251 and GRS-0247 merged to `main` as PRs #271 and #273.

**Built.** Scope 1, 2, 3, 5 and 6, plus the consent gate that GRS-0255 owns.

- `MediaRecorder` in the advisor UI on the prospect page, working at phone width, with a live level
  meter and elapsed time. Screenshotted at 1440×1000 and 393×851.
- **The consent gate, and the decision behind it.** The advisor states who was in the room before
  anything records. *A voice note* is the advisor alone — no consent, because there is nobody to
  ask. *A recorded session* has somebody else present, shows the founder-approved wording from
  GRS-0255 verbatim, and cannot be stored without `consent_confirmed_at` + `consent_wording`.
  Both directions are refused: a session without consent, and a voice note claiming consent nobody
  gave. Enforced in the contract, the repository and a table CHECK.
- The wording is served by `GET /transcripts/consent-line` so exactly one copy of it exists, and an
  upload carrying different text is refused rather than stored.
- **The audio is kept** as a GRS-0247 document, linked by `recording_document_id`. It used to be
  discarded after transcription, which left a disputed correction with nothing to check against.
- Transcripts gained `prospect_id` and `workshop_id` — **GRS-0254 build 1 and 2**, absorbed because
  a car-park note has no engagement to hang off and the ticket cannot work without it.
- **Offline tolerance: v1 does it.** The recording is written to IndexedDB before the first upload
  attempt and released only on a 201; a failed upload stays on the device with a retry.
  **The gap that remains:** the hold starts when the advisor presses stop. A tab that dies *during*
  a recording still loses it, because the chunks are in memory until then. Closing that would mean
  writing each chunk to IndexedDB as it arrives — worth doing, not done here.
- Tests: 14 backend (`tests/test_voice_notes.py`), 8 frontend
  (`frontend/components/VoiceNoteRecorder.test.tsx`).

**Scope 4, built second (2026-09-03).** Extraction to a *pipeline* proposal, as the Path B pattern
one level down.

- **`PipelineExtractor` port** beside `pathb.extraction`, with the same offline default: it
  proposes nothing. A keyword match on "move them to qualified" would be a fabrication wearing a
  confidence score, so the placeholder refuses to guess and returns every field as a gap. The
  Claude extractor plugs in at the composition root — a DI swap, never a handler change.
- **`voice_note_proposals` + `voice_note_proposed_fields`** (migration `0047`). The proposed values
  live there and never on the prospect. `proposed_value` and `confirmed_value` are kept **side by
  side**: collapsing them would destroy the only evidence the gate does anything, because
  afterwards nobody could tell a corrected field from an accepted one.
- **Confirmation applies what the advisor confirmed, not what was suggested.** Each field has its
  own tick and there is no "accept all", because an approval that does not name what it approves is
  not an approval. `accepted` on a field means *applied*, not *the proposal was answered*.
- **Every write goes through the door a typed update uses** — `update_prospect_stage`,
  `update_prospect`, `append_comms_entry`. So the stage-history row is written the same way and an
  illegal move is refused by the same lifecycle graph. This is Path B's `update_assessment`
  convergence, and it is what makes a confirmed voice note indistinguishable from typing.
- **Discard is recorded, not deleted.** "The machine suggested this and a person said no" is worth
  keeping; it is the only positive evidence that the gate bites.

**Two gaps this scope exposed in the model, both now handled:**

1. **There was no next-action field anywhere.** The ticket names "next action + date" as a target
   and the pipeline had nowhere to put it, though the Sales Ops course already teaches that a deal
   with no dated next action is drifting. Added as `next_action` + `next_action_on` (migration
   `0046`), independently nullable — an undated action is honest, and inventing a date to fill the
   column is the fabrication #3 exists to prevent. Shown on the prospect header, where its absence
   is stated in words rather than left blank.
2. **The communication log belongs to an engagement, not a prospect.** A car-park note therefore
   has nowhere to file a comms line until an engagement exists, and a prospect with two engagements
   has no single obvious place. Both are refused **in words the advisor can act on** rather than
   guessed at. Filing it against a prospect properly is GRS-0254-shaped work and is not done here.

**A bug this scope's own tests caught:** `IllegalStageTransition` escaped the confirm route as a
500. The lifecycle graph raises its own exception type rather than `ConflictError`, so "you cannot
go straight from prospect to delivered" arrived as an internal error instead of a 409 the advisor
could read. Mapped, and tested.

**Two things the founder should look at, neither an engineering call.**

1. **The consent wording says the recording is not shared outside the engagement team. The
   transcription provider is hosted OpenAI Whisper, so the audio does leave our infrastructure.**
   The wording is founder-approved and is used verbatim, unchanged. The advisor-facing UI says
   plainly where the audio goes, so the person pressing record is not misled — but the client
   hears the approved line. Reconciling the two is a founder decision (GRS-0255).
2. Whether a solo voice note should show the client-consent line anyway. It does not, because the
   advisor is alone; see the recording-kind split above.

## Done when

An advisor records 30 seconds on a phone, sees a transcript, sees a proposed stage change and next
action, edits one field, confirms — and the pipeline shows the change with the voice note attached
as its source, audio and transcript both retrievable.
