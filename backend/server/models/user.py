from pydantic import BaseModel, Field
from pydantic_mongo import PydanticObjectId
from typing import Optional


class User(BaseModel):
    """
    Model for a user retrieved from the DB
    (safe to return to client).
    """
    id: PydanticObjectId = Field(..., alias="_id")
    username: str
    email: Optional[str] = None

    class Config:
        json_encoders = {PydanticObjectId: str}


class UserInDB(User):
    """
    Model for a user as stored in the DB
    (can include sensitive info).
    """
    # In a real system, this would be hashed_password
    pass