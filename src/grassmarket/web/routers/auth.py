"""Auth router — login, invitation redemption, invitation creation, and the current identity."""

from __future__ import annotations

from bcap_contracts.auth import (
    AcceptInvitationRequest,
    Consultant,
    LoginRequest,
    TokenResponse,
)
from bcap_contracts.common import ConsultantTier, Role
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from grassmarket.auth.service import (
    AuthService,
    InvalidCredentialsError,
    InvalidInvitationError,
)
from grassmarket.data.repository import Principal, Repository
from grassmarket.web.dependencies import (
    get_auth_service,
    get_current_principal,
    get_repository,
)

router = APIRouter(prefix="/auth", tags=["auth"])


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
    delivery (email integration is a later loop)."""
    raw_token = auth.create_invitation(
        inviter_id=principal.consultant_id,
        email=payload.email,
        role=payload.role,
        tier=payload.tier,
    )
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
