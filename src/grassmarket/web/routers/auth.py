"""Auth router — login, invitation redemption, invitation creation, and the current identity."""

from __future__ import annotations

import secrets

from bcap_contracts.auth import (
    AcceptInvitationRequest,
    Consultant,
    LoginRequest,
    TokenResponse,
)
from bcap_contracts.common import ConsultantTier, Role
from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr

from grassmarket.auth.google_oauth import (
    GoogleOAuthClient,
    GoogleOAuthError,
    pkce_pair,
    sign_oauth_txn,
    verify_oauth_txn,
)
from grassmarket.auth.service import (
    AuthService,
    ForbiddenInvitationError,
    InvalidCredentialsError,
    InvalidInvitationError,
    UnprovisionedGoogleAccountError,
)
from grassmarket.config import Settings
from grassmarket.data.repository import ConflictError, Principal, Repository
from grassmarket.web.dependencies import (
    get_app_settings,
    get_auth_service,
    get_current_principal,
    get_google_oauth_client,
    get_repository,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# The signed OAuth-transaction cookie (state + PKCE verifier). Path-scoped to /auth, httpOnly, and
# SameSite=Lax so it survives Google's top-level redirect back to the callback.
_OAUTH_TXN_COOKIE = "gm_oauth_txn"


class CreateInvitationRequest(BaseModel):
    email: EmailStr
    role: Role = Role.CONSULTANT
    tier: ConsultantTier = ConsultantTier.VENTURE_ASSOCIATE


class CreateInvitationResponse(BaseModel):
    email: EmailStr
    token: str  # raw invite token, delivered out of band; never stored


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, auth: AuthService = Depends(get_auth_service)) -> TokenResponse:
    try:
        token = auth.login(email=payload.email, password=payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=token)


@router.post("/accept-invitation", response_model=Consultant, status_code=status.HTTP_201_CREATED)
def accept_invitation(
    payload: AcceptInvitationRequest, auth: AuthService = Depends(get_auth_service)
) -> Consultant:
    try:
        return auth.accept_invitation(
            token=payload.token, full_name=payload.full_name, password=payload.password
        )
    except InvalidInvitationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/invitations", response_model=CreateInvitationResponse, status_code=status.HTTP_201_CREATED
)
def create_invitation(
    payload: CreateInvitationRequest,
    principal: Principal = Depends(get_current_principal),
    auth: AuthService = Depends(get_auth_service),
) -> CreateInvitationResponse:
    """Authenticated consultants invite others. The raw token is returned once for out-of-band
    delivery (email integration is a later loop). Only an admin may grant an elevated role/tier."""
    try:
        raw_token = auth.create_invitation(
            inviter_id=principal.consultant_id,
            inviter_role=principal.role,
            email=payload.email,
            role=payload.role,
            tier=payload.tier,
        )
    except ForbiddenInvitationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return CreateInvitationResponse(email=payload.email, token=raw_token)


@router.get("/me", response_model=Consultant)
def me(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
) -> Consultant:
    stored = repo.get_consultant_by_id(principal.consultant_id)
    if stored is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultant not found.")
    return stored.to_contract()


# --- Google OAuth (ADR-0024, GRS-0073) --------------------------------------------------------


@router.get("/google/start")
def google_start(
    settings: Settings = Depends(get_app_settings),
    client: GoogleOAuthClient = Depends(get_google_oauth_client),
) -> RedirectResponse:
    """Begin the authorization-code flow: build Google's consent URL (with `state` + PKCE) and
    redirect there, stashing the state + PKCE verifier in a signed, short-TTL cookie the callback
    validates. The public site's "LOG IN" simply links here."""
    state = secrets.token_urlsafe(24)
    verifier, challenge = pkce_pair()
    consent_url = client.authorization_url(state=state, code_challenge=challenge)
    response = RedirectResponse(consent_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    response.set_cookie(
        _OAUTH_TXN_COOKIE,
        sign_oauth_txn(settings, state=state, code_verifier=verifier),
        max_age=600,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path="/auth",
    )
    return response


@router.get("/google/callback")
def google_callback(
    code: str,
    state: str,
    settings: Settings = Depends(get_app_settings),
    auth: AuthService = Depends(get_auth_service),
    client: GoogleOAuthClient = Depends(get_google_oauth_client),
    gm_oauth_txn: str | None = Cookie(default=None),
) -> RedirectResponse:
    """Google's redirect target: validate `state` against the signed cookie, exchange the code for a
    Google-verified identity, resolve the invited consultant, mint the GM JWT, and hand it to the
    advisory app. The JWT rides back in the URL **fragment** (never a query string; not sent to the
    server) — GRS-0074 replaces this with a one-time code + `/auth/session/exchange` for the
    cross-origin case."""
    if not gm_oauth_txn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing OAuth transaction."
        )
    try:
        cookie_state, verifier = verify_oauth_txn(settings, gm_oauth_txn)
    except GoogleOAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not secrets.compare_digest(state, cookie_state):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth state mismatch.")
    try:
        identity = client.exchange_code(code=code, code_verifier=verifier)
    except GoogleOAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    try:
        token = auth.login_with_google(email=identity.email, google_sub=identity.sub)
    except UnprovisionedGoogleAccountError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except ConflictError as exc:  # email already bound to a different Google identity
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    response = RedirectResponse(
        f"{settings.frontend_origin}/login#access_token={token}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    response.delete_cookie(_OAUTH_TXN_COOKIE, path="/auth")
    return response
