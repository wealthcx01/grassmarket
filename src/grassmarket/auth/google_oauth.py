"""Google OAuth authorization-code client + the OAuth-transaction cookie (ADR-0024, GRS-0073).

The backend is the OAuth client: it builds the consent URL (with `state` + PKCE), exchanges the
authorization code for Google's ID token, verifies that token's RS256 signature against Google's
JWKS, and returns the verified `email`/`sub`. It then mints the *existing* Grassmarket JWT — Google
proves who you are; the invite-only match (in `AuthService.login_with_google`) decides whether you
get a token.

Fail-loud throughout: an unconfigured OAuth client refuses (never a weak default); a token that
fails signature/`aud`/`iss`/`exp`/`email_verified` raises, never returns a truthy-but-unverified
identity. The real client makes live HTTP calls (token exchange + JWKS); tests inject a fake through
the `GoogleOAuthClient` protocol so CI stays offline.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from urllib.parse import urlencode

import httpx
import jwt

from grassmarket.config import Settings

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"  # noqa: S105 - a public URL, not a secret
GOOGLE_JWKS_URI = "https://www.googleapis.com/oauth2/v3/certs"
# Google issues the ID token under either form of the issuer claim.
GOOGLE_ISSUERS = frozenset({"https://accounts.google.com", "accounts.google.com"})
# The OAuth transaction (state + PKCE verifier) lives in a signed cookie for this long — long enough
# to complete the consent round-trip, short enough to bound replay.
_TXN_TTL_SECONDS = 600
_TXN_TYPE = "google_oauth_txn"


class GoogleOAuthError(Exception):
    """A Google OAuth step failed (token exchange, verification, or a rejected identity)."""


class GoogleOAuthNotConfiguredError(GoogleOAuthError):
    """The Google OAuth client env vars are not provisioned — refuse the flow (surfaced as 503)."""


@dataclass(frozen=True)
class GoogleIdentity:
    """A Google-verified identity. Only produced after a valid ID-token verification."""

    email: str
    email_verified: bool
    sub: str


def pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) for PKCE S256 (RFC 7636)."""
    verifier = secrets.token_urlsafe(48)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest())
        .rstrip(b"=")
        .decode("ascii")
    )
    return verifier, challenge


class GoogleOAuthClient(Protocol):
    """The seam tests replace with a fake so no live Google call happens in CI."""

    def authorization_url(self, *, state: str, code_challenge: str) -> str: ...

    def exchange_code(self, *, code: str, code_verifier: str) -> GoogleIdentity: ...


@dataclass(frozen=True)
class HttpGoogleOAuthClient:
    """The real client. Live HTTP for token exchange + JWKS-verified ID token."""

    client_id: str
    client_secret: str
    redirect_uri: str

    def authorization_url(self, *, state: str, code_challenge: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "online",
            "prompt": "select_account",
        }
        return f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}"

    def exchange_code(self, *, code: str, code_verifier: str) -> GoogleIdentity:
        try:
            resp = httpx.post(
                GOOGLE_TOKEN_ENDPOINT,
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code",
                    "code_verifier": code_verifier,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise GoogleOAuthError(f"Google token exchange failed: {exc}") from exc
        id_token = resp.json().get("id_token")
        if not id_token:
            raise GoogleOAuthError("Google token response carried no id_token.")
        return self._verify_id_token(id_token)

    def _verify_id_token(self, id_token: str) -> GoogleIdentity:
        try:
            signing_key = jwt.PyJWKClient(GOOGLE_JWKS_URI).get_signing_key_from_jwt(id_token)
            claims = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id,
                options={"require": ["exp", "iat", "aud", "iss", "sub"]},
            )
        except jwt.InvalidTokenError as exc:
            raise GoogleOAuthError(f"Google ID token failed verification: {exc}") from exc
        # PyJWT accepts only one issuer string; Google uses two forms, so check issuer here.
        if claims.get("iss") not in GOOGLE_ISSUERS:
            raise GoogleOAuthError(f"Unexpected ID-token issuer: {claims.get('iss')!r}.")
        email = claims.get("email")
        if not email:
            raise GoogleOAuthError("Google ID token carried no email claim.")
        if not claims.get("email_verified", False):
            raise GoogleOAuthError("Google email is not verified.")
        return GoogleIdentity(email=email, email_verified=True, sub=str(claims["sub"]))


def build_google_client(settings: Settings) -> GoogleOAuthClient:
    """Construct the real client, or refuse loud if the operator has not provisioned the app."""
    if not (
        settings.google_client_id and settings.google_client_secret and settings.google_redirect_uri
    ):
        raise GoogleOAuthNotConfiguredError(
            "Google OAuth is not configured. Set GM_GOOGLE_CLIENT_ID / GM_GOOGLE_CLIENT_SECRET / "
            "GM_GOOGLE_REDIRECT_URI (operator-provisioned) to enable Google sign-in."
        )
    return HttpGoogleOAuthClient(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        redirect_uri=settings.google_redirect_uri,
    )


# --- the OAuth-transaction cookie (state + PKCE verifier), signed with the app's JWT secret ---


def sign_oauth_txn(settings: Settings, *, state: str, code_verifier: str) -> str:
    """Sign an opaque, short-TTL cookie carrying the state + PKCE verifier. Same HS256 secret as the
    access token, but a distinct `typ` so the two can never be confused (and it carries no `aud`/
    `iss`, which `decode_access_token` requires)."""
    now = datetime.now(UTC)
    payload = {
        "typ": _TXN_TYPE,
        "state": state,
        "cv": code_verifier,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=_TXN_TTL_SECONDS)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def verify_oauth_txn(settings: Settings, cookie: str) -> tuple[str, str]:
    """Return (state, code_verifier) from a valid transaction cookie, or raise. Fail loud on
    tamper/expiry/wrong-type — a bad cookie is a refused login, never a bypass."""
    try:
        payload = jwt.decode(
            cookie,
            settings.jwt_secret,
            algorithms=["HS256"],
            options={"require": ["exp", "iat"]},
        )
    except jwt.InvalidTokenError as exc:
        raise GoogleOAuthError(f"Invalid OAuth transaction: {exc}") from exc
    if payload.get("typ") != _TXN_TYPE:
        raise GoogleOAuthError("OAuth transaction cookie has the wrong type.")
    state, verifier = payload.get("state"), payload.get("cv")
    if not state or not verifier:
        raise GoogleOAuthError("OAuth transaction cookie is missing state/verifier.")
    return str(state), str(verifier)
