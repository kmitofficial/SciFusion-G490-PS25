from fastapi import APIRouter
# Import our new internal router
# We comment out 'jobs' for now, as it will be fixed in Stage 2
from server.api.routers import hello, websocket, internal, auth

# This is the main router for the /api/v1 prefix
router = APIRouter()

# --- NEW: Auth Routes ---
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# --- HTTP Routes ---
router.include_router(hello.router, prefix="/hello", tags=["Hello"])
# We comment this out to fix the startup error
# router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])

# --- NEW: Internal Callback Router ---
# This includes all our new /_internal/... routes
router.include_router(internal.router, prefix="", tags=["_Internal"])

# --- WebSocket Route ---
# We add this at the root of /api/v1
router.include_router(websocket.router, tags=["WebSocket"])