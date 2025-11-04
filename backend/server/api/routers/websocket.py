# Location: backend/server/api/routers/websocket.py

from fastapi import (
    APIRouter, WebSocket, WebSocketDisconnect, Depends, status
)
from server.models.job import ResearchRequest, Job
from server.models.user import User
from server.services.auth import get_current_user_ws
from server.services.websocket import manager
from server.services import research
from server.core.db import db
import json

router = APIRouter()
jobs_collection = db.get_jobs_collection_async()


@router.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        current_user: User = Depends(get_current_user_ws)
):
    user_id = str(current_user.id)
    await manager.connect(user_id, websocket)

    try:
        while True:
            # This loop just keeps the connection alive
            # and waits for the client to disconnect.
            data = await websocket.receive_text()
            print(f"Received (and ignoring) ws message from {user_id}: {data[:50]}...")

    except WebSocketDisconnect:
        # --- FIX ---
        # Removed 'await'. disconnect() is not an async function.
        manager.disconnect(user_id)
        # --- END FIX ---
    except Exception as e:
        print(f"Error in WebSocket for user {user_id}: {e}")
        # --- FIX ---
        # Removed 'await'. disconnect() is not an async function.
        manager.disconnect(user_id)
        # --- END FIX ---