from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic_mongo import PydanticObjectId


# --- ResearchRequest (from Stage 2) ---
# (We keep this exactly as it was)
class ResearchRequest(BaseModel):
    topic: str = "novel attention mechanisms for sentiment classification"
    experiment: str = "sentiment_classification_sst2"
    model: str = "gemini-2.5-flash-lite"
    code_model: str = "flash"
    num_ideas: int = 3
    rag: bool = True
    check_similarity: bool = True
    skip_novelty_check: bool = False
    round: int = 0
    save_name: str = "api_test"

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "using transformers for time series forecasting",
                "experiment": "AutoTSF_ETTh1",
                "num_ideas": 2,
            }
        }


# --- NEW: Job Model (for Database) ---
class Job(BaseModel):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    user_id: PydanticObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"
    request: ResearchRequest

    # --- NEW FIELDS FOR LIVE DATA ---
    papers: Optional[Dict[str, Any]] = None
    ideas: Optional[List[Dict[str, Any]]] = None
    experiment_results: List[Dict[str, Any]] = []  # Start as empty list

    # --- Final Log Fields (from Stage 3) ---
    log: Optional[str] = None
    error_log: Optional[str] = None

    class Config:
        json_encoders = {PydanticObjectId: str}


class ResearchRequestSidebar(BaseModel):
    """
    A small model for just the topic in the sidebar.
    """
    topic: str

class JobSidebarItem(BaseModel):
    """
    A small model for the job list in the sidebar.
    Matches the projection in the 'get_all_jobs' endpoint.
    """
    id: PydanticObjectId = Field(..., alias="_id")
    request: ResearchRequestSidebar
    created_at: datetime
    status: str

    class Config:
        json_encoders = {PydanticObjectId: str}