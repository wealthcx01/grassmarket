# GRS-0073 — Google OAuth sign-in (backend as the client)

**Status:** Planned
**Loop:** Track B — Auth / SSO
**Depends on:** ADR-0024

## Why

Login is invitation-only email/password today (`AuthService.login`, `auth/service.py:121`). The
advisory network wants "Sign in with Google" so consultants use their existing Google identity
instead of a Grassmarket-specific password. The chosen approach (ADR-0024) is the OAuth
**authorization-code** flow with the **backend as the OAuth client**: Google verifies identity, the
backend mints the *existing* Grassmarket JWT via the single mint point `create_access_token`
(`auth/security.py:57`). Nothing downstream changes — the same Holy-Corner-shaped `JWTClaims`
(`packages/bcap_contracts/src/bcap_contracts/auth.py`) and `decode_access_token`
(`auth/security.py:83`) verify a Google-originated session identically. Sign-in stays invite-only:
Google proves *who* you are, but only a pre-provisioned consultant may get a token.

## What to build

- **Config** (`src/grassmarket/config.py`, `.env.example`): add `GM_GOOGLE_CLIENT_ID`,
  `GM_GOOGLE_CLIENT_SECRET`, `GM_GOOGLE_REDIRECT_URI` as `Settings` fields (follow the existing
  `Field(validation_alias=AliasChoices(...))` pattern at `config.py:43-63`). The **operator**
  provisions the OAuth client in Google Cloud Console and supplies these as env vars — this ticket
  MUST NOT create credentials or embed any secret. Mirror the three vars into `.env.example` under a
  new `# --- Google OAuth ---` block with placeholder values only.
- **Endpoints** in `src/grassmarket/web/routers/auth.py` (router already mounted at
  `web/app.py:81`):
  - `GET /auth/google/start` — build the Google consent URL with `state` + PKCE
    (`code_challenge`); return a redirect (or the URL). Persist the `state`/`code_verifier` for the
    callback to validate (short-TTL server-side store or signed cookie — fail loud on mismatch).
  - `GET /auth/google/callback` — validate `state`, exchange the `code` at Google's token endpoint
    (using client id/secret + `code_verifier`), verify the returned Google **ID token** (signature,
    `aud` = our client id, `iss`, `exp`), and extract the verified `email` (require
    `email_verified`).
- **`AuthService.login_with_google(email)`** in `src/grassmarket/auth/service.py`, beside `login`
  (`service.py:121`): invite-only email match — resolve the consultant via
  `get_consultant_by_email` (`data/repository.py:421`; email is unique + lowercased). Unknown email
  → raise a new `UnprovisionedGoogleAccountError` surfaced as **403** (NO auto-provision).
  Inactive account → same refusal as `login`. On success, record an `AUTH_LOGIN` audit event exactly
  as `login` does (`service.py:133`) and return `create_access_token(...)` — reuse the existing mint
  point, do not build a second one.
- **Alembic migration** `migrations/versions/0019_google_oauth.py` (schema is migration-driven —
  `run_migrations` at `web/app.py:61`; chain `down_revision = "0018_audit_events"`): add a nullable
  `google_sub` column to `consultants` and make `hashed_password` nullable (OAuth-only accounts have
  no password). Mirror both onto `ConsultantORM` (`data/models.py:39` — `hashed_password` at
  `models.py:45` becomes `nullable=True`; add `google_sub: Mapped[str | None]`, unique+nullable).
- **Frontend** `frontend/app/login/page.tsx`: add a "Sign in with Google" button that navigates to
  `{API_BASE_URL}/auth/google/start`. On the app's return, store the returned token under the
  existing key `bas.access_token` (`TOKEN_KEY`, `login/page.tsx:11` / `frontend/lib/api.ts:64`) so
  the rest of the app authenticates unchanged. Keep the email/password form as an admin/fallback
  path.

## Acceptance / verification

- An OAuth round-trip against a **test** Google client yields a Grassmarket JWT that
  `decode_access_token` accepts (correct `iss`/`aud`, valid `JWTClaims`).
- Unknown (non-provisioned) verified Google email → **403**, no consultant row created.
- Existing email/password `login` still works; `tests/test_invitation_flow_http.py` stays green.
- New tests: the `/auth/google/callback` happy path (mock Google token exchange + ID-token
  verification, no live calls per CI rules), the invite-only 403 gate, `state`/PKCE mismatch is
  refused, and an inactive account is refused.
- `hashed_password` nullable migration applies cleanly and round-trips a password login (password
  accounts still have a hash).

## Not in scope

- Cross-origin / public-site hand-off and multi-origin CORS — GRS-0074.
- Auto-provisioning consultants from a Google Workspace domain (stays invite-only).
- Refresh tokens / httpOnly-cookie sessions — the token still lives in `localStorage` (Loop 6 /
  the custom-domain SSO work replaces that; see GRS-0074 evolution note).
- Linking a Google identity to an existing password account via UI (`google_sub` column is added
  now but populated later).
