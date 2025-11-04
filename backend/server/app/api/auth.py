"""Authentication endpoints for SciFusion."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import AuthenticatedUser, get_current_user
from app.models.auth import AuthResponse, LoginRequest, SignupRequest, UserPublic
from app.services import auth_service
from app.services.auth_service import InvalidCredentialsError, UserAlreadyExistsError

router = APIRouter()


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest) -> AuthResponse:
    try:
        session = auth_service.register_user(payload.name, payload.email, payload.password)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return AuthResponse(token=session.token, expires_at=session.expires_at, user=session.user)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest) -> AuthResponse:
    try:
        session = auth_service.authenticate(payload.email, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return AuthResponse(token=session.token, expires_at=session.expires_at, user=session.user)


@router.get("/me", response_model=UserPublic)
async def get_me(authenticated: AuthenticatedUser = Depends(get_current_user)) -> UserPublic:
    return authenticated.user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(authenticated: AuthenticatedUser = Depends(get_current_user)) -> None:
    auth_service.revoke_token(authenticated.token)
