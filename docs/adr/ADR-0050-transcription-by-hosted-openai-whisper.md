# ADR-0050 — Transcription by hosted OpenAI Whisper

- **Status:** Accepted. Two follow-ups open (cost metering, compliance-page note), below.
- **Date:** 2026-09-03 (decision and build, PR #271). Recorded 2026-10-21.
- **Driver:** Founder direction 2026-09-02, in GRS-0251 scope 4: "use their OpenAI API key for
  Whisper." Tickets GRS-0251, GRS-0249, GRS-0255.
- **Amends:** ADR-0018 §1 (the production default transcriber).

## Context

ADR-0018 set up transcription as a swappable `Transcriber` port. It recorded the production default
as **local Whisper**, run on our own infrastructure, so client speech would never leave it.

That local adapter was never built. GRS-0251 found that production was using `EchoTranscriber`, a
test double that decoded audio bytes as text and stored the result as a transcript. Fixing that
needed a real provider. On 2026-09-02 the founder chose **hosted OpenAI Whisper** (`whisper-1`),
using the firm's OpenAI API key.

This changes where client data goes. A recorded client conversation is sensitive, and with this
choice it is processed by a third party. That is why the decision is recorded here and not only in
the ticket.

## Decision

**Production transcribes audio with hosted OpenAI Whisper.** The adapter is
`OpenAIWhisperTranscriber` in `src/grassmarket/pathb/transcription.py`. It is selected by
`GM_TRANSCRIBER_PROVIDER=openai-whisper` and authenticated by `GM_OPENAI_API_KEY`.

**Client speech leaves our infrastructure to be transcribed.** The audio is sent to OpenAI; the
text comes back and is stored encrypted, as ADR-0018 §2 describes. OpenAI does not train on API data
by default, but the audio is still processed by them.

**The port stays.** The `Transcriber` protocol is unchanged. If the data-processing question
hardens, a local `faster-whisper` adapter can be added behind the same port and selected by the same
setting, with no change to the ingestion path.

**This one decision also covers GRS-0249 scope 3.** Voice notes transcribe through the provider
selected here. That ticket said not to make the decision twice, and it was not.

## Safeguards

- **Fail loud, with no fallback.** A rate limit, a timeout, a refusal or any other failure raises
  `TranscriptionError`. The adapter never falls back to another provider, and never to the echo
  test double. A quiet downgrade is the bug GRS-0251 fixed.
- **The key is an operator secret.** `GM_OPENAI_API_KEY` is set as a Railway variable on the
  staging and production API services, and in a local `.env`. It is never committed. `.env.example`
  holds an empty placeholder only. The setting is read only under its `GM_` name, so an unrelated
  `OPENAI_API_KEY` on a machine is never picked up by accident. A missing key refuses to
  transcribe; it does not guess.
- **Test doubles cannot run in production.** `build_transcriber` refuses the `echo` provider in
  production, and `build_scanner` refuses `allow-all`. The endpoint returns a readable 503 instead.
  The app itself still boots; GRS-0251 explains why the refusal sits at the endpoint and not at
  boot.
- **The advisor is told.** The recorder's consent line (GRS-0255,
  `frontend/components/VoiceNoteRecorder.tsx`) says the recording is sent to OpenAI Whisper to be
  transcribed.

## Consequences

- Production produces real transcripts, or refuses. It no longer invents one.
- Each transcript carries the provider's version (`openai-whisper-1`), so it can be traced to the
  service that made it.
- Transcription now depends on an outside service being up and reachable. When it is not, the
  advisor sees an error; nothing is stored.
- There is a running cost of about $0.006 a minute of audio.

## Open items

These are **not built**. They are recorded so they are not mistaken for done.

1. **Cost metering.** Nothing counts audio minutes or spend yet. GRS-0251 scope 4 asked for it. It
   is a small separate ticket if wanted, for example logging the audio seconds of each request.
2. **A note on the compliance surface.** Today only the recorder's consent line names OpenAI. A
   note on the compliance page waits on the founder's D4 decision on UK regulatory framing.
