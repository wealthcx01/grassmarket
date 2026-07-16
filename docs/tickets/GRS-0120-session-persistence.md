# GRS-0120 — Persist the session / stop the random sign-outs

**Status:** Shipped
**Loop:** Part 2 — auth/session (ADR-0024)
**Depends on:** ADR-0024 (Google OAuth / cross-site session)
**Branch:** `grs-0120-persist-session`

## What shipped

Refresh-token rotation + an expiry-aware retry, so an active advisor is no longer signed out at the
30-minute access TTL, and the UI stops lying about auth state.

**Backend**
- `RefreshTokenORM` + migration `0023_refresh_tokens` — a long-lived (30-day, config
  `GM_JWT_REFRESH_TTL_DAYS`), single-use, rotated token; only its hash is stored; `consumed_at`
  enforces single use, `revoked_at` reserved for explicit logout.
- Repository — `create_refresh_token` + `rotate_refresh_token` (consume-on-use, fail loud on
  unknown/used/revoked/expired — mirrors the hand-off-code single-use logic).
- `auth/service.py` — `IssuedTokens` (access + refresh); `_issue_tokens` is the single mint point;
  `login` and `exchange_handoff_code` return the pair; `refresh_session` rotates a token → a fresh
  pair (a replayed token is dead once its successor is minted).
- `TokenResponse.refresh_token` + `RefreshRequest` contracts; `POST /auth/refresh` route
  (used/expired/unknown → 401, client falls back to full login).

**Frontend**
- `lib/api.ts` — `setTokens`/`getRefreshToken`; a **single-flight** `tryRefresh` (concurrent 401s
  share ONE refresh call so the single-use token isn't spent by a stampede); `request()`
  transparently refreshes and retries once on a 401 for any non-`/auth/*` call.
- `lib/session.ts` — `getSession()` treats an expired (or exp-less) token as signed-out, so the
  chrome no longer shows signed-in while every call 401s (the confusing symptom).
- `login/page.tsx` — stores both tokens via `setTokens` on password login and the Google hand-off.

## Acceptance / verification

`tests/test_auth_refresh.py` — login issues a pair; `/auth/refresh` rotates and mints a working new
access token (survives access-TTL expiry without re-login); a reused / unknown / expired refresh
token is refused loud. `frontend/lib/session.test.ts` — `getSession()` returns signed-out for an
expired / exp-less token. Invite-only + owner-scoping unchanged. Backend + frontend gates green.

## Why

Advisers report being signed out mid-work at random. Confirmed root cause: the access token has a
**30-minute TTL and no refresh** (`config.py:45` `jwt_access_ttl_minutes=30`; minted
`auth/security.py:68`, `exp` enforced on decode `:83-92`); the frontend stores it in `localStorage`
(`bas.access_token`) with **no refresh and no expiry-aware retry** (`frontend/lib/api.ts:64` — the
token getter is literally commented "(skeleton) … Loop 6 replaces this"). Worse, `getSession()` never
checks `exp` (`lib/session.ts:23-35`), so the UI *looks* signed-in while every call 401s — the
confusing symptom. Raising the TTL is only a stop-gap; this is the "Loop 6 / Holy Corner SSO" the code
already anticipates (`auth.py:1-2`), done in the ADR-0024 auth workstream.

## What to build

- **Refresh mechanism** — add refresh-token rotation (or sliding/rolling expiry) so an active advisor
  isn't kicked out. `TokenResponse` in `auth/service.py` gains a refresh token; add a new
  `/auth/refresh` route in `web/routers/auth.py`. Mint/enforce alongside the existing access token in
  `auth/security.py:68`; TTL config sits at `config.py:45`.
- **Expiry-aware retry / silent-refresh interceptor** in `frontend/lib/api.ts:64-78` — on 401 (or when
  the token is near expiry), transparently refresh and retry the call once before surfacing an error.
- **Stop the UI lying** — make `getSession()` (`frontend/lib/session.ts:23-35`) treat an expired token
  as signed-out so the chrome reflects real auth state.
- Keep **invite-only + owner-scoping** intact; no change to who can sign in, only how long they stay in.

## Acceptance / verification

- An active session demonstrably survives beyond the 30-minute access-token TTL without a manual
  re-login (refresh path exercised).
- A call made with an expired access token is silently refreshed and retried once; only a genuine
  refresh failure surfaces as signed-out.
- `getSession()` returns signed-out for an expired token — the UI no longer shows signed-in while calls
  401.

## Not in scope

- Full Holy Corner SSO handoff (this lays the ADR-0024 groundwork; HC integration is later).
- Any change to invite-only onboarding or the scoping rules.
