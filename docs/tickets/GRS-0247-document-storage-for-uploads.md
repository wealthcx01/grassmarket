# GRS-0247 — Advisors have nowhere to put a client document

**Status:** OPEN (2026-09-02). **Priority:** HIGH. **Type:** Missing capability.
**Loop:** post-wave. **Relates to:** GRS-0029/GRS-0030 (Path B), GRS-0015 (deliverables), GRS-0249, GRS-0251.
**Non-negotiables in play:** #3 (fail loud), #5 (all persistence through the repository), #9 (scoping absolute).

## Correction to the first draft of this ticket

The first version said *"no router anywhere accepts a file."* **That is wrong and is corrected
here.** `POST /transcripts/media` (`src/grassmarket/web/routers/transcripts.py:101`) has accepted
uploaded bytes since GRS-0029. The grep that produced the claim looked for FastAPI's `UploadFile`,
and this endpoint does not use multipart — it takes **base64 in a JSON body** (`UploadMediaRequest`),
which is why the search missed it.

What that endpoint does, accurately:

- caps size **before** decoding (`settings.max_upload_bytes`, default 25 MB), rejecting on the
  encoded length so an oversized body is never buffered into memory — a nice piece of work;
- runs a `MediaScanner` before anything is stored;
- transcribes via a `Transcriber` port;
- encrypts the **transcript** with Fernet and stores it owner-scoped with a retention date.

So the ingestion *pattern* exists and is good. Three things remain true, and they are what this
ticket is for.

## What is actually missing

**1. It only accepts meeting media.** `source_kind` must be `audio` or `video`
(`_ALLOWED_MEDIA_KINDS`). A PDF board pack, an org chart, a signed engagement letter or an annual
report is refused with a 422. There is no general document type.

**2. The uploaded bytes are discarded.** `MeetingTranscriptORM` has exactly one binary column,
`text_ciphertext` — the transcript. The audio or video that produced it is transcribed and dropped.
Nothing in 47 tables stores an uploaded file as a file.

**3. There is no user interface.** `grep -rln "transcripts/media\|media_base64" frontend/` returns
**nothing**. The endpoint is reachable only by someone hand-crafting an API call. No advisor has
ever used it.

Net effect for the founder's question: an advisor with a client's board pack has nowhere to put it,
and it lives in their email. That is unchanged by the discovery above.

## Why it matters beyond convenience

- **Assessment evidence has no home.** ATLAS judgements cite what the advisor was told; the source
  document cannot be attached, so a rating is unauditable at exactly the point non-negotiable #6
  cares about.
- **The founder's own files move by `scp`.** Commission Schedule v7 and the ASX pack go to
  `/home/dev/inbox/grassmarket/` because the product cannot receive them.
- **GRS-0249 (voice notes) needs somewhere to keep the recording**, and a transcript whose audio was
  thrown away cannot be re-checked when the extraction is disputed.

## Scope

**1. Decide where bytes live — ADR required.**
Postgres `LargeBinary` is the path of least resistance, keeps non-negotiable #5 intact, and reuses
the encryption already written. Against it: Railway Postgres is not a blob store, and every board
pack inflates backup and restore time. Object storage (Railway volume or S3-compatible) needs a
signed-URL path and a second surface to scope, which is a second place for #9 to be got wrong.
**Recommendation: Postgres for v1 with a hard per-file cap, revisited when stored bytes pass ~2 GB.**
Write the ADR either way — this is the cross-cutting kind of decision ADRs exist for.

**2. `documents` table + repository methods.** Owner-scoped (`owner_consultant_id`) like every other
owned resource, with optional `engagement_id` / `prospect_id` / `assessment_id` links; `filename`,
`content_type`, `byte_size`, `sha256`, uploader, and provenance per ADR-0029. Next migration is
`0043`. Scoping tests from day one — an advisor must get a 404, not a 403, for another's document
(the existing routers already model this refusal correctly; copy it).

**3. Generalise rather than duplicate the ingest path.** The size-cap-before-decode, scan, encrypt,
scope sequence in `ingest_media` is the right shape. Prefer extracting it over writing a second one.
Decide explicitly whether documents keep the base64-in-JSON convention or move to multipart
`UploadFile`; **multipart is the recommendation for documents** (a 25 MB PDF becomes ~33 MB of JSON
otherwise), which means the two paths differ at the edge and share the core.

**4. Encrypt at rest**, reusing `FernetTranscriptCipher`'s key path. Client documents are at least
as sensitive as transcripts. Note the key is currently named for transcripts; either rename it or
document that it covers both.

**5. Media-type allowlist, fail loud.** An unknown type is refused, never "stored anyway".

**6. Retention and deletion.** ADR-0047 says production records are not deletable. Decide *now*
whether an uploaded document is such a record or advisor-owned scratch — they are not the same, and
guessing later is precisely how GRS-0246 happened. Carry the `retention_until` idea across from
transcripts.

**7. UI.** Attach on the engagement; list with size, date and uploader; download; remove. This is
also the first surface that would make the existing media endpoint usable, so build it generally.

## Explicitly not in scope

Parsing, OCR, or extraction from an uploaded document. Store it first. Reading it is GRS-0030's
territory and a separate ticket.

## Done when

An advisor attaches a PDF to an engagement, sees it listed, downloads it back **byte-identical**,
and a second advisor gets a 404 for the same id. A file over the cap is refused before it is
buffered. An unsupported type is refused with a reason.
