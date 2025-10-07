"""
Model management endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
import requests

router = APIRouter()

class ModelInfo(BaseModel):
    name: str
    type: str  # "chat", "code", "embedding"
    provider: str  # "ollama", "openai", "anthropic"
    status: str  # "available", "loading", "error"
    size: str = None
    description: str = None

class ModelStatus(BaseModel):
    name: str
    status: str
    memory_usage: float = None
    load_time: float = None

@router.get("/", response_model=List[ModelInfo])
async def list_models():
    """List all available models"""
    models = []
    
    # Check Ollama models
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            ollama_data = response.json()
            for model in ollama_data.get("models", []):
                models.append(ModelInfo(
                    name=model["name"],
                    type="chat",
                    provider="ollama",
                    status="available",
                    size=model.get("size", "unknown"),
                    description=f"Ollama model: {model['name']}"
                ))
    except:
        pass  # Ollama not available
    
    # Add default models
    default_models = [
        ModelInfo(
            name="localhost-deepseek-v2-16b",
            type="chat",
            provider="ollama",
            status="recommended",
            description="DeepSeek V2 16B via Ollama (recommended)"
        ),
        ModelInfo(
            name="gpt-4o-2024-08-06",
            type="chat",
            provider="openai",
            status="available",
            description="OpenAI GPT-4 Omni"
        ),
        ModelInfo(
            name="claude-3-5-sonnet-20240620",
            type="chat",
            provider="anthropic",
            status="available",
            description="Anthropic Claude 3.5 Sonnet"
        )
    ]
    
    models.extend(default_models)
    return models

@router.get("/{model_name}/status", response_model=ModelStatus)
async def get_model_status(model_name: str):
    """Get status of a specific model"""
    
    # Check if it's an Ollama model
    if "localhost" in model_name or "ollama" in model_name:
        try:
            # Check Ollama server health
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                return ModelStatus(
                    name=model_name,
                    status="available"
                )
            else:
                return ModelStatus(
                    name=model_name,
                    status="error"
                )
        except:
            return ModelStatus(
                name=model_name,
                status="offline"
            )
    
    # For other models, return default status
    return ModelStatus(
        name=model_name,
        status="available"
    )

@router.post("/{model_name}/load")
async def load_model(model_name: str):
    """Load/start a model"""
    if "localhost" in model_name or "ollama" in model_name:
        # For Ollama models, we could trigger model loading
        return {"message": f"Loading model {model_name}"}
    else:
        raise HTTPException(status_code=400, detail="Model loading not supported for this provider")

@router.delete("/{model_name}/unload")
async def unload_model(model_name: str):
    """Unload/stop a model"""
    if "localhost" in model_name or "ollama" in model_name:
        return {"message": f"Unloading model {model_name}"}
    else:
        raise HTTPException(status_code=400, detail="Model unloading not supported for this provider")