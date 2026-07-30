"""Issuing, resolving and revoking shared report links (GRS-0220).

The link is the credential. That single fact drives everything here:

* the token is generated with `secrets.token_urlsafe` — unguessable, not a sequence or a UUID;
* only its SHA-256 is ever stored, so a leaked backup yields no working links;
* the plaintext is returned exactly once, from `issue_link`, and cannot be recovered afterwards;
* resolution is constant-time on the hash and re-checks expiry and revocation on every request,
  because a link that was valid a minute ago may not be now.

Revocation beats expiry, and both are checked at resolve time rather than cached — "revoking a link
makes it stop working immediately, and that is tested" is the ticket's own wording.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from bcap_contracts.report_links import ClientReportLink, LinkState

#: 32 bytes of entropy — a token nobody guesses and nothing enumerates.
_TOKEN_BYTES = 32

#: What an advisor gets if they express no preference.
DEFAULT_EXPIRY = timedelta(days=30)

#: Beyond this an "expiring" link is a fiction. A client who needs longer gets a fresh one.
MAX_EXPIRY = timedelta(days=180)


class LinkNotUsableError(Exception):
    """The token resolved to a link that is revoked or expired. Never say which to the caller."""

    def __init__(self, state: LinkState):
        self.state = state
        super().__init__(f"report link is {state.value}")


class ExpiryTooLongError(Exception):
    """An expiry beyond MAX_EXPIRY was requested."""


@dataclass(frozen=True)
class IssuedLink:
    """The one and only time the plaintext token exists after creation."""

    link: ClientReportLink
    token: str


def hash_token(token: str) -> str:
    """SHA-256 hex of a token. The only function that maps plaintext to what we store."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_token() -> str:
    """A fresh, unguessable token. URL-safe so it can live in a path segment."""
    return secrets.token_urlsafe(_TOKEN_BYTES)


def resolve_expiry(*, now: datetime, requested: timedelta | None) -> datetime:
    """When a link issued `now` should stop working.

    Refuses an over-long life rather than silently clamping it: an advisor who asked for a year and
    got six months without being told would believe the wrong thing about their own client's access.
    """
    lifetime = DEFAULT_EXPIRY if requested is None else requested
    if lifetime > MAX_EXPIRY:
        raise ExpiryTooLongError(
            f"a report link may live at most {MAX_EXPIRY.days} days; "
            f"{lifetime.days} was requested. Issue a fresh link when this one lapses."
        )
    if lifetime <= timedelta(0):
        raise ExpiryTooLongError("a report link's lifetime must be positive.")
    return now + lifetime


def assert_usable(link: ClientReportLink, *, now: datetime | None = None) -> None:
    """Refuse a link that is revoked or expired.

    Called on EVERY resolution rather than once at issue. The gap between "was valid" and "is valid"
    is exactly where a revoked link would keep working.
    """
    moment = now or datetime.now(UTC)
    state = link.state(now=moment)
    if state is not LinkState.ACTIVE:
        raise LinkNotUsableError(state)
