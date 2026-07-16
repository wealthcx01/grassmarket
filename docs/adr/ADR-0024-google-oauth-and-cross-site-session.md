# ADR-0024 — Google OAuth sign-in + cross-site session (public site → advisory app)

- **Status:** Accepted (2026-07-16). Founder-directed: "log in on the public Bruntsfield Capital site → redirect to the advisory app; all consultants have Gmail."
- **Date:** 2026-07-16
- **Deciders:** Founder + engineering
- **Implements:** tickets GRS-0073 (google-oauth-signin), GRS-0074 (public-site-login-handoff).
- **Related:** the "Holy Corner SSO" direction the auth layer is already built toward (`frontend/app/login/page.tsx:8`; `bcap_contracts/auth.py` `JWTClaims`).

## Context

Sign-in today is email/password → a GM JWT (`AuthService.login` → `create_access_token`, `auth/security.py:57`), invite-only account creation, token in `localStorage`. There is no OAuth/SSO and no change-password endpoint. The founder wants Google sign-in (every consultant has a Gmail) and a flow where the **public** Bruntsfield Capital site carries the "LOG IN" entry point and hands the authenticated advisor to the **advisory app** on a different origin.

The token/claim/verification core is already SSO-shaped and fully reusable: `JWTClaims` deliberately mirrors the future Holy Corner SSO claim, so a token minted after Google verification validates through the unchanged `decode_access_token` path exactly like a password-minted one, and every `authHeaders()`/`get_current_principal`/scoping consumer works untouched. Email is the unique, lowercased natural key (`repository.py:421`), so mapping a verified Google `email` onto an existing consultant is clean.

## Decision

1. **Google OAuth = authorization-code flow, backend as the client.** New `GET /auth/google/start` (consent URL + `state`/PKCE) and `GET /auth/google/callback` (exchange code → verify Google ID token → verified `email`) in the already-mounted `web/routers/auth.py`. The callback resolves the consultant and **mints the existing GM JWT** via `create_access_token` — no downstream change.

2. **Invite-only match, no auto-provisioning.** `AuthService.login_with_google(email)` resolves an existing consultant by email; an unknown Google email gets **403**. New consultants still arrive through the existing invitation flow (which may be enhanced to "invite by email → sign in with Google"). This preserves the invitation gate that is a system non-negotiable.

3. **Bind the Google identity, allow OAuth-only accounts.** Add a nullable `google_sub` column to `ConsultantORM` (bind the Google account id, not merely trust the email on every login) and make `hashed_password` **nullable** (an OAuth-only consultant has no password). Schema is migration-driven (`app.py:61`), so this is an Alembic migration.

4. **Keep email/password** as an admin/fallback path — not removed.

5. **Cross-site hand-off via a short-lived single-use code.** A `localStorage` token is origin-scoped and cannot cross from the BC site's origin to the advisory app's. The Google callback redirects to the advisory app with a **one-time code** (single-use, short TTL); the app exchanges it for the GM JWT. **The JWT is never placed in a URL query string** (platform privacy rule + hygiene). The public BC site's "LOG IN" simply links to `/auth/google/start`.

6. **Multi-origin CORS.** `frontend_origin` is a single allowed origin today (`config.py:61`, `app.py:74`). Make it a list so the public BC site origin is also permitted.

7. **Operator provisions the Google OAuth client.** `GM_GOOGLE_CLIENT_ID` / `GM_GOOGLE_CLIENT_SECRET` / `GM_GOOGLE_REDIRECT_URI` are operator-supplied env vars (Google Cloud Console). Engineering wires the flow; **no OAuth credentials or secrets are created or committed in the repo.**

## Consequences

- New config keys, two auth endpoints, a `login_with_google` service method, a `google_sub`/nullable-password migration, multi-origin CORS, and a one-time-code exchange endpoint. Everything else (mint, verify, claims, scoping) is reused.
- **Evolution (not this ADR):** when the custom domain lands (O3, pre-release), move session storage to a **shared-domain httpOnly cookie on `.bruntsfieldcapital.com`** — the cleaner long-term substrate and the explicit Holy Corner direction. The one-time-code exchange is designed so this is a later, isolated change; until then it works on the `*.up.railway.app` origins.
- Security posture unchanged: invite-only gate preserved; no token in URLs; Google verifies the ID token signature (RS256) before we mint our own HS256 GM token.

## Alternatives considered

- **Auto-provision any Google account.** Rejected — breaks the invitation-only guarantee; a stranger's Gmail must not become a consultant.
- **Trust the email claim without `google_sub`.** Rejected — binds identity to a mutable claim; storing the stable Google subject is cheap and safer.
- **Put the JWT in the redirect URL.** Rejected — tokens in query strings leak via history/referrer/logs; the one-time code is the standard safe hand-off.
- **Go straight to a shared-domain httpOnly cookie now.** Deferred — it requires both sites on `*.bruntsfieldcapital.com` (custom domain, O3, deferred to pre-release); the one-time code is the low-regret interim that works today.
