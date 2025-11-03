"""REST endpoints for orchestrating AutoAD pipeline sessions."""
from typing import List

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.models.session import (
    PipelineStage,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionEvent,
    SessionListItem,
    SessionStatus,
)
from app.services import session_service
from app.services.session_service import SessionNotFoundError

router = APIRouter()


@router.post(
    "",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Kick off a new AutoAD session",
)
async def launch_session(payload: SessionCreateRequest, background_tasks: BackgroundTasks) -> SessionCreateResponse:
    """Queue the AutoAD agent pipeline and return a tracking identifier."""

    session_id = session_service.create_session(payload)
    background_tasks.add_task(session_service.execute_session, session_id)
    return SessionCreateResponse(session_id=session_id)


@router.get(
    "",
    response_model=List[SessionListItem],
    summary="List recent AutoAD sessions",
)
async def list_sessions() -> List[SessionListItem]:
    """Return a snapshot summary of all known sessions for dashboards."""

    return session_service.list_sessions()


@router.get(
    "/{session_id}",
    response_model=SessionStatus,
    summary="Fetch detailed status for a session",
)
async def get_session_status(session_id: str) -> SessionStatus:
    """Fetch the current stage, events, and result paths for a session."""

    try:
        return session_service.get_status(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{session_id}/events",
    response_model=List[SessionEvent],
    summary="Stream session events",
)
async def get_session_events(session_id: str) -> List[SessionEvent]:
    """Return the event timeline for clients that poll for incremental updates."""

    try:
        status_snapshot = session_service.get_status(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return status_snapshot.events
