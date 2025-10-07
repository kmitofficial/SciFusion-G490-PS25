"""
WebSocket endpoints for real-time communication
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
import asyncio
from datetime import datetime

from core.websocket_manager import WebSocketManager
from core.experiment_manager import ExperimentManager

router = APIRouter()

# Global WebSocket manager
websocket_manager = WebSocketManager()

def get_experiment_manager() -> ExperimentManager:
    return ExperimentManager()


@router.websocket("/experiments/{experiment_id}")
async def experiment_updates(
    websocket: WebSocket,
    experiment_id: str,
    exp_manager: ExperimentManager = Depends(get_experiment_manager)
):
    """WebSocket endpoint for real-time experiment updates"""
    await websocket_manager.connect(websocket, f"experiment:{experiment_id}")
    
    try:
        while True:
            # Send current experiment status
            status = exp_manager.get_experiment_status(experiment_id)
            if status:
                await websocket_manager.send_to_client(
                    websocket,
                    {
                        "type": "status_update",
                        "data": status.dict(),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            
            # Wait before next update
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket, f"experiment:{experiment_id}")


@router.websocket("/global")
async def global_updates(websocket: WebSocket):
    """WebSocket endpoint for global system updates"""
    await websocket_manager.connect(websocket, "global")
    
    try:
        while True:
            # Send system-wide updates
            await websocket_manager.send_to_client(
                websocket,
                {
                    "type": "system_status",
                    "data": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "active_experiments": len(websocket_manager.connections.get("experiment", {})),
                        "connected_clients": websocket_manager.get_connection_count()
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            await asyncio.sleep(10)  # Less frequent updates for global status
            
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket, "global")


# API endpoint to send messages to connected clients
@router.post("/broadcast/{channel}")
async def broadcast_message(channel: str, message: dict):
    """Send a message to all clients connected to a specific channel"""
    await websocket_manager.broadcast_to_channel(channel, message)
    return {"message": f"Broadcasted to channel: {channel}"}


@router.get("/connections")
async def get_connections():
    """Get information about active WebSocket connections"""
    return {
        "total_connections": websocket_manager.get_connection_count(),
        "channels": list(websocket_manager.connections.keys()),
        "connections_per_channel": {
            channel: len(connections) 
            for channel, connections in websocket_manager.connections.items()
        }
    }