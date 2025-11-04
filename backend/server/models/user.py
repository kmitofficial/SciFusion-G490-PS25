from pydantic import BaseModel, Field, EmailStr
from pydantic_mongo import PydanticObjectId
from typing import Optional


class User(BaseModel):
    """
    Model for a user retrieved from the DB
    (safe to return to client).
    """
    id: PydanticObjectId = Field(..., alias="_id")
    username: str
    email: EmailStr

    class Config:
        json_encoders = {PydanticObjectId: str}


class UserInDB(User):
    """
    Model for a user as stored in the DB
    (can include sensitive info).
    """
    hashed_password: str


class UserCreate(BaseModel):
    """
    Model for creating a new user (signup).
    """
    username: str
    email: EmailStr
    password: str


class Token(BaseModel):
    """
    Model for the JWT access token.
    """
    access_token: str
    token_type: str