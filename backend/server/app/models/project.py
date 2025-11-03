"""Pydantic schemas describing new AutoAD project payloads and responses."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class ProjectCreateRequest(BaseModel):
    """Inbound payload for creating a brand-new AutoAD experiment workspace."""

    name: str = Field(..., min_length=3, description="Human friendly project name.")
    topic: str = Field(..., description="Primary research topic or problem focus.")
    objective: str = Field(..., description="High level objective you want AutoAD to pursue.")
    success_metric: str = Field(
        ..., description="How the user will evaluate the success of the generated algorithms."
    )
    user_persona: Optional[str] = Field(
        None,
        description="Target persona or end-user profile the assistant should keep in mind during ideation.",
    )
    data_sources: List[str] = Field(
        default_factory=list,
        description="Known datasets, corpora, or sensors that are relevant to the project.",
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="Any hard constraints (latency, hardware, fairness, privacy, etc.).",
    )
    preferred_modalities: List[str] = Field(
        default_factory=list,
        description="Optional hints about data modalities or model families the user wants to prioritize.",
    )
    enable_rag: bool = Field(
        False,
        description="Whether to prefetch literature via RAG to ground idea generation.",
    )
    seed: int = Field(
        2025,
        ge=0,
        description="Random seed used when sampling literature or ideas for this project.",
    )
    rag_max_papers: int = Field(
        20,
        ge=1,
        le=200,
        description="Upper bound on papers to retrieve when RAG is enabled.",
    )
    rag_memory_papers: int = Field(
        10,
        ge=0,
        le=200,
        description="How many previously retrieved papers to feed into the next RAG query.",
    )
    notes: Optional[str] = Field(
        None,
        description="Free-form context, background knowledge, or extra prompts to persist alongside the project.",
    )

    @validator("rag_memory_papers")
    def validate_memory_window(cls, value: int, values: dict) -> int:
        """Clamp the rolling memory window to the configured retrieval budget."""
        max_papers = values.get("rag_max_papers", 20)
        if value > max_papers:
            raise ValueError("rag_memory_papers cannot exceed rag_max_papers")
        return value


class ProjectDetail(ProjectCreateRequest):
    """Full project configuration enriched with derived metadata."""
    slug: str
    created_at: datetime
    base_dir: str
    results_dir: str


class ProjectSummary(BaseModel):
    """Compact listing shape for dashboard tables."""
    name: str
    slug: str
    topic: str
    created_at: datetime
    enable_rag: bool


class ProjectResponse(BaseModel):
    """Wrapper returned by the API after successfully creating a project."""
    message: str
    project: ProjectDetail
