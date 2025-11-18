from fastapi import APIRouter
from server.services import hello
from server.models.message import MessageResponse

router = APIRouter()

@router.get("/hello", response_model=MessageResponse, tags=["Hello"])
async def get_hello_endpoint():
    """
    A test endpoint to see if the router, service,
    and models are all working together.
    """
    return hello.get_hello_message()