from contextlib import asynccontextmanager
from fastapi import FastAPI

# We no longer need to watch the database,
# so the lifespan event can be very simple.

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan manager.
    """
    print("Server is starting up...")
    yield
    print("Server is shutting down...")