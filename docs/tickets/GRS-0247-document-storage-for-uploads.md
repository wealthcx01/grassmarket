# GRS-0247 — Advisors cannot upload a document anywhere

**Status:** OPEN (2026-09-02). **Priority:** HIGH. **Type:** Missing capability.
**Loop:** post-wave. **Relates to:** GRS-0030 (Path B extraction), GRS-0015 (deliverables), non-negotiable #5, #9.

## Why

The founder asked on 2026-09-02 whether we have database storage for hosting the documents
advisors upload. **We do not, because there is no upload path at all.**

Verified 2026-09-02:

- `grep -rn "UploadFile\|File(" src/grassmarket/web/routers/*.py` → **no matches.** Not one
  endpoint in the API accepts a file.
- The only `LargeBinary` column in 47 tables is `meeting_transcripts.text_ciphertext`, and that is
  **pasted text encrypted at rest**, not an uploaded file. Path B ingests a transcript the advisor
  copies in; it never took the recording or the document.
- `DeliverableORM` stores **metadata only** — its docstring is explicit: *"the .docx is regenerated
  deterministically from the finalised scoring run on download (no bytes stored)."* That is a
  deliberate and good choice for our own output. It says nothing about inbound files.

So today an advisor who has a client's annual report, an org chart, a signed engagement letter or a
board pack has nowhere to put it. It lives in their email.

## What this blocks

- **Path B is half a feature.** The advisor must transcribe or paste; they cannot hand us the file.
- **Engagement evidence has no home.** The assessment cites judgements with no attachable source.
- **The founder's own two files** (Commission Schedule v7, the ASX pack) are moved by `scp` into
  `/home/dev/inbox/grassmarket/` because the product has no way to receive them.

## Scope

1. **Decide where bytes live.** Postgres `LargeBinary` is the path of least resistance and keeps
   non-negotiable #5 intact (everything through the repository layer), but Railway Postgres is not
   a blob store and the backup/restore cost grows with every board pack. Object storage (Railway
   volume, S3-compatible) needs a signed-URL path and a second thing to scope. **Recommend:
   Postgres for v1 with a hard per-file size cap**, revisited when total stored bytes pass ~2 GB.
   Record as an ADR either way — this is exactly the cross-cutting decision ADRs exist for.
2. **`documents` table + repository methods.** Owner-scoped (`owner_consultant_id`) like every
   other table, optional `engagement_id` / `prospect_id` / `assessment_id`, plus filename, media
   type, byte size, SHA-256, uploader and provenance (ADR-0029). Scoping tests from day one
   (non-negotiable #9) — an advisor must not read another's upload.
3. **Upload + download endpoints.** Size cap, media-type allowlist, and a fail-loud refusal on
   anything else. No silent truncation, no "unknown type, stored anyway".
4. **Encrypt at rest**, reusing the transcript key path — client documents are at least as
   sensitive as transcripts.
5. **Retention and deletion.** ADR-0047 says production records are not deletable; decide now
   whether an uploaded document is such a record or is advisor-owned scratch. They are not the
   same and guessing later is how GRS-0246 happened.
6. **UI**: attach on the engagement, list with size/date/uploader, download, remove.

## Not in scope

Parsing, OCR or extraction from the uploaded file. Store it first; reading it is GRS-0030's problem
and a separate ticket.

## Done when

An advisor attaches a PDF to an engagement, sees it listed, downloads it back byte-identical, and a
second advisor gets a 404 for the same id.
