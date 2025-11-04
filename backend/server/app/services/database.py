"""MongoDB utility helpers for the SciFusion backend."""
from __future__ import annotations

import os
from typing import Optional

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

_MONGO_URI = (
    os.getenv("MONGO_URI")
    or os.getenv("MONGODB_URI")
    or "mongodb://127.0.0.1:27017"
)
_DB_NAME = os.getenv("MONGO_DB_NAME") or os.getenv("MONGODB_DB") or "scifusion"

_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    """Return a shared MongoDB client instance."""

    global _client
    if _client is None:
        _client = MongoClient(_MONGO_URI)
    return _client


def get_database() -> Database:
    """Return the configured MongoDB database handle."""

    return get_client()[_DB_NAME]


def get_collection(name: str) -> Collection:
    """Shortcut for retrieving a named collection from the database."""

    return get_database()[name]


def init_db() -> None:
    """Ensure required collections and indexes exist."""

    db = get_database()

    users = db["users"]
    users.create_index("email", unique=True)
    users.create_index("created_at")

    tokens = db["auth_tokens"]
    tokens.create_index("user_id")
    tokens.create_index("expires_at", expireAfterSeconds=0)

    chats = db["chats"]
    chats.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    chats.create_index("session_id")

    chat_messages = db["chat_messages"]
    chat_messages.create_index([("chat_id", ASCENDING), ("timestamp", ASCENDING)])
    chat_messages.create_index("message_id", unique=False)


def close_client() -> None:
    """Dispose of the shared Mongo client (useful for tests)."""

    global _client
    if _client is not None:
        _client.close()
        _client = None


__all__ = ["get_client", "get_database", "get_collection", "init_db", "close_client"]
