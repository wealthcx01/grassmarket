"""Auth primitives: password hashing (bcrypt), JWT encode/decode (Holy Corner claim shape),
and invitation-token generation.

Fail-loud: token decode raises `InvalidTokenError` on any problem (expiry, bad signature, wrong
audience/issuer) — never returns an unauthenticated-but-truthy result.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
import jwt
from bcap_contracts.auth import JWTClaims
from bcap_contracts.common import AssessorLevel, ConsultantTier, Role

from grassmarket.config import Settings

# bcrypt truncates silently at 72 bytes; we refuse over-long inputs rather than truncate.
_BCRYPT_MAX_BYTES = 72


class InvalidTokenError(Exception):
    """A token failed validation. Authentication is refused."""


def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > _BCRYPT_MAX_BYTES:
        raise ValueError("Password exceeds 72 bytes; refuse rather than silently truncate.")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    if len(password.encode("utf-8")) > _BCRYPT_MAX_BYTES:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        # A malformed stored hash is a verification failure, never an exception that reads as auth.
        return False


def generate_invite_token() -> tuple[str, str]:
    """Return (raw_token, token_hash). Only the hash is stored; the raw token is delivered out of
    band and never persisted."""
    raw = secrets.token_urlsafe(32)
    return raw, hash_invite_token(raw)


def hash_invite_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def create_access_token(
    settings: Settings,
    *,
    consultant_id: UUID,
    email: str,
    role: Role,
    tier: ConsultantTier,
    assessor_level: AssessorLevel,
    now: datetime | None = None,
) -> str:
    issued = now or datetime.now(UTC)
    expires = issued + timedelta(minutes=settings.jwt_access_ttl_minutes)
    payload = {
        "sub": str(consultant_id),
        "email": email,
        "role": role.value,
        "tier": tier.value,
        "assessor_level": assessor_level.value,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(issued.timestamp()),
        "exp": int(expires.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(settings: Settings, token: str) -> JWTClaims:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "sub", "aud", "iss"]},
        )
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError(str(exc)) from exc
    try:
        return JWTClaims(**payload)
    except Exception as exc:  # pydantic validation error → refuse, never pass a malformed claim
        raise InvalidTokenError(f"Token claims failed contract validation: {exc}") from exc
