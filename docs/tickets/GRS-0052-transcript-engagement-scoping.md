# GRS-0052 — Validate the engagement a transcript is attached to

- **Loop:** 6 (Path B meeting intelligence)
- **Status:** Fixed — from the 2026-07-14 audit backlog (GRS-0049, API finding #5).
- **Severity:** Low — a scoping smell (dangling/foreign reference), not a cross-tenant read leak.
- **Normative source:** CLAUDE.md #9 (data scoping is absolute, enforced in the repository layer).

## Problem

`ingest_text` / `ingest_media` passed the caller-supplied `engagement_id` straight into
`_store_transcript`, which stored it with no ownership check. A consultant could attach their own
transcript to another consultant's (or a non-existent) `engagement_id` — no foreign data is *read*,
but it creates a dangling/foreign reference inconsistent with every other link in the codebase
(which all go through `_require_engagement` / `get_engagement`).

## Change

- `_store_transcript` calls `self._require_engagement(principal, engagement_id)` when an
  `engagement_id` is supplied — a missing or cross-owner engagement raises `NotFoundError` /
  `ScopeViolationError` (kept in the repository layer, like every other link).
- Both ingest routes map those to a 404 ("Engagement not found."), never revealing another owner's
  engagement.

## Exit criteria

- Attaching a transcript to one's own engagement succeeds and is recorded; a missing or cross-owner
  `engagement_id` is 404 with nothing stored — pinned by `test_transcript_engagement_link_is_scoped`.
