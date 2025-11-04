"""Application router wiring for API endpoints."""
from fastapi import APIRouter

from app.api import ai, auth, chats, projects, sessions

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(chats.router, prefix="/chats", tags=["chats"])
router.include_router(projects.router, prefix="/projects", tags=["projects"])
router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
router.include_router(ai.router, prefix="/ai", tags=["ai"])
