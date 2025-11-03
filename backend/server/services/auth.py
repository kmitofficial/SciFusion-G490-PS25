from fastapi import Depends
from server.models.user import User
from server.services.user import get_or_create_stub_user


async def get_current_user_stub() -> User:
    """
    This is our DUMMY auth dependency.
    It provides a "stub" user for all API calls,
    bypassing login.
    """

    # 1. Get the UserInDB object from the database
    user_in_db = await get_or_create_stub_user()

    # 2. JUST RETURN THE OBJECT.
    # A UserInDB object *is* a valid User object,
    # so we can return it directly. This avoids
    # the Pydantic validation error.
    return user_in_db