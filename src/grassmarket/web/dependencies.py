"""FastAPI dependencies: settings, a request-scoped repository, and the authenticated principal.

The repository dependency owns the session/transaction lifecycle so routers never touch a
session directly — persistence stays behind the one layer.
"""

from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from grassmarket.auth.google_oauth import (
    GoogleOAuthClient,
    GoogleOAuthNotConfiguredError,
    build_google_client,
)
from grassmarket.auth.security import InvalidTokenError, decode_access_token
from grassmarket.auth.service import AuthService
from grassmarket.config import Settings, get_settings
from grassmarket.data.repository import Principal, Repository
from grassmarket.gtm import LsegRosterSource

_bearer = HTTPBearer(auto_error=False)


def get_app_settings(request: Request) -> Settings:
    """Settings live on app.state so tests can inject an override app."""
    return request.app.state.settings


def get_repository(request: Request) -> Iterator[Repository]:
    """Yield a repository over a request-scoped session; commit on success, roll back on error."""
    factory = request.app.state.session_factory
    session = factory()
    try:
        yield Repository(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_auth_service(
    repo: Repository = Depends(get_repository),
    settings: Settings = Depends(get_app_settings),
) -> AuthService:
    return AuthService(repo, settings)


def get_google_oauth_client(
    settings: Settings = Depends(get_app_settings),
) -> GoogleOAuthClient:
    """The Google OAuth client, or a 503 if the operator has not provisioned the credentials.
    Tests override this dependency with a fake so CI never makes a live Google call."""
    try:
        return build_google_client(settings)
    except GoogleOAuthNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_app_settings),
    repository: Repository = Depends(get_repository),
) -> Principal:
    """Decode the bearer token into a `Principal`. Any token problem is a 401 — never a silent
    pass to an unauthenticated request."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = decode_access_token(settings, credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    # The founder claim (ADR-0041) is derived here from the configured reviewer email rather than
    # read from the token. Deriving it per request means rotating GM_FOUNDER_REVIEWER_EMAIL takes
    # effect on the next call instead of waiting for every issued token to expire, and there is no
    # new claim that could be forged or go stale. Compared case-insensitively because email
    # local-part case is not identity.
    is_founder = claims.email.strip().lower() == settings.founder_reviewer_email.strip().lower()
    authenticated = Principal(
        consultant_id=UUID(claims.sub), role=claims.role, is_founder=is_founder
    )
    if claims.act_as is None:
        return authenticated

    # An act-as token (GRS-0208). The session runs as the SUBJECT — their id, their role, their
    # founder status — with the admin recorded for attribution. Rebuilt per request from the
    # subject's stored row rather than from claims, so a role change or a deleted account takes
    # effect immediately instead of living on inside an issued token.
    #
    # The admin check is repeated here even though `begin_act_as` made it: this runs on EVERY
    # request, and a token minted while its holder was an admin must stop acting the moment they
    # are not one.
    if not authenticated.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an admin may act as another consultant.",
        )
    subject = repository.get_consultant_by_id(UUID(claims.act_as))
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The consultant this session was acting as no longer exists.",
        )
    return Principal(
        consultant_id=subject.id,
        role=subject.role,
        is_founder=subject.email.strip().lower() == settings.founder_reviewer_email.strip().lower(),
        acting_admin_id=authenticated.consultant_id,
    )


# Convenience aliases used unmodified by the deferred router; falls back to get_settings if the
# app was built without state (e.g. unit tests importing a dependency in isolation).
def get_settings_default() -> Settings:
    return get_settings()


def get_lseg_roster_source() -> LsegRosterSource:
    """The LSEG roster port (GRS-0194).

    No live client is wired in this build: the connector is an interactively-authenticated operator
    tool, so an unconfigured deployment refuses the pull loudly rather than returning an empty map
    that would read as "this bank has no analysts". Tests and the operator console override this
    dependency with a real source.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="No LSEG connector is configured for this deployment, so no roster can be pulled.",
    )
