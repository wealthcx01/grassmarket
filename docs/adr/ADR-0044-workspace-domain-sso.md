# ADR-0044 — Workspace domain SSO: @bruntsfield.capital auto-provisioning

- **Status:** Proposed (2026-07-23). Founder-directed (feedback 23/07/2026, item 1); ratifies
  with GRS-0173. Amends ADR-0024 (Google OAuth, invite-bound).
- **Deciders:** Founder (identity model), Engineering (implementation).
- **Normative source:** ADR-0024 (OAuth architecture — PKCE, JWKS verification, hand-off code,
  minimal scopes), non-negotiable #9 (data scoping), GRS-0042 (privilege-escalation guards).

## Context

All advisors will hold @bruntsfield.capital Google Workspace accounts. ADR-0024 built Google
sign-in but bound it to the invite list: an unknown email is refused. That leaves a manual
invite step in front of every advisor whose identity the Workspace already vouches for. The
founder wants the Foundry Studio pattern: domain-restricted SSO as the primary path. (gbrain
was not available to consult; the standard Workspace pattern — hosted-domain verification with
auto-provisioning — is what a Foundry-style setup uses, and is what this ADR adopts.)

## Decision

1. **Domain sign-in:** an ID token whose verified `hd` claim equals the configured Workspace
   domain (`GM_GOOGLE_WORKSPACE_DOMAIN=bruntsfield.capital`) authenticates as a Bruntsfield
   consultant. The `hd` claim is read from the JWKS-verified token only — never from the
   userinfo endpoint or an unverified source.
2. **Auto-provisioning:** a first-time domain sign-in creates the consultant with configured
   default role and tier and records an audit event. Elevated roles are never auto-granted —
   promotion stays an explicit admin action (GRS-0042 posture).
3. **Everything else in ADR-0024 stands:** PKCE, minimal `openid email` scopes, the single-use
   hand-off code, refresh rotation. Invite flow and password login remain for non-domain
   accounts; unknown non-domain Google accounts are still refused.

## Consequences

- Advisor onboarding is: create the Workspace account, sign in — no invite step.
- Access control for the domain delegates to Workspace admin (offboarding = suspending the
  Google account; the JWT TTL bounds the residual window).
- Scoping guarantees are unchanged and tested for auto-provisioned accounts: a new consultant
  sees an empty book.
