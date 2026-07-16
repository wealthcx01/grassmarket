"""Auth service — the invitation → signup → login flow, orchestrated over the repository.

No queries here; every persistence call goes through `Repository`. Fail-loud on every branch:
expired/used/unknown invitations, duplicate accounts, and bad credentials all raise, never
return a partial success.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from bcap_contracts.audit import AuditEventType
from bcap_contracts.auth import Consultant
from bcap_contracts.common import ConsultantTier, Role

from grassmarket.auth.security import (
    create_access_token,
    generate_invite_token,
    hash_invite_token,
    hash_password,
    verify_password,
)
from grassmarket.config import Settings
from grassmarket.data.repository import ConflictError, Repository


class AuthError(Exception):
    """Base auth failure."""


class InvalidCredentialsError(AuthError):
    """Login failed. Deliberately does not distinguish unknown-email from wrong-password."""


class InvalidInvitationError(AuthError):
    """The invitation is unknown, expired, or already used."""


class ForbiddenInvitationError(AuthError):
    """The inviter is not allowed to grant the requested role or tier (privilege escalation)."""


class UnprovisionedGoogleAccountError(AuthError):
    """A Google-verified email has no invited consultant. Sign-in stays invite-only (403)."""


# The role and tier a non-admin inviter may grant. Anything above these requires admin — otherwise
# any consultant could self-mint an ADMIN account (GRS-0042) and defeat the whole ownership model.
_DEFAULT_INVITE_ROLE = Role.CONSULTANT
_DEFAULT_INVITE_TIER = ConsultantTier.VENTURE_ASSOCIATE


class AuthService:
    def __init__(self, repo: Repository, settings: Settings) -> None:
        self._repo = repo
        self._settings = settings

    # -------------------------------------------------------------- invitations
    def create_invitation(
        self,
        *,
        inviter_id: UUID,
        inviter_role: Role,
        email: str,
        role: Role = Role.CONSULTANT,
        tier: ConsultantTier = ConsultantTier.VENTURE_ASSOCIATE,
        now: datetime | None = None,
    ) -> str:
        """Create an invitation and return the RAW token (delivered out of band; only its hash is
        stored). Signup is invitation-only (PRD §2).

        Only an admin may grant an elevated role or tier. A non-admin inviting anything above the
        default consultant/entry-tier is refused loud (GRS-0042) — the whole ownership model rests
        on the JWT `role`, so the invite flow must not let an unprivileged user forge it."""
        if inviter_role is not Role.ADMIN and (
            role is not _DEFAULT_INVITE_ROLE or tier is not _DEFAULT_INVITE_TIER
        ):
            raise ForbiddenInvitationError(
                "Only an admin may invite a consultant with an elevated role or tier."
            )
        issued = now or datetime.now(UTC)
        raw_token, token_hash = generate_invite_token()
        self._repo.create_invitation(
            email=email,
            token_hash=token_hash,
            role=role,
            tier=tier,
            invited_by_consultant_id=inviter_id,
            expires_at=issued + timedelta(hours=self._settings.invite_ttl_hours),
        )
        return raw_token

    def accept_invitation(
        self, *, token: str, full_name: str, password: str, now: datetime | None = None
    ) -> Consultant:
        """Redeem an invitation to create a consultant. Fails loud on unknown/expired/used."""
        moment = now or datetime.now(UTC)
        invitation = self._repo.get_invitation_by_token_hash(hash_invite_token(token))
        if invitation is None:
            raise InvalidInvitationError("Unknown invitation token.")
        if invitation.accepted_at is not None:
            raise InvalidInvitationError("Invitation has already been used.")
        expires_at = invitation.expires_at
        if expires_at.tzinfo is None:  # SQLite may return naive datetimes
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < moment:
            raise InvalidInvitationError("Invitation has expired.")

        try:
            stored = self._repo.create_consultant(
                email=invitation.email,
                full_name=full_name,
                hashed_password=hash_password(password),
                role=Role(invitation.role),
                tier=ConsultantTier(invitation.tier),
            )
        except ConflictError as exc:
            raise InvalidInvitationError(str(exc)) from exc

        self._repo.mark_invitation_accepted(invitation, accepted_at=moment)
        return stored.to_contract()

    # -------------------------------------------------------------- login
    def login(self, *, email: str, password: str) -> str:
        """Return a signed access token, or raise `InvalidCredentialsError`. Runs the password
        verification even when the email is unknown, to avoid a user-enumeration timing oracle."""
        stored = self._repo.get_consultant_by_email(email)
        if stored is None or stored.hashed_password is None:
            # Verify against a dummy hash so timing does not reveal whether the email exists — and
            # an OAuth-only account (no password hash) is a password-login miss, not a crash.
            verify_password(password, _DUMMY_HASH)
            raise InvalidCredentialsError("Invalid email or password.")
        if not stored.is_active:
            raise InvalidCredentialsError("Account is inactive.")
        if not verify_password(password, stored.hashed_password):
            raise InvalidCredentialsError("Invalid email or password.")
        self._repo.record_audit(
            actor_consultant_id=stored.id,
            event_type=AuditEventType.AUTH_LOGIN,
            resource_type="consultant",
            resource_id=stored.id,
            now=datetime.now(UTC),
        )
        return create_access_token(
            self._settings,
            consultant_id=stored.id,
            email=stored.email,
            role=stored.role,
            tier=stored.tier,
            assessor_level=stored.assessor_level,
        )

    def _resolve_google_consultant(self, *, email: str, google_sub: str):
        """Invite-only Google resolution (ADR-0024). Google has already verified `email`/`sub`; here
        we resolve a *pre-provisioned* consultant — an unknown email is refused (no auto-provision),
        an inactive account is refused, and the Google id is bound on first use."""
        stored = self._repo.get_consultant_by_email(email)
        if stored is None:
            raise UnprovisionedGoogleAccountError(
                "No Grassmarket consultant is provisioned for this Google account. "
                "Sign-in is invitation-only."
            )
        if not stored.is_active:
            raise InvalidCredentialsError("Account is inactive.")
        self._repo.bind_google_sub(stored.id, google_sub)  # set-if-null; refuse a different sub
        return stored

    def begin_google_session(self, *, email: str, google_sub: str) -> str:
        """Resolve the invited consultant, then issue a single-use, short-TTL hand-off code bound to
        them (GRS-0074). The OAuth callback carries this opaque code back to the advisory app in a
        query string — never the JWT — and the app exchanges it. Only the code's hash is stored."""
        stored = self._resolve_google_consultant(email=email, google_sub=google_sub)
        raw_code = secrets.token_urlsafe(32)
        self._repo.create_login_handoff_code(
            consultant_id=stored.id,
            code_hash=hash_invite_token(raw_code),
            expires_at=datetime.now(UTC)
            + timedelta(seconds=self._settings.login_handoff_ttl_seconds),
        )
        return raw_code

    def exchange_handoff_code(self, *, code: str, now: datetime | None = None) -> str:
        """Redeem a single-use hand-off code for the GM JWT (GRS-0074) — the only place a JWT
        crosses back to the browser, over POST, never a URL. Fail loud on unknown/expired/reused;
        on success record `AUTH_LOGIN` (the login completes here) and mint at the single point."""
        moment = now or datetime.now(UTC)
        consultant_id = self._repo.consume_login_handoff_code(
            code_hash=hash_invite_token(code), now=moment
        )
        stored = self._repo.get_consultant_by_id(consultant_id)
        if stored is None or not stored.is_active:
            raise InvalidCredentialsError("Account is inactive.")
        self._repo.record_audit(
            actor_consultant_id=stored.id,
            event_type=AuditEventType.AUTH_LOGIN,
            resource_type="consultant",
            resource_id=stored.id,
            now=moment,
        )
        return create_access_token(
            self._settings,
            consultant_id=stored.id,
            email=stored.email,
            role=stored.role,
            tier=stored.tier,
            assessor_level=stored.assessor_level,
        )


# A precomputed bcrypt hash of a random string, used only to equalise login timing on the
# unknown-email path. Not a secret.
_DUMMY_HASH = "$2b$12$abcdefghijklmnopqrstuuABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
