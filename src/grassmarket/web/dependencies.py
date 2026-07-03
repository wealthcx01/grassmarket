"""FastAPI dependencies: settings, a request-scoped repository, and the authenticated principal.

The repository dependency owns the session/transaction lifecycle so routers never touch a
session directly — persistence stays behind the one layer.
"""

from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from grassmarket.auth.security import InvalidTokenError, decode_access_token
from grassmarket.auth.service import AuthService
from grassmarket.config import Settings, get_settings
from grassmarket.data.repository import Principal, Repository

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


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_app_settings),
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
    return Principal(consultant_id=UUID(claims.sub), role=claims.role)


# Convenience aliases used unmodified by the deferred router; falls back to get_settings if the
# app was built without state (e.g. unit tests importing a dependency in isolation).
def get_settings_default() -> Settings:
    return get_settings()
