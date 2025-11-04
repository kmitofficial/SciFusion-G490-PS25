"""Service utilities for coordinating chats, projects, and sessions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List
from uuid import uuid4

from app.models.auth import UserPublic
from app.models.ai import Thought
from app.models.chat import ChatCreateRequest, ChatListItem, ChatMessagePayload
from app.models.project import ProjectCreateRequest
from app.models.session import SessionCreateRequest
from app.services import project_service, session_service
from app.services.database import get_collection
from pymongo import ASCENDING, ReplaceOne


@dataclass
class ChatRecord:
    chat_id: str
    user_id: str
    project_slug: str
    session_id: str
    title: str
    created_at: datetime


class ChatNotFoundError(RuntimeError):
    """Raised when a chat does not exist for the current user."""


def _determine_title(prompt: str, fallback: str) -> str:
    cleaned = " ".join(prompt.strip().split())
    if not cleaned:
        return fallback
    return cleaned[:80] + ("…" if len(cleaned) > 80 else "")


def _build_project_request(payload: ChatCreateRequest) -> ProjectCreateRequest:
    enable_rag = payload.enable_rag if payload.enable_rag is not None else payload.max_papers > 0
    rag_max = max(payload.max_papers, 0)
    rag_memory = max(1, min(rag_max if rag_max else 1, 5))

    now_label = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    project_name = payload.project_name or f"Research chat {now_label}"
    topic = payload.topic or payload.prompt

    return ProjectCreateRequest(
        name=project_name,
        topic=topic,
        objective=payload.prompt,
        success_metric="Surface the most novel and feasible research ideas.",
        enable_rag=enable_rag,
        rag_max_papers=rag_max if rag_max else 20,
        rag_memory_papers=rag_memory,
        notes=f"Seed prompt: {payload.prompt}",
    )


def _build_session_request(project_slug: str, payload: ChatCreateRequest) -> SessionCreateRequest:
    enable_rag = payload.enable_rag if payload.enable_rag is not None else payload.max_papers > 0
    return SessionCreateRequest(
        project_slug=project_slug,
        model=payload.model,
        code_model=payload.code_model,
        num_ideas=payload.num_ideas,
        use_rag=enable_rag,
        topic_override=payload.topic or payload.prompt,
        parallel=0,
    )


def _as_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:  # pragma: no cover - defensive
            pass
    return datetime.utcnow()


def _thoughts_from_doc(payload: object) -> List[Thought]:
    thoughts: List[Thought] = []
    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or item.get("heading") or "Thought").strip()
            detail = str(item.get("detail") or item.get("content") or "").strip()
            thoughts.append(Thought(title=title, detail=detail))
    return thoughts


def create_chat(user: UserPublic, payload: ChatCreateRequest) -> ChatRecord:
    project_request = _build_project_request(payload)
    project_detail = project_service.create_project(project_request)

    session_request = _build_session_request(project_detail.slug, payload)
    session_id = session_service.create_session(session_request)

    chat_id = str(uuid4())
    created_at = datetime.utcnow()
    title = _determine_title(payload.prompt, project_detail.name)

    chats = get_collection("chats")
    chats.insert_one(
        {
            "_id": chat_id,
            "user_id": user.id,
            "project_slug": project_detail.slug,
            "session_id": session_id,
            "title": title,
            "created_at": created_at,
        }
    )

    return ChatRecord(
        chat_id=chat_id,
        user_id=user.id,
        project_slug=project_detail.slug,
        session_id=session_id,
        title=title,
        created_at=created_at,
    )


def list_chats(user_id: str) -> List[ChatListItem]:
    chats = get_collection("chats")
    cursor = chats.find({"user_id": user_id}).sort("created_at", -1)

    items: List[ChatListItem] = []
    for doc in cursor:
        items.append(
            ChatListItem(
                chat_id=str(doc["_id"]),
                title=str(doc.get("title", "")),
                session_id=str(doc["session_id"]),
                project_slug=str(doc["project_slug"]),
                created_at=_as_datetime(doc.get("created_at")),
            )
        )
    return items


def get_chat(chat_id: str, user_id: str) -> ChatRecord:
    chats = get_collection("chats")
    doc = chats.find_one({"_id": chat_id, "user_id": user_id})

    if doc is None:
        raise ChatNotFoundError("Chat not found")

    return ChatRecord(
        chat_id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        project_slug=str(doc["project_slug"]),
        session_id=str(doc["session_id"]),
        title=str(doc.get("title", "")),
        created_at=_as_datetime(doc.get("created_at")),
    )


def _message_to_doc(chat_id: str, user_id: str, payload: ChatMessagePayload) -> dict[str, object]:
    return {
        "_id": f"{chat_id}:{payload.id}",
        "chat_id": chat_id,
        "user_id": user_id,
        "message_id": payload.id,
        "role": payload.role,
        "content": payload.content,
        "thoughts": [thought.model_dump() for thought in payload.thoughts],
        "timestamp": payload.timestamp,
    }


def append_messages(chat_id: str, user_id: str, messages: Iterable[ChatMessagePayload]) -> None:
    # Ensure chat belongs to user before writing.
    get_chat(chat_id, user_id)

    operations: List[ReplaceOne] = []
    for payload in messages:
        doc = _message_to_doc(chat_id, user_id, payload)
        operations.append(ReplaceOne({"_id": doc["_id"]}, doc, upsert=True))

    if not operations:
        return

    collection = get_collection("chat_messages")
    collection.bulk_write(operations, ordered=False)


def list_messages(chat_id: str, user_id: str) -> List[ChatMessagePayload]:
    get_chat(chat_id, user_id)
    collection = get_collection("chat_messages")

    cursor = collection.find({"chat_id": chat_id, "user_id": user_id}).sort("timestamp", ASCENDING)

    results: List[ChatMessagePayload] = []
    for doc in cursor:
        results.append(
            ChatMessagePayload(
                id=str(doc.get("message_id") or str(doc.get("_id", ""))).split(":")[-1],
                role=str(doc.get("role", "assistant")),
                content=str(doc.get("content", "")),
                timestamp=_as_datetime(doc.get("timestamp")),
                thoughts=_thoughts_from_doc(doc.get("thoughts")),
            )
        )
    return results


def delete_chat(chat_id: str, user_id: str) -> None:
    chats = get_collection("chats")
    result = chats.delete_one({"_id": chat_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise ChatNotFoundError("Chat not found")

    collection = get_collection("chat_messages")
    collection.delete_many({"chat_id": chat_id, "user_id": user_id})


__all__ = [
    "ChatRecord",
    "ChatNotFoundError",
    "create_chat",
    "list_chats",
    "get_chat",
    "append_messages",
    "list_messages",
    "delete_chat",
]
