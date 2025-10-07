"""
API Router aggregator for version 1
"""

from fastapi import APIRouter
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.endpoints import experiments, papers, models, auth, health, websockets

app = FastAPI(title="SciFusion Backend", version="1.0.0")
api_router = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
api_router.include_router(papers.router, prefix="/papers", tags=["papers"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(websockets.router, prefix="/ws", tags=["websockets"])


@app.get("/")
async def root():
    return {"message": "SciFusion FastAPI + MongoDB backend running!"}
