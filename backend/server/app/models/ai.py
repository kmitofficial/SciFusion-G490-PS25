"""Schemas for direct LLM interactions exposed via the API."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Thought(BaseModel):
    title: str
    detail: str


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMChatRequest(BaseModel):
    model: str = Field(default="gemini-2.5-flash-lite", description="LLM identifier to invoke.")
    system_prompt: Optional[str] = Field(
        default=None,
        description="Optional system instruction appended before the default guidance.",
    )
    messages: list[ChatMessage] = Field(
        ..., description="Conversation history in chronological order.", min_length=1
    )


class LLMChatResponse(BaseModel):
    content: str
    thoughts: list[Thought] = Field(default_factory=list)
    raw: Optional[dict] = Field(default=None, description="Raw JSON payload returned by the model, if available.")


__all__ = [
    "Thought",
    "ChatMessage",
    "LLMChatRequest",
    "LLMChatResponse",
]