from fastapi import Depends
from server.models.user import User
from server.services.user import get_or_create_stub_user


async def get_current_user_stub() -> User:
    """
    This is our DUMMY auth dependency.
    It provides a "stub" user for all API calls,
    bypassing login.

    When we're ready for real auth, we'll create a
    'get_current_user_real' and just swap this dependency.
    """
    user_in_db = await get_or_create_stub_user()
    # Return the "safe" User model (no password)
    return User(**user_in_db.model_dump())