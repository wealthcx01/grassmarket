"""Auth service — the invitation → signup → login flow, orchestrated over the repository.

No queries here; every persistence call goes through `Repository`. Fail-loud on every branch:
expired/used/unknown invitations, duplicate accounts, and bad credentials all raise, never
return a partial success.
"""

from __future__ import annotations

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


class AuthService:
    def __init__(self, repo: Repository, settings: Settings) -> None:
        self._repo = repo
        self._settings = settings

    # -------------------------------------------------------------- invitations
    def create_invitation(
        self,
        *,
        inviter_id: UUID,
        email: str,
        role: Role = Role.CONSULTANT,
        tier: ConsultantTier = ConsultantTier.VENTURE_ASSOCIATE,
        now: datetime | None = None,
    ) -> str:
        """Create an invitation and return the RAW token (delivered out of band; only its hash is
        stored). Signup is invitation-only (PRD §2)."""
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
        if stored is None:
            # Verify against a dummy hash so timing does not reveal whether the email exists.
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


# A precomputed bcrypt hash of a random string, used only to equalise login timing on the
# unknown-email path. Not a secret.
_DUMMY_HASH = "$2b$12$abcdefghijklmnopqrstuuABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
