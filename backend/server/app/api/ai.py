"""LLM-facing API endpoints for structured chat generations."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import AuthenticatedUser, get_current_user
from app.models.ai import LLMChatRequest, LLMChatResponse
from app.services import llm_service

router = APIRouter()


@router.post(
    "/chat",
    response_model=LLMChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Call the LLM with structured thoughts output",
)
async def create_llm_chat(
    payload: LLMChatRequest,
    authenticated: AuthenticatedUser = Depends(get_current_user),
) -> LLMChatResponse:
    try:
        return llm_service.generate_structured_chat(
            messages=payload.messages,
            model_name=payload.model,
            system_prompt=payload.system_prompt,
        )
    except llm_service.LLMConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc