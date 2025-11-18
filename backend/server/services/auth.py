# Location: backend/server/services/auth.py

from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from pydantic import ValidationError
import urllib.parse  # Import this

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


# --- NEW: Internal Token Validation Logic ---
async def _get_user_from_token(token: str) -> User:
    """
    Internal function to decode a token and fetch a user.
    Reusable for both HTTP and WS.
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


# --- UPDATED: HTTP "Get Current User" Dependency ---
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency for HTTP routes. Gets token from Authorization header.
    """
    return await _get_user_from_token(token)


# --- NEW: WebSocket "Get Current User" Dependency ---
async def get_current_user_ws(websocket: WebSocket) -> User:
    """
    Dependency for WebSocket routes. Gets token from query string.
    """
    token = None
    query_string = websocket.scope.get("query_string", b"").decode("utf-8")
    query_params = dict(urllib.parse.parse_qsl(query_string))

    token = query_params.get("token")

    if token is None:
        # If no token, close the connection
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        # We still raise an exception to stop dependency processing
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    # Now that we have the token, validate it.
    try:
        user = await _get_user_from_token(token)
        return user
    except HTTPException:
        # If token is invalid, close the connection
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise