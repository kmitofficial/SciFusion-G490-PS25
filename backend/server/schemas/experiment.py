"""
Experiment-related Pydantic schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ExperimentType(str, Enum):
    POINT_CLASSIFICATION = "point_classification_modelnet"
    IMAGE_CLASSIFICATION = "image_classification_cifar100"
    SENTIMENT_CLASSIFICATION = "sentiment_classification_sst2"
    CUSTOM = "custom"


class ExperimentStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class ExperimentCreate(BaseModel):
    name: str = Field(..., description="Experiment name")
    description: Optional[str] = Field(None, description="Experiment description")
    experiment_type: ExperimentType = Field(..., description="Type of experiment")
    
    # Model configuration
    model: str = Field(default="localhost-deepseek-v2-16b", description="LLM model to use")
    code_model: str = Field(default="localhost-deepseek-v2-16b", description="Code generation model")
    
    # Experiment parameters
    num_ideas: int = Field(default=20, ge=1, le=100, description="Number of ideas to generate")
    max_papers: int = Field(default=20, ge=1, le=100, description="Maximum papers for RAG")
    parallel: int = Field(default=0, ge=0, le=8, description="Number of parallel processes")
    
    # RAG configuration
    use_rag: bool = Field(default=False, description="Enable RAG for paper retrieval")
    topic: Optional[str] = Field(None, description="Research topic for RAG")
    
    # Advanced settings
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="LLM temperature")
    seed: int = Field(default=2025, description="Random seed for reproducibility")
    
    # GPU configuration
    gpus: Optional[str] = Field(None, description="GPU IDs to use (comma-separated)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Point Cloud Classification Experiment",
                "description": "Testing new architectures for 3D point cloud classification",
                "experiment_type": "point_classification_modelnet",
                "model": "localhost-deepseek-v2-16b",
                "num_ideas": 10,
                "use_rag": True,
                "topic": "point cloud deep learning attention mechanisms"
            }
        }


class ExperimentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ExperimentStatus] = None


class ExperimentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    experiment_type: ExperimentType
    status: ExperimentStatus
    
    # Configuration
    model: str
    code_model: str
    num_ideas: int
    max_papers: int
    parallel: int
    use_rag: bool
    topic: Optional[str]
    
    # Metadata
    created_at: datetime
    updated_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    # Progress tracking
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Completion progress (0-1)")
    current_step: Optional[str] = Field(None, description="Current processing step")
    
    # Results summary
    ideas_generated: int = Field(default=0, description="Number of ideas generated")
    ideas_tested: int = Field(default=0, description="Number of ideas tested")
    successful_ideas: int = Field(default=0, description="Number of successful ideas")
    
    class Config:
        from_attributes = True


class ExperimentStatusResponse(BaseModel):
    id: str
    status: ExperimentStatus
    progress: float
    current_step: Optional[str]
    message: Optional[str]
    
    # Real-time metrics
    ideas_generated: int
    ideas_tested: int
    successful_ideas: int
    failed_ideas: int
    
    # Time tracking
    elapsed_time: Optional[float] = Field(None, description="Elapsed time in seconds")
    estimated_remaining: Optional[float] = Field(None, description="Estimated remaining time in seconds")
    
    # Resource usage
    memory_usage: Optional[float] = Field(None, description="Memory usage percentage")
    gpu_usage: Optional[float] = Field(None, description="GPU usage percentage")


class IdeaResult(BaseModel):
    name: str
    title: str
    description: str
    status: str  # success, failed, running
    score: Optional[float] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    
    # Result metrics
    baseline_score: Optional[float] = None
    improvement: Optional[float] = None
    
    # Files and artifacts
    code_files: List[str] = []
    log_files: List[str] = []


class ExperimentResults(BaseModel):
    experiment_id: str
    status: ExperimentStatus
    
    # Summary statistics
    total_ideas: int
    successful_ideas: int
    failed_ideas: int
    
    # Performance metrics
    best_score: Optional[float] = None
    average_score: Optional[float] = None
    baseline_score: Optional[float] = None
    
    # Execution info
    total_execution_time: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Detailed results
    ideas: List[IdeaResult] = []
    
    # Generated artifacts
    result_files: List[str] = []
    log_files: List[str] = []
    
    # Error information
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None