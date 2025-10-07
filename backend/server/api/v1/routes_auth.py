from fastapi import APIRouter, HTTPException
from app.schemas.user_schema import UserCreate
from app.services.user_service import create_user, login_user

router = APIRouter()

@router.post("/signup")
async def signup(user: UserCreate):
    result = await create_user(user)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"message": "User created successfully", "user": result}

@router.post("/login")
async def login(data: dict):
    email = data.get("email")
    password = data.get("password")
    result = await login_user(email, password)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
