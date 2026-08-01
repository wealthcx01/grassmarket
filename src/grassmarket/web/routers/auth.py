"""Auth router — login, invitation redemption, invitation creation, and the current identity."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from uuid import UUID

from bcap_contracts.auth import (
    AcceptInvitationRequest,
    ChangePasswordRequest,
    Consultant,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from bcap_contracts.common import ConsultantTier, Role
from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, EmailStr

from grassmarket.auth.google_oauth import (
    GoogleOAuthClient,
    GoogleOAuthError,
    pkce_pair,
    sign_oauth_txn,
    verify_oauth_txn,
)
from grassmarket.auth.security import create_access_token
from grassmarket.auth.service import (
    AuthService,
    ForbiddenInvitationError,
    InvalidCredentialsError,
    InvalidInvitationError,
    UnprovisionedGoogleAccountError,
)
from grassmarket.config import Settings
from grassmarket.data.repository import (
    ConflictError,
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
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
        tokens = auth.login(email=payload.email, password=payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    payload: RefreshRequest, auth: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Rotate a refresh token for a new access + refresh pair (GRS-0120), so an active advisor is
    not signed out at the 30-minute access TTL. A used/expired/unknown refresh token is refused
    loud — the client then falls back to a full re-login."""
    try:
        tokens = auth.refresh_session(refresh_token=payload.refresh_token)
    except (NotFoundError, ConflictError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token)


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


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    principal: Principal = Depends(get_current_principal),
    auth: AuthService = Depends(get_auth_service),
) -> None:
    """Self-scoped password change (GRS-0148d) — a signed-in advisor changes only their own
    password. A wrong current password / OAuth-only account surfaces as 401, mirroring login."""
    try:
        auth.change_password(
            consultant_id=principal.consultant_id,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


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
        handoff_code = auth.begin_google_session(
            email=identity.email, google_sub=identity.sub, hd=identity.hd
        )
    except UnprovisionedGoogleAccountError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except ConflictError as exc:  # email already bound to a different Google identity
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    # Carry ONLY the opaque one-time code back to the advisory app — never the JWT (ADR-0024). The
    # app exchanges it server-side via POST /auth/session/exchange.
    response = RedirectResponse(
        f"{settings.frontend_origin}/login?code={handoff_code}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    response.delete_cookie(_OAUTH_TXN_COOKIE, path="/auth")
    return response


class ExchangeSessionRequest(BaseModel):
    code: str


@router.post("/session/exchange", response_model=TokenResponse)
def exchange_session(
    payload: ExchangeSessionRequest, auth: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Exchange a single-use login hand-off code for the GM JWT (GRS-0074). The only place a JWT
    crosses back to the browser, over POST — never a URL. Reuse/expiry is refused loud."""
    try:
        tokens = auth.exchange_handoff_code(code=payload.code)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ConflictError as exc:  # already used or expired
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token)


class ActAsResponse(BaseModel):
    """The narrowed session, plus who it is for — the banner needs a name, not a UUID."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"
    subject_consultant_id: UUID
    subject_name: str
    subject_email: str


@router.post("/act-as/{consultant_id}", response_model=ActAsResponse)
def start_act_as(
    consultant_id: UUID,
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
    settings: Settings = Depends(get_app_settings),
) -> ActAsResponse:
    """Open an admin session scoped to one consultant (GRS-0208).

    No refresh token is issued. An act-as session is deliberately short-lived and non-renewable:
    it should end because the admin finished looking, not because a background refresh quietly kept
    it alive for a day. Ending is `DELETE /auth/act-as`; expiry ends it too.
    """
    now = datetime.now(UTC)
    try:
        acting = repo.begin_act_as(
            principal,
            consultant_id,
            now=now,
            founder_reviewer_email=settings.founder_reviewer_email,
        )
    except ScopeViolationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    subject = repo.get_consultant_by_id(acting.consultant_id)
    if subject is None:  # pragma: no cover - begin_act_as just read this row
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    admin = repo.get_consultant_by_id(principal.consultant_id)
    if admin is None:  # pragma: no cover - the caller authenticated as this row
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")

    # `sub` stays the ADMIN. The token names who is at the keyboard; `act_as` is the restriction.
    token = create_access_token(
        settings,
        consultant_id=admin.id,
        email=admin.email,
        role=admin.role,
        tier=admin.tier,
        assessor_level=admin.assessor_level,
        now=now,
        act_as=subject.id,
    )
    return ActAsResponse(
        access_token=token,
        subject_consultant_id=subject.id,
        subject_name=subject.full_name,
        subject_email=subject.email,
    )


@router.delete("/act-as", response_model=TokenResponse)
def stop_act_as(
    principal: Principal = Depends(get_current_principal),
    repo: Repository = Depends(get_repository),
    settings: Settings = Depends(get_app_settings),
) -> TokenResponse:
    """Close the act-as session and hand back an ordinary admin token.

    The admin's own identity is rebuilt from `acting_admin_id` rather than trusted from the client,
    so "stop acting as" can only ever return you to yourself.
    """
    now = datetime.now(UTC)
    try:
        repo.end_act_as(principal, now=now)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    assert principal.acting_admin_id is not None  # end_act_as refused otherwise
    admin = repo.get_consultant_by_id(principal.acting_admin_id)
    if admin is None:  # pragma: no cover - they authenticated moments ago
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown admin.")
    token = create_access_token(
        settings,
        consultant_id=admin.id,
        email=admin.email,
        role=admin.role,
        tier=admin.tier,
        assessor_level=admin.assessor_level,
        now=now,
    )
    # No refresh token here either: this path returns an admin to their own scope, and the client
    # already holds whatever refresh token their original login issued.
    return TokenResponse(access_token=token, refresh_token="", token_type="bearer")
