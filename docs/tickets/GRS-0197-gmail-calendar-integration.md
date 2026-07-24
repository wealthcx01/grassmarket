# GRS-0197 — Gmail + Google Calendar integration

**Status:** Planned (2026-07-23, founder feedback items 15b and 18). **Priority:** HIGH within
Wave 5. **Loop:** founder-feedback remediation, Wave 5. Elevates the planned GRS-0112; extends
ADR-0024/ADR-0044 OAuth.

## Why

The founder: linking the per-client record to Gmail and Google Calendar "would be incredible",
and the Communication Log should be linked with advisor gmails. With GRS-0173 all advisors hold
@bruntsfield.capital Workspace accounts, so the scopes attach to accounts we manage.

## Scope

1. **Incremental OAuth (opt-in, never bundled into sign-in).** `src/grassmarket/auth/google_oauth.py`
   keeps sign-in at `scope="openid email"`, `access_type=online` (unchanged, ~85–97). Add a
   distinct connect flow on the `GoogleOAuthClient` Protocol: `connect_url(*, state, code_challenge,
   scopes) -> str` and `exchange_code_for_tokens(*, code, code_verifier) -> GoogleTokenGrant`
   (a new frozen dataclass carrying `access_token`, `refresh_token`, `expiry`, `granted_scopes`,
   `sub`). The `HttpGoogleOAuthClient` `connect_url` requests
   `scope="openid email https://www.googleapis.com/auth/gmail.readonly
   https://www.googleapis.com/auth/calendar.events"`, `access_type=offline`,
   `include_granted_scopes=true`, `prompt=consent` (to guarantee a refresh token). Decision:
   `gmail.readonly` **deliberately excludes any send scope** — the Studio reads mail, never sends
   on the advisor's behalf; `calendar.events` (not `calendar`) limits Calendar to events the Studio
   creates/updates. A fixture `FakeGoogleOAuthClient` implements the same Protocol for CI.
2. **Per-advisor token storage (server-side, encrypted).** New migration
   `migrations/versions/00xx_google_connections.py` (next free number after rebasing onto the
   merged migration head): table `google_account_connections` — id, `owner_consultant_id` (unique,
   FK), google_sub, granted_scopes (text), refresh_token_enc (text), access_token_enc (text),
   token_expiry (timestamptz), connected_at, revoked_at (nullable), created_at, updated_at. Tokens
   are encrypted at rest with the existing app secret handling (the same Fernet/secret seam used
   for refresh tokens in migration 0023); the raw tokens never appear in a contract or a log.
   Repository methods `upsert_google_connection`, `get_google_connection`,
   `revoke_google_connection` — all strictly self-scoped (`owner_consultant_id ==
   principal.consultant_id`, **no admin-all branch**, mirroring `_own_prospects`, ADR-0016).
3. **Connect / disconnect endpoints** (new router
   `src/grassmarket/web/routers/google_connect.py`, prefix `/auth/google/connect`):
   - `GET /auth/google/connect/start` → 307 redirect to `connect_url(...)`, stashing state + PKCE
     in the same signed short-TTL cookie mechanism (`sign_oauth_txn`) sign-in uses.
   - `GET /auth/google/connect/callback` → verifies the txn cookie, exchanges the code for tokens,
     `upsert_google_connection`, then 307 to `/settings#connected-accounts`. A denied/failed
     consent redirects with an error flag, never a partial connection (fail loud).
   - `POST /auth/google/connect/revoke` → 200; `revoke_google_connection` clears the stored tokens
     (sets `revoked_at`, nulls the encrypted tokens) and best-effort calls Google's token-revoke
     endpoint. Sync stops; existing synced entries are retained (they are history).
   - `GET /me/connections/google` → 200 `GoogleConnectionStatus{ connected: bool, scopes: list[str],
     connected_at: datetime | None }` (never the tokens).
4. **Comms provenance (contract widening).** `packages/bcap_contracts/.../engagements.py`
   `CommsLogEntry` gains `provenance: CommsProvenance` (new StrEnum `manual` | `synced`, default
   `manual`) and `external_ref: str | None = None` (the provider message/event id, for idempotent
   de-dup). Migration `00xx_comms_provenance.py` adds `provenance` and `external_ref` columns to
   the comms rows (default `manual`, backfilled). Regenerate the JSON schema and update the
   `CommsLogEntry` TS interface (`frontend/lib/types.ts` ~677). Synced entries are append-only and
   read-only in the UI.
5. **Prospect-level comms home.** The comms log is engagement-only today, so pre-contract threads
   have nowhere to land. Add a prospect-scoped log: the comms row gains a nullable `prospect_id`
   (exactly one of `engagement_id` / `prospect_id` is set — a check constraint, fail-loud on both
   or neither). Repository `append_prospect_comms_entry` / `list_prospect_comms` (owner-scoped);
   endpoints `POST /prospects/{id}/comms` and `GET /prospects/{id}/comms` in
   `routers/prospects.py`. Frontend: a `CommsLog` section (extracted from the engagement page into
   a shared `frontend/components/CommsLog.tsx`) is rendered on the prospect detail page. Manual
   entry stays available at both scopes; synced entries render with a `synced` provenance label
   (vs `manual`).
