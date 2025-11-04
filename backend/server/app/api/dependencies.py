"""Reusable FastAPI dependencies for authentication."""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException, status

from app.models.auth import UserPublic
from app.services import auth_service


def _extract_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header")
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")
    token = authorization[len(prefix) :].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")
    return token


@dataclass
class AuthenticatedUser:
    user: UserPublic
    token: str


def get_current_user(authorization: str | None = Header(default=None)) -> AuthenticatedUser:
    token = _extract_token(authorization)
    user = auth_service.get_user_from_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return AuthenticatedUser(user=user, token=token)


__all__ = ["AuthenticatedUser", "get_current_user"]
