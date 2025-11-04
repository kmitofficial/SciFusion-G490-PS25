"""Pydantic models describing chat orchestration payloads."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.models.ai import Thought


class ChatCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, description="Initial user prompt to seed the project and session.")
    num_ideas: int = Field(..., ge=1, le=50, description="Number of ideas to request from the LLM.")
    max_papers: int = Field(..., ge=0, le=200, description="Maximum literature papers to retrieve when RAG is enabled.")
    project_name: Optional[str] = Field(
        None,
        description="Optional friendly name for the generated project. Defaults to a timestamped label.",
    )
    topic: Optional[str] = Field(
        None,
        description="Optional topic override for RAG and idea generation stages.",
    )
    enable_rag: Optional[bool] = Field(
        None,
        description="Override for enabling RAG. If omitted, inferred from max_papers > 0.",
    )
    model: str = Field(
        default="gemini-2.5-flash-lite",
        description="LLM model identifier used during idea generation.",
    )
    code_model: str = Field(
        default="flash",
        description="Model identifier passed to aider for experiment execution.",
    )


class ChatResponse(BaseModel):
    chat_id: str
    project_slug: str
    session_id: str
    title: str
    created_at: datetime


class ChatListItem(BaseModel):
    chat_id: str
    title: str
    session_id: str
    project_slug: str
    created_at: datetime


class ChatMessagePayload(BaseModel):
    id: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Unique identifier for the message within a chat transcript.",
    )
    role: Literal["user", "assistant"] = Field(..., description="Role associated with the message content.")
    content: str = Field(..., description="Message body text supplied by the sender.")
    timestamp: datetime = Field(..., description="Timestamp applied when the message was generated.")
    thoughts: list[Thought] = Field(
        default_factory=list,
        description="Optional structured reasoning metadata for assistant replies.",
    )


class ChatMessagesAppendRequest(BaseModel):
    messages: list[ChatMessagePayload] = Field(
        ...,
        min_items=1,
        description="Messages to append or upsert for the specified chat.",
    )


class ChatMessagesResponse(BaseModel):
    messages: list[ChatMessagePayload] = Field(default_factory=list)


__all__ = [
    "ChatCreateRequest",
    "ChatResponse",
    "ChatListItem",
    "ChatMessagePayload",
    "ChatMessagesAppendRequest",
    "ChatMessagesResponse",
]