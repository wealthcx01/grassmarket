"""Auth contracts — the JWT claim shape mirrors the future Holy Corner SSO (PRD §2), so the
token an advisor carries today validates unchanged once Holy Corner issues it.

`Consultant` is the *public* shape — it never carries the password hash. The hash lives only in
the Grassmarket storage model, never in a contract that could be serialised to a client.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from bcap_contracts.base import ResourceBase
from bcap_contracts.common import AssessorLevel, ConsultantTier, Role


class JWTClaims(BaseModel):
    """Decoded access-token claims. `sub` is the consultant id — the principal the repository
    layer scopes every query to."""

    model_config = ConfigDict(extra="forbid")

    sub: str = Field(description="Subject: the consultant id (stringified UUID).")
    email: EmailStr
    role: Role
    tier: ConsultantTier
    assessor_level: AssessorLevel
    iss: str = Field(description="Issuer, e.g. advisors.bruntsfieldcapital.com.")
    aud: str = Field(description="Audience, e.g. bruntsfield.")
    iat: int = Field(description="Issued-at (unix seconds).")
    exp: int = Field(description="Expiry (unix seconds).")


class Consultant(ResourceBase):
    """Public consultant resource — NO password material."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    full_name: str = Field(min_length=1)
    role: Role = Role.CONSULTANT
    tier: ConsultantTier = ConsultantTier.VENTURE_ASSOCIATE
    assessor_level: AssessorLevel = AssessorLevel.TRAINED
    is_active: bool = True


class Invitation(ResourceBase):
    """An invitation to join the network. Signup is invitation-only (PRD §2). The raw token is
    never stored — only its hash — and is delivered out of band."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    role: Role
    tier: ConsultantTier
    invited_by_consultant_id: UUID
    expires_at: datetime
    accepted_at: datetime | None = None


# --- Request/response payloads (the auth router surface) ---


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"


class AcceptInvitationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=1)
    full_name: str = Field(min_length=1)
    password: str = Field(min_length=12, description="Minimum 12 characters (fail-loud on weak).")
