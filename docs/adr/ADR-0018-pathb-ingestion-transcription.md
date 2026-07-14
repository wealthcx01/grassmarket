# ADR-0018 — Path B ingestion: encryption at rest, swappable transcription, no extraction

- **Status:** Accepted
- **Loop:** 6 (GRS-0029)
- **Normative source:** PRD §3.3 (Path B); Viewforth-inherited data-protection standards;
  CLAUDE.md #9 (scoping), #3 (fail loud), #8 (AI proposes — deferred to GRS-0030).
- **Builds on:** GRS-0009 (assessment lifecycle Path B feeds).

## Context

Meeting recordings and transcripts are the raw material of Path B, and they are sensitive (client
conversations). Three things needed deciding before any extraction (GRS-0030) is built: how media
enters and is transcribed, how the stored transcript is protected, and where the trust boundary sits.

## Decision

### 1. Transcription is a swappable adapter; the production default is local Whisper

A `Transcriber` **port** turns uploaded audio/video bytes into text; the provider is a **build-time,
config-selected choice**, never a code change in the ingestion path. The recorded production default
is **local Whisper** (`whisper-local-v1`, openai-whisper / faster-whisper), wired at the composition
root — deliberately NOT imported in the package, so CI never downloads a model. CI and the
adapter-contract test use a deterministic offline `EchoTranscriber`; the swap is proven by a test
that runs the exact same ingestion path against a *second*, differently-behaving provider with no
code change. A pasted transcript needs no transcriber (`transcriber_ref = "pasted"`).

### 2. Transcripts are encrypted at rest; plaintext never lands in the database

A `TranscriptCipher` port encrypts on write and decrypts on read. The shipped implementation is
**Fernet** (authenticated AES-128-CBC + HMAC) keyed from config (`GM_TRANSCRIPT_ENCRYPTION_KEY`); the
key is never hard-coded, a dev placeholder key works locally, and **production refuses the
placeholder** (the `jwt_secret` pattern). The DB column holds only ciphertext (`text_ciphertext`,
`LargeBinary`) — a straight DB read yields no plaintext (tested). A wrong key or tampered ciphertext
**fails loud** (`TranscriptCipherError`), never returns garbage. The port lets a KMS-backed cipher
swap in later. (A malware-scan **hook** — `MediaScanner`, default permissive `AllowAllScanner` —
runs before anything is transcribed or stored, refusing by raising; a real AV scanner plugs in by
config.)

### 3. Storage + retention + scoping, but NO extraction here

Uploads are size-limited (`GM_MAX_UPLOAD_BYTES`, default 25 MB) and type-guarded (`/media` accepts
audio/video only; a text source uses `/text`), enforced before scan/transcribe. Every transcript is
**owner-scoped**: `list` returns the caller's own (admin sees all), and a cross-owner `get` is a
**404** (not shown to exist). A `retention_until` date is carried for the GDPR groundwork (GRS-0032).
Crucially, **no AI extraction happens here** — this ticket is storage + transcription only; mapping a
transcript into the assessment schema (a gated proposal, #8) is GRS-0030.

## Consequences

- The transcription provider is a config/adapter swap, proven; CI stays offline and fast.
- Sensitive transcripts are encrypted at rest with a real cipher and a production-enforced key; the
  scan hook and retention field are in place for the AV integration and GDPR work.
- **Accepted scope boundaries:** the real Whisper adapter and a real AV scanner are composition-root
  wiring behind the ports defined here (not run in CI). Uploads are base64-in-JSON (no multipart
  dependency); a streaming/multipart path can replace the transport later without changing the ports.
  Encryption is app-level Fernet; the managed Postgres also encrypts at rest — defence in depth.
  Retention *enforcement* (the delete job) is GRS-0032.
