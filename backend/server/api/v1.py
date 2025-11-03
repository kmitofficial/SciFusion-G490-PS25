from fastapi import APIRouter
# Import our new internal router
from server.api.routers import hello, jobs, websocket, internal

# This is the main router for the /api/v1 prefix
router = APIRouter()

# --- HTTP Routes ---
router.include_router(hello.router, prefix="/hello", tags=["Hello"])
router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])

# --- NEW: Internal Callback Router ---
# This includes all our new /_internal/... routes
router.include_router(internal.router, prefix="", tags=["_Internal"])

# --- WebSocket Route ---
# We add this at the root of /api/v1
router.include_router(websocket.router, tags=["WebSocket"])