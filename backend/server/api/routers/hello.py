from fastapi import APIRouter
from server.services import hello
from server.models.message import MessageResponse

# This is the line that was likely missing or had a typo
router = APIRouter()

@router.get("/", response_model=MessageResponse, tags=["Hello"]) # <-- I'm also changing the path
async def get_hello_endpoint():
    """
    A test endpoint to see if the router, service,
    and models are all working together.
    """
    return hello.get_hello_message()