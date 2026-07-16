# GRS-0074 — Public-site login hand-off (Bruntsfield Capital → advisory app)

**Status:** Planned
**Loop:** Track B — Auth / SSO
**Depends on:** ADR-0024

## Why

Once Google sign-in exists (GRS-0073), the public Bruntsfield Capital marketing site needs a "LOG IN"
control that lands a consultant, authenticated, in the advisory app. Two things block a naive
hand-off today:

1. **CORS is single-origin.** `frontend_origin` is one string (`config.py:61`), wired as
   `allow_origins=[settings.frontend_origin]` at `web/app.py:74` — the public BC site origin can't
   call the API.
2. **localStorage is origin-scoped.** A token minted while the browser is on the BC site cannot be
   read by the advisory app (different origin), so the `bas.access_token` key (`frontend/lib/api.ts:64`)
   the app reads would be empty.

The fix is a **short-lived single-use code** hand-off, never a token in the URL (platform privacy
rule: no credentials/JWTs in query strings). The Google callback redirects to the advisory app with a
one-time code; the app exchanges it server-side for the real Grassmarket JWT (reusing
`create_access_token`, `auth/security.py:57`).

## What to build

- **Multi-origin CORS** (`src/grassmarket/config.py`, `src/grassmarket/web/app.py`): change
  `frontend_origin` (`config.py:61`) from a single `str` to a list of origins (e.g.
  `frontend_origins: list[str]`, env as comma-separated), and update `web/app.py:74` to
  `allow_origins=settings.frontend_origins`. Include the advisory app origin **and** the public
  Bruntsfield Capital site origin. Update `.env.example` (`GM_FRONTEND_ORIGIN` block, `.env.example:25`)
  to document the list form. Keep a back-compat read of the old single-origin var if trivial.
- **One-time-code issuance** (extend `web/routers/auth.py` + `auth/service.py`, building on the
  GRS-0073 callback): after Google verifies the `email` and `login_with_google` (`service.py`, added
  in GRS-0073) confirms an invited consultant, mint a **single-use, short-TTL** opaque code (e.g.
  `secrets.token_urlsafe`, hashed at rest like invite tokens — see `generate_invite_token` /
  `hash_invite_token`, `auth/security.py:46-54`), bound to the consultant id and an expiry (~60s).
  Store it via the repository layer (new small table + `migrations/versions/0020_login_handoff_codes.py`,
  chained after `0019_google_oauth`; all persistence stays in `data/repository.py`). The callback
  redirects to the advisory app's login route carrying only this code (`?code=...`), never the JWT.
- **Exchange endpoint** `POST /auth/session/exchange` in `web/routers/auth.py`: accept the one-time
  code, look it up, verify not-expired and not-yet-consumed, mark it consumed (fail loud on
  reuse/expiry — mirror the invitation single-use logic at `service.py:98-104`), and return a
  `TokenResponse` minted through `create_access_token` (`auth/security.py:57`). This is the only place
  a JWT crosses back to the browser, over POST, never a URL.
- **Frontend** (`frontend/app/login/page.tsx`): on load, if a `?code=` param is present, call
  `/auth/session/exchange`, store the returned token under `bas.access_token`
  (`TOKEN_KEY`, `login/page.tsx:11`), strip the code from the URL, and route to `/`. The public BC
  site's "LOG IN" simply links to `{API_BASE_URL}/auth/google/start` — no shared code, the whole
  round-trip is driven by the advisory backend.

## Evolution path (note, not build)

When the custom domain lands (O3, pre-release), session storage moves to a shared-domain httpOnly
cookie on `.bruntsfieldcapital.com` — the codebase already anticipates this (the "Holy Corner SSO"
comment at `frontend/app/login/page.tsx:8`). Design the one-time-code exchange so that swapping
localStorage for a cookie is a later, isolated change: keep the JWT server-minted and the exchange
the single hand-off seam, so only the exchange response's storage target changes.

## Acceptance / verification

- The one-time-code exchange works cross-origin end-to-end: BC-site "LOG IN" → `/auth/google/start`
  → callback → advisory app `?code=` → `POST /auth/session/exchange` → JWT stored → dashboard loads.
- The code is **single-use** (second exchange of the same code → 4xx, fail loud) and **short-TTL**
  (expired code → 4xx).
- **No JWT appears in any URL** at any step (assert the redirect carries only the opaque code).
- Multi-origin CORS: a preflight from the BC-site origin succeeds; an un-listed origin is rejected.
- New tests: exchange happy path, reuse rejection, expiry rejection, and CORS origin allow/deny.
- GRS-0073 tests and `tests/test_invitation_flow_http.py` stay green.

## Not in scope

- The httpOnly shared-domain cookie / custom-domain session store (O3 — see evolution note).
- Refresh tokens or silent re-auth.
- Any change to how the JWT itself is minted or validated (`create_access_token` /
  `decode_access_token` are reused unchanged).
- Building the public BC marketing site's markup — only the API contract the "LOG IN" link targets.
