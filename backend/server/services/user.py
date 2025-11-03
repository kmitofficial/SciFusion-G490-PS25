from server.core.db import db
from server.models.user import UserInDB

# Use the ASYNC collection for our async auth function
users_collection = db.get_users_collection_async()
STUB_USERNAME = "testuser"


async def get_or_create_stub_user() -> UserInDB:
    """
    This is our "dummy" user function. It finds "testuser"
    or creates it if it doesn't exist.
    This replaces a real login system for now.
    """

    # 1. Try to find the user
    user_doc = await users_collection.find_one({"username": STUB_USERNAME})

    if user_doc:
        # Found it. Pydantic will handle the _id alias.
        return UserInDB(**user_doc)

    # 2. Not found, so let's create it
    print(f"Stub user '{STUB_USERNAME}' not found, creating...")
    new_user_data = {
        "username": STUB_USERNAME,
        "email": "test@user.com"
    }
    insert_result = await users_collection.insert_one(new_user_data)

    # 3. Fetch the newly created user and return it
    created_user_doc = await users_collection.find_one(
        {"_id": insert_result.inserted_id}
    )

    if created_user_doc:
        return UserInDB(**created_user_doc)

    # This should never happen, but it's a safe fallback
    raise Exception("Failed to create or find stub user.")