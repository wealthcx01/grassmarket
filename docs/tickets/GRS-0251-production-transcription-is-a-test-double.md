# GRS-0251 — Production transcribes audio by decoding it as UTF-8, and stores the result as a transcript

**Status:** OPEN (2026-09-02). **Priority:** HIGH. **Type:** Bug (silent fallback).
**Loop:** post-wave hardening. **Relates to:** GRS-0029, GRS-0030, GRS-0247, GRS-0249, ADR-0009.
**Non-negotiable violated:** **#3 — fail loud, never silently fall back. Nothing is fabricated.**

## What is wrong

`POST /transcripts/media` accepts audio or video, transcribes it, and stores the transcript
encrypted. The transcriber it uses in **production** is `EchoTranscriber`
(`src/grassmarket/pathb/transcription.py`), whose entire implementation is:

```python
return media.decode("utf-8", errors="replace").strip()
```

That is a **test double**. It exists so CI can round-trip a text fixture masquerading as audio
without downloading a model. It is wired as the unconditional return value of `_transcriber()` in
`src/grassmarket/web/routers/transcripts.py:46`.

Feed it a real MP3 and it does not fail. `errors="replace"` guarantees it cannot: every
undecodable byte becomes U+FFFD, so the function returns a long string of replacement characters,
the endpoint returns **201 Created**, and mojibake is encrypted and stored as that meeting's
transcript — attributed to provider `echo-transcriber-v1`, with no error anywhere.

Everything downstream then treats it as a real transcript: Path B extraction reads it, proposes
fields from it, and an advisor reviews those proposals.

## Why it is still true

The docstrings say the real thing is wired elsewhere — *"the production default is local Whisper
(`WhisperTranscriber`, wired outside CI)"*, *"the real adapter is wired at the composition root."*

It is not. Verified 2026-09-02:

- `grep -rn "WhisperTranscriber\|whisper" src/ --include=*.py` matches **only the comment and
  `WHISPER_PROVIDER_REF` in `transcription.py`**. No adapter class exists anywhere in the repo.
- No setting selects a transcription provider — `config.py` has `max_upload_bytes` and
  `transcript_encryption_key`, and nothing else about transcription.
- Nothing overrides the `_transcriber` dependency outside tests.

So the "composition root" the docstrings describe was never built. The design is sound and the port
is clean; the production implementation behind it is absent, and the absence is invisible because
the stand-in never fails.

## The same shape, second instance

`_scanner()` returns `AllowAllScanner` — *"the default hook — accepts everything. Replace by config
with a real AV scanner in prod."* Nothing replaces it. There is no malware scanning in production
on a path that accepts 25 MB of arbitrary bytes from a browser.

This one is less severe: it is honestly named, it fabricates nothing, and it is a missing control
rather than invented data. But it is unconfigurable by the same omission.

## Why `Settings` did not catch it

`config.py` refuses to boot production with a placeholder JWT secret, a SQLite database, or the
placeholder transcript key. That guard is exactly the right instinct. It simply does not know about
the transcriber or the scanner, so the two test doubles walk straight past it.

## Scope

1. **Make the stand-in refuse to run in production.** The smallest correct fix and the one to do
   first: `EchoTranscriber.transcribe` raises `TranscriptionError` when `env == production`, or the
   `Settings` production guard rejects an echo/allow-all provider at boot the way it rejects the
   placeholder key. **A fabricated transcript must be impossible, even if that means the endpoint
   is unavailable until step 2 lands.** Unavailable is honest; mojibake is not.
2. **Drop `errors="replace"` from the echo transcriber.** It converts a decode failure into
   plausible-looking output. Let it raise; the fixtures it serves are valid UTF-8 anyway.
3. **Add a provider setting** — `GM_TRANSCRIBER_PROVIDER` — resolved at the composition root, with
   an unknown value refused at load time (the registry pattern from ADR-0001).
4. **Build the real adapter.** Local `faster-whisper` in the Railway image (no third party sees
   client audio; costs image size and CPU) or a hosted STT API (smaller image, but client speech
   leaves our infrastructure and needs a data-processing note). **This is the same decision GRS-0249
   scope 3 must make — make it once, here.** Record it as an ADR.
5. **Same treatment for the scanner:** a provider setting, and a production guard that refuses
   `AllowAllScanner`.
6. **Regression test:** constructing the production app with the echo transcriber or the
   allow-all scanner must raise. This is the test that would have caught it.

## Interim note

The exposure today is **zero in practice**: there is no UI for this endpoint (`grep` finds no
frontend reference), so no advisor has ever reached it. That is why this is not an incident. It
would become one the moment GRS-0249 ships a record button, which is why this ticket blocks it.

## Done when

Production refuses to transcribe rather than inventing a transcript; a real provider is selected by
config and produces real text; and a test proves the doubles cannot reach production.
