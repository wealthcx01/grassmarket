# GRS-0173 — Workspace domain SSO: @bruntsfield.capital sign-in

**Status:** In review (2026-07-25) — Workspace domain auto-provisioning + login primary Google button; PR open. **Priority:** HIGH.
**Loop:** founder-feedback remediation, Wave 1. Carries ADR-0044 (amends ADR-0024).

## Why

All advisors will hold @bruntsfield.capital Google Workspace accounts. Today Google sign-in exists
(ADR-0024: PKCE, JWKS-verified, `openid email` scopes) but is invite-bound: an email the repository
does not already know is refused with a 403. That means every advisor still needs a manual invite
before their Workspace account works. The founder wants Workspace sign-in to be the primary path,
matching the Foundry Studio pattern (domain-restricted SSO with auto-provisioning).

## Scope

1. **Config** (`src/grassmarket/config.py`). Add two settings next to the existing
   `google_client_id` block (around line 100):
   - `google_workspace_domain: str | None = None`, env `GM_GOOGLE_WORKSPACE_DOMAIN`. When unset,
     behaviour is byte-for-byte today's invite-only flow. Staging/production set it to
     `bruntsfield.capital`.
   - `google_autoprovision_tier: str = "venture_associate"`, env `GM_GOOGLE_AUTOPROVISION_TIER`.
     Validated at settings load against `ConsultantTier` values with a Pydantic validator; an
     unknown tier is a startup refusal, never a default. Decision: the auto-provisioned **role is
     always `Role.CONSULTANT`** and is not configurable. Auto-provisioning must never be able to
     mint an elevated role (GRS-0042 posture, ADR-0044 point 2); promotion stays an explicit admin
     action.

2. **`src/grassmarket/auth/google_oauth.py`**:
   - `GoogleIdentity` (line 49) gains `hd: str | None = None`.
   - `_verify_id_token` (line 121) reads `claims.get("hd")` and carries it onto the returned
     `GoogleIdentity`. The `hd` claim is taken only from the JWKS-verified, audience-checked token
     claims, never from any other source (ADR-0044 point 1). No scope change: `openid email`
     stays as-is.

3. **`src/grassmarket/auth/service.py`**:
   - `_resolve_google_consultant` (line 217) gains a keyword-only `hd: str | None` parameter.
     Resolution order:
     a. `repo.get_consultant_by_email(email)` finds a consultant: unchanged path. Inactive is
        refused; `bind_google_sub` binds as today. Domain membership does not bypass the
        inactive check (a suspended advisor stays out even with a live Workspace account).
     b. No consultant, `settings.google_workspace_domain` is set, and `hd` equals it exactly
        (case-insensitive compare after `.lower()`): auto-provision via
        `repo.create_consultant(email=email, full_name=<derived>, hashed_password=None,
        role=Role.CONSULTANT, tier=ConsultantTier(settings.google_autoprovision_tier))`, then
        `repo.bind_google_sub` on the new account, then `repo.record_audit` with a new
        `AuditEventType.AUTH_ACCOUNT_AUTOPROVISIONED` event (resource: the new consultant id,
        detail naming the domain). All persistence stays inside the repository layer.
        Decision on `full_name`: derived from the email local part (dots and underscores to
        spaces, title-cased, so `john.smith` becomes "John Smith"). Reasoning: ADR-0044 keeps the
        minimal `openid email` scopes, so no verified display name is available; the advisor can
        correct it on the profile page later.
     c. No consultant and (b) does not apply (no configured domain, missing `hd`, or a different
        `hd`): raise `UnprovisionedGoogleAccountError` exactly as today (surfaced 403).
   - `begin_google_session` (line 232) gains `hd: str | None` and passes it through. The caller in
     `src/grassmarket/web/routers/auth.py` (`/auth/google/callback`, line 178) passes
     `identity.hd`.

