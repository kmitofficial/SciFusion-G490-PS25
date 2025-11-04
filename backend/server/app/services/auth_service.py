"""Authentication and user management helpers."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta
from typing import Mapping, Optional
from uuid import uuid4

from app.models.auth import AuthSession, UserPublic
from app.services.database import get_collection
from pymongo.errors import DuplicateKeyError

_TOKEN_TTL_DAYS = 7
_ITERATIONS = 200_000
_HASH_NAME = "sha256"
_SALT_BYTES = 16


class UserAlreadyExistsError(RuntimeError):
    """Raised when attempting to register an email that already exists."""


class InvalidCredentialsError(RuntimeError):
    """Raised when a user provides incorrect login details."""


def _hash_password(password: str) -> str:
    salt = os.urandom(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(_HASH_NAME, password.encode("utf-8"), salt, _ITERATIONS)
    payload = salt + derived
    return base64.b64encode(payload).decode("ascii")


def _verify_password(password: str, stored_hash: str) -> bool:
    payload = base64.b64decode(stored_hash.encode("ascii"))
    salt = payload[:_SALT_BYTES]
    stored = payload[_SALT_BYTES:]
    derived = hashlib.pbkdf2_hmac(_HASH_NAME, password.encode("utf-8"), salt, _ITERATIONS)
    return hmac.compare_digest(stored, derived)


def _doc_to_user(doc: Mapping[str, object]) -> UserPublic:
    return UserPublic(
        id=str(doc["_id"]),
        email=str(doc["email"]),
        name=str(doc["name"]),
        created_at=_as_datetime(doc.get("created_at")),
    )


def _as_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:  # pragma: no cover - defensive
            pass
    return datetime.utcnow()


def _issue_token(user_id: str) -> AuthSession:
    token = secrets.token_urlsafe(48)
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(days=_TOKEN_TTL_DAYS)

    tokens = get_collection("auth_tokens")
    tokens.replace_one(
        {"_id": token},
        {
            "_id": token,
            "user_id": user_id,
            "created_at": created_at,
            "expires_at": expires_at,
        },
        upsert=True,
    )

    users = get_collection("users")
    user_doc = users.find_one({"_id": user_id})
    if user_doc is None:  # pragma: no cover - defensive guard
        raise RuntimeError("User not found while issuing token")

    return AuthSession(token=token, user=_doc_to_user(user_doc), expires_at=expires_at)


def register_user(name: str, email: str, password: str) -> AuthSession:
    """Create a new user and return an authenticated session."""

    user_id = str(uuid4())
    created_at = datetime.utcnow()
    password_hash = _hash_password(password)

    users = get_collection("users")
    normalized_email = email.lower()
    if users.find_one({"email": normalized_email}):
        raise UserAlreadyExistsError("An account with this email already exists.")

    try:
        users.insert_one(
            {
                "_id": user_id,
                "email": normalized_email,
                "name": name.strip(),
                "password_hash": password_hash,
                "created_at": created_at,
            }
        )
    except DuplicateKeyError as exc:  # pragma: no cover - race condition guard
        raise UserAlreadyExistsError("An account with this email already exists.") from exc

    return _issue_token(user_id)


def authenticate(email: str, password: str) -> AuthSession:
    """Validate credentials and return a fresh auth session."""

    users = get_collection("users")
    normalized_email = email.lower()
    doc = users.find_one({"email": normalized_email})

    if doc is None or not _verify_password(password, str(doc["password_hash"])):
        raise InvalidCredentialsError("Invalid email or password.")

    return _issue_token(str(doc["_id"]))


def get_user_from_token(token: str) -> Optional[UserPublic]:
    """Return the user associated with the provided token if valid."""

    tokens = get_collection("auth_tokens")
    token_doc = tokens.find_one({"_id": token})
    if token_doc is None:
        return None

    expires_at = _as_datetime(token_doc.get("expires_at"))
    if expires_at < datetime.utcnow():
        revoke_token(token)
        return None

    users = get_collection("users")
    user_doc = users.find_one({"_id": token_doc["user_id"]})
    if user_doc is None:
        revoke_token(token)
        return None

    return _doc_to_user(user_doc)


def revoke_token(token: str) -> None:
    tokens = get_collection("auth_tokens")
    tokens.delete_one({"_id": token})


def cleanup_expired_tokens() -> None:
    tokens = get_collection("auth_tokens")
    tokens.delete_many({"expires_at": {"$lt": datetime.utcnow()}})


__all__ = [
    "AuthSession",
    "UserPublic",
    "UserAlreadyExistsError",
    "InvalidCredentialsError",
    "register_user",
    "authenticate",
    "get_user_from_token",
    "revoke_token",
    "cleanup_expired_tokens",
]
