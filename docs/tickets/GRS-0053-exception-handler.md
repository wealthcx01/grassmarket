# GRS-0053 — Global exception safety net + controlled decrypt failure

- **Loop:** 6 (hardening)
- **Status:** Fixed — from the 2026-07-14 audit backlog (GRS-0049, API finding #3).
- **Severity:** Low — a few uncaught paths surfaced as bare 500s (not a detail leak).
- **Normative source:** CLAUDE.md #3 (fail loud, but cleanly).

## Problem

`web/app.py` registered no exception handlers. A `RepositoryError` a route forgot to catch, and a
transcript decrypt failure (`TranscriptCipherError` from key rotation / corrupt ciphertext on a
list/get), both surfaced as a generic uncaught 500 rather than their correct status.

## Change

`create_app` now registers two safety-net handlers (routes that already translate these still win —
the handlers only fire for what slips through):

- `RepositoryError` → `ScopeViolationError` maps to 404 ("Not found.", never confirming existence),
  `NotFoundError` to 404, conflict-family errors (`ConflictError` / `WorkshopStateError` /
  `EngagementLinkError`) to 409, and any other to a generic 500.
- `TranscriptCipherError` → a controlled 500 ("A stored transcript could not be decrypted.") — never
  an uncaught traceback, and never the raw crypto detail.

## Exit criteria

- An uncaught `ScopeViolationError` is 404 and a `ConflictError` is 409; a corrupted transcript
  ciphertext yields a controlled 500 with no crypto internals — pinned by `test_error_handling.py`.
- Existing per-route error mapping is unchanged (regression suite green).