4. **Contracts** (`packages/bcap_contracts/src/bcap_contracts/audit.py`): add
   `AUTH_ACCOUNT_AUTOPROVISIONED = "auth_account_autoprovisioned"` to `AuditEventType` (line 22).
   Regenerate JSON Schemas (`uv run python scripts/generate_schemas.py`) and commit the diff. The
   frontend TS mirror does not carry audit types, so no `frontend/lib/types.ts` change.

5. **Login page** (`frontend/app/login/page.tsx`): the Google link (line 100-106) becomes the
   primary action, styled `btn btn-primary`, labelled "Sign in with Bruntsfield Google", placed
   above the email/password form. The email/password form remains below it under a separator line
   reading "Not on a Bruntsfield account?". No behaviour change to either flow; this is layout
   and copy only, written in the GRS-0174 register.

6. **Invite flow**: untouched. It remains the path for externals (reviewer accounts,
   contractors), and the only path that can grant a non-default role or tier.

No migration is needed: `create_consultant` with `hashed_password=None` (OAuth-only account) is
already supported by the login and change-password paths (see `service.py` lines 141-149,
167-169).

## Test plan

Backend (`uv run pytest`; all offline, fake OAuth client through the existing
`GoogleOAuthClient` protocol seam):

1. `tests/test_google_oauth.py` extends:
   - `hd` verification: `_verify_id_token` surfaces `hd` from verified claims;
     a token without `hd` yields `hd=None`.
   - Auto-provision happy path: unknown `john.smith@bruntsfield.capital` with matching `hd` and
     configured domain gets a consultant (role `consultant`, tier from config, name
     "John Smith"), a bound `google_sub`, a hand-off code, and an
     `AUTH_ACCOUNT_AUTOPROVISIONED` audit event.
   - Unknown email, `hd` missing → 403 (invite-bound path).
   - Unknown email, `hd` = `other.example` → 403.
   - Matching `hd` but `GM_GOOGLE_WORKSPACE_DOMAIN` unset → 403 (feature off means today's
     behaviour exactly).
   - Existing invited consultant with a domain email: no second account created;
     `google_sub` binds; no autoprovision audit event.
   - Inactive existing domain consultant → refused, no auto-provision of a duplicate.
   - Unknown `GM_GOOGLE_AUTOPROVISION_TIER` value → settings load raises.
   - Second sign-in of an auto-provisioned account: resolves the same consultant, exactly one
     consultant row for the email.
2. `tests/test_scoping.py` (or a new scoping case in `test_google_oauth.py`): an
   auto-provisioned consultant's JWT lists zero assessments, zero prospects, zero commission
   lines, and gets 404 reading another consultant's assessment. The empty-book guarantee is
   asserted, not assumed.
3. `tests/test_auth_flow.py`: password login unchanged; an auto-provisioned (passwordless)
   account attempting password login gets `InvalidCredentialsError` semantics (401), not a crash.

Frontend: `bunx vitest run frontend/app/login/page.test.tsx` (create it): the Google action
renders as the primary button with the new label; the password form still submits.

Standing gate: pyright, tsc, ESLint, ruff, schema-validate hook all green.

## Out of scope

- Any change to PKCE, JWKS verification, the hand-off code, refresh rotation, or scopes
  (ADR-0024 stands).
- Requesting the `profile` scope or any Google Directory API integration.
- Role/tier promotion flows, offboarding automation, or session revocation on Workspace
  suspension (the JWT TTL bounds that window; ADR-0044 records it).
- Removing the invite flow or password login.

## Acceptance

A never-seen john.smith@bruntsfield.capital Workspace account signs in first time with no invite
and lands in an empty, correctly-scoped book. A non-domain unknown Google account is still refused
403. With `GM_GOOGLE_WORKSPACE_DOMAIN` unset, every current auth test passes unchanged. Scoping
tests cover the auto-provisioned consultant. Password login unchanged. The autoprovision audit
event is recorded and the JSON Schema diff for `AuditEventType` is committed.
