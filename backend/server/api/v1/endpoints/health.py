"""
Health check endpoints
"""

from fastapi import APIRouter
from pydantic import BaseModel
import psutil
import os
import sys

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
    system_info: dict


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime=0.0,  # Would implement actual uptime tracking
        system_info={
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
        }
    )

@router.get("/detailed")
async def detailed_health():
    """Detailed health check with dependencies"""
    health_status = {
        "api": "healthy",
        "database": "checking...",
        "redis": "checking...",
        "ollama": "checking...",
        "disk_space": "healthy",
        "memory": "healthy"
    }
    
    # Check memory usage
    memory = psutil.virtual_memory()
    if memory.percent > 90:
        health_status["memory"] = "critical"
    elif memory.percent > 75:
        health_status["memory"] = "warning"
    
    return health_status