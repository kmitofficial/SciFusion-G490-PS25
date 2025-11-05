from pydantic import BaseModel

class MessageResponse(BaseModel):
    """A simple JSON response model with a single message."""
    message: str