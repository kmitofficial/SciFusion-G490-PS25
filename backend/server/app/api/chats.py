"""Chat orchestration endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.api.dependencies import AuthenticatedUser, get_current_user
from app.models.chat import (
    ChatCreateRequest,
    ChatListItem,
    ChatMessagesAppendRequest,
    ChatMessagesResponse,
    ChatResponse,
)
from app.services import chat_service, session_service
from app.services.chat_service import ChatNotFoundError

router = APIRouter()


def _record_to_response(record: chat_service.ChatRecord) -> ChatResponse:
    return ChatResponse(
        chat_id=record.chat_id,
        project_slug=record.project_slug,
        session_id=record.session_id,
        title=record.title,
        created_at=record.created_at,
    )


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    payload: ChatCreateRequest,
    background_tasks: BackgroundTasks,
    authenticated: AuthenticatedUser = Depends(get_current_user),
) -> ChatResponse:
    record = chat_service.create_chat(authenticated.user, payload)
    background_tasks.add_task(session_service.execute_session, record.session_id)
    return _record_to_response(record)


@router.get("", response_model=List[ChatListItem])
async def list_chats(authenticated: AuthenticatedUser = Depends(get_current_user)) -> List[ChatListItem]:
    return chat_service.list_chats(authenticated.user.id)


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(chat_id: str, authenticated: AuthenticatedUser = Depends(get_current_user)) -> ChatResponse:
    try:
        record = chat_service.get_chat(chat_id, authenticated.user.id)
    except ChatNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _record_to_response(record)


@router.get("/{chat_id}/messages", response_model=ChatMessagesResponse)
async def list_chat_messages(
    chat_id: str,
    authenticated: AuthenticatedUser = Depends(get_current_user),
) -> ChatMessagesResponse:
    try:
        messages = chat_service.list_messages(chat_id, authenticated.user.id)
    except ChatNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ChatMessagesResponse(messages=messages)


@router.post("/{chat_id}/messages", status_code=status.HTTP_204_NO_CONTENT)
async def append_chat_messages(
    chat_id: str,
    payload: ChatMessagesAppendRequest,
    authenticated: AuthenticatedUser = Depends(get_current_user),
) -> None:
    try:
        chat_service.append_messages(chat_id, authenticated.user.id, payload.messages)
    except ChatNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(chat_id: str, authenticated: AuthenticatedUser = Depends(get_current_user)) -> None:
    try:
        chat_service.delete_chat(chat_id, authenticated.user.id)
    except ChatNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