6. **Sync engine (seams, offline in CI).** New `src/grassmarket/integrations/google_sync.py`:
   `GmailReader` and `CalendarWriter` Protocols with httpx implementations (`HttpGmailReader`,
   `HttpCalendarWriter`) and fixture fakes. Pure orchestration functions the repository/router
   drive:
   - `sync_comms_for_advisor(principal, connection, gmail, repo, now) -> SyncSummary`: fetches
     recent messages, matches sender/recipient against the advisor's prospect and engagement
     contact emails (via existing `list_contacts`), and appends a `synced` `CommsLogEntry`
     (channel `email`, `external_ref` = Gmail message id) to the matching prospect or engagement.
     Idempotent: an entry whose `external_ref` already exists is skipped (no duplicate on re-run).
   - `create_calendar_event_for_workshop(principal, connection, calendar, workshop) -> str`:
     scheduling a workshop creates a Calendar event (advisor + prospect primary contact as
     attendees) and stores the returned event id on the workshop; reschedule/cancel push a one-way
     update/delete from the Studio (the Studio is the source of truth — inbound calendar edits are
     not read back). Wired into the workshop create/reschedule/cancel paths in
     `routers/workshops.py`.
   - Trigger: `POST /integrations/google/sync` (self-scoped, syncs the caller's own mail) plus a
     cron script `scripts/sync_google_comms.py` calling the same logic for every connected advisor.
     Decision: no in-process scheduler (no new daemon), matching the GRS-0192 cron-plus-on-demand
     pattern. The real readers/writers are constructed only in the router/script; every test uses
     the fakes.
7. **Scoping (absolute).** Synced mail is the owning advisor's alone — enforced in the repository
   (every sync path keys on `principal.consultant_id`) and tested. There is no network-wide mail
   view, **including for admins** (the connection table has no admin-all read; the sync trigger is
   self-only). Google tokens are never returned by any endpoint.

## Test plan

Backend (pytest, offline — fixture Google clients only):
- New `tests/test_google_connect.py`:
  - `connect/start` redirects to a URL carrying the gmail.readonly + calendar.events scopes and
    `access_type=offline`; sign-in's `authorization_url` still carries only `openid email`.
  - `connect/callback` with the fake client stores an encrypted connection; the raw tokens never
    appear in `GET /me/connections/google` (status only).
  - `revoke` sets `revoked_at`, nulls the tokens, and stops sync; existing synced entries remain.
  - Scoping: advisor B's `GET /me/connections/google` never reveals advisor A's connection; there
    is no admin endpoint that lists connections or tokens.
- New `tests/test_google_sync.py` (fixture `GmailReader`/`CalendarWriter`):
  - `sync_comms_for_advisor` appends `synced`, `email`-channel entries only for messages matching
    the advisor's own prospect/engagement contacts; a message to a foreign advisor's contact is
    never attached to this advisor.
  - Idempotence: a second sync over the same fixture messages adds no duplicates (`external_ref`
    de-dup).
  - **Cross-advisor negative:** advisor A's sync never writes a comms entry owned by advisor B;
    advisor B cannot read A's synced entries (403/404 on the scoped list).
  - Calendar: scheduling a workshop calls the fake `CalendarWriter` and stores the event id;
    reschedule updates it, cancel deletes it (one-way).
- `tests/test_prospect_comms.py`: prospect-level `POST`/`GET /prospects/{id}/comms` are
  owner-scoped (advisor B → 404); the exactly-one-of `prospect_id`/`engagement_id` constraint is
  enforced (a row with both or neither is refused).
- No test performs a live network call (existing CI rule).

Frontend (vitest, per-file):
- `bunx vitest run frontend/components/CommsLog.test.tsx`: renders manual and `synced` entries with
  distinct provenance labels; synced entries have no edit affordance (read-only); manual entry
  posts.
- `bunx vitest run frontend/app/settings/page.test.tsx` (Connected accounts section): shows
  "Not connected" → connect link; shows connected status + disconnect when
  `api.googleConnectionStatus` reports connected.

## Out of scope

- Sending email from the Studio (no send scope — deliberate).
- Reading inbound Calendar edits back into the Studio (one-way; Studio is source of truth).
- Any admin or network-wide mail view.
- Attachments / full-body archival of synced mail (subject + snippet + link only).
- One ticket = one branch = one PR; contract regeneration + both migrations ship in this PR.

## Acceptance

An opted-in advisor sees their client email threads (provenance-labelled `synced`, read-only) on
the prospect and engagement records, and their scheduled workshops appear as Calendar events;
opting out stops sync and leaves manual entries intact; scoping tests prove no cross-advisor mail
leakage (including no admin path); Google tokens are never exposed by any endpoint; CI runs the
whole suite with zero network access.
