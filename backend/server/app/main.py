"""
FastAPI Server for InternAgent

This server provides REST API and WebSocket endpoints to interact with 
the InternAgent research automation system from frontend applications.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn
import os
import sys

# Add parent directory to path to import InternAgent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.v1.api import api_router
from core.experiment_manager import ExperimentManager
from utils.logging import setup_logging
from app.config import get_settings

# Setup logging
setup_logging()

# Get settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="InternAgent API",
    description="REST API for InternAgent Research Automation System",
    version="1.0.0",
    openapi_url=f"/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Redirect root to API documentation"""
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "InternAgent API",
        "version": "1.0.0"
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    return HTTPException(
        status_code=500,
        detail=f"Internal server error: {str(exc)}"
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )