"""Application router wiring for API endpoints."""
from fastapi import APIRouter

from app.api import projects, sessions

router = APIRouter()
router.include_router(projects.router, prefix="/projects", tags=["projects"])
router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
