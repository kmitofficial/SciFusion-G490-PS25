"""
API Router aggregator for version 1
"""

from fastapi import APIRouter

from api.v1.endpoints import experiments, papers, models, auth, health, websockets

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
api_router.include_router(papers.router, prefix="/papers", tags=["papers"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(websockets.router, prefix="/ws", tags=["websockets"])