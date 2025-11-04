"""Pydantic schemas used for authentication workflows."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    name: str
    created_at: datetime


class AuthResponse(BaseModel):
    token: str
    expires_at: datetime
    user: UserPublic


@dataclass
class AuthSession:
    token: str
    user: UserPublic
    expires_at: datetime


__all__ = [
    "SignupRequest",
    "LoginRequest",
    "UserPublic",
    "AuthResponse",
    "AuthSession",
]
