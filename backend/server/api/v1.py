# Location: backend/server/api/v1.py
from fastapi import APIRouter
# --- FIX ---
# Re-enable the 'jobs' import
from server.api.routers import hello, jobs, websocket, internal, auth
# --- END FIX ---

# This is the main router for the /api/v1 prefix
router = APIRouter()

# --- NEW: Auth Routes ---
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# --- HTTP Routes ---
router.include_router(hello.router, prefix="/hello", tags=["Hello"])
# --- FIX ---
# Re-enable the 'jobs' router
router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
# --- END FIX ---

# --- NEW: Internal Callback Router ---
# This includes all our new /_internal/... routes
router.include_router(internal.router, prefix="", tags=["_Internal"])

# --- WebSocket Route ---
# We add this at the root of /api/v1
router.include_router(websocket.router, tags=["WebSocket"])