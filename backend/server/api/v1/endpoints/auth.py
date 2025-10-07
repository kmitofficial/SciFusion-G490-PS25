"""
Authentication endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# Simple auth for now - would implement proper JWT auth in production
security = HTTPBearer()

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str

class UserInfo(BaseModel):
    username: str
    email: Optional[str] = None
    is_admin: bool = False

# Placeholder for authentication
@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """User authentication endpoint"""
    # Placeholder authentication - replace with real auth
    if login_data.username == "admin" and login_data.password == "admin":
        return LoginResponse(
            access_token="dummy-token",
            username=login_data.username
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

@router.post("/logout")
async def logout():
    """User logout endpoint"""
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserInfo)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user information"""
    # Placeholder - would validate JWT token in production
    return UserInfo(
        username="admin",
        email="admin@internagent.com",
        is_admin=True
    )