from server.core.db import db
from server.models.user import UserInDB, UserCreate
from server.services.auth import get_password_hash

# Use the ASYNC collection for our async auth function
users_collection = db.get_users_collection_async()


async def get_user_by_username(username: str) -> UserInDB | None:
    """Finds a user by their username."""
    user_doc = await users_collection.find_one({"username": username})
    if user_doc:
        return UserInDB(**user_doc)
    return None


async def get_user_by_email(email: str) -> UserInDB | None:
    """Finds a user by their email."""
    user_doc = await users_collection.find_one({"email": email})
    if user_doc:
        return UserInDB(**user_doc)
    return None


async def create_db_user(user_in: UserCreate) -> UserInDB:
    """Creates a new user in the database."""
    hashed_password = get_password_hash(user_in.password)

    user_doc = {
        "username": user_in.username,
        "email": user_in.email,
        "hashed_password": hashed_password
    }

    insert_result = await users_collection.insert_one(user_doc)

    created_user = await users_collection.find_one(
        {"_id": insert_result.inserted_id}
    )

    if created_user:
        return UserInDB(**created_user)

    # This should not happen
    raise Exception("Failed to create user after insertion.")