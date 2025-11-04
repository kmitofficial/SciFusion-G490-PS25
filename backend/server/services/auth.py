from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from pydantic import ValidationError

from server.core.config import settings
from server.models.user import User, UserInDB
from server.core.db import db

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
users_collection = db.get_users_collection_async()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashes a password."""
    return pwd_context.hash(password)


# --- JWT Token Creation ---
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


# --- NEW: "Get Current User" Dependency ---
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to get the current user from a JWT token.
    This replaces get_current_user_stub.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception

    except (JWTError, ValidationError):
        raise credentials_exception

    # Find user in the database
    user_doc = await users_collection.find_one({"username": username})

    if user_doc is None:
        raise credentials_exception

    # Return the client-safe User model
    return User(**user_doc)