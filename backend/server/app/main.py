"""FastAPI application exposing project bootstrapping endpoints for AutoAD."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(
    title="SciFusion AutoAD Backend",
    version="0.1.0",
    description=(
        "APIs for creating and managing AutoAD experiment workspaces that feed the "
        "launch_dolphin automation pipeline."
    ),
)

# Allow local tooling (e.g., session monitor page) to poll the API from other ports.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8080",
        "http://localhost",
        "http://localhost:5500",
        "http://localhost:8080",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", tags=["health"], summary="Basic readiness probe")
async def health_check() -> dict[str, str]:
    """Return a simple heartbeat payload for uptime monitoring."""
    return {"status": "ok"}
