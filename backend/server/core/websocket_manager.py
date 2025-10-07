"""
WebSocket Manager for handling real-time connections
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time communication"""
    
    def __init__(self):
        # Store connections by channel
        self.connections: Dict[str, Set[WebSocket]] = {}
        
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, channel: str):
        """Accept a new WebSocket connection and add to channel"""
        await websocket.accept()
        
        # Initialize channel if not exists
        if channel not in self.connections:
            self.connections[channel] = set()
        
        # Add connection to channel
        self.connections[channel].add(websocket)
        
        # Store metadata
        self.connection_metadata[websocket] = {
            "channel": channel,
            "connected_at": asyncio.get_event_loop().time()
        }
        
        logger.info(f"WebSocket connected to channel: {channel}")
    
    async def disconnect(self, websocket: WebSocket, channel: str):
        """Remove WebSocket connection from channel"""
        if channel in self.connections:
            self.connections[channel].discard(websocket)
            
            # Clean up empty channels
            if not self.connections[channel]:
                del self.connections[channel]
        
        # Clean up metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        
        logger.info(f"WebSocket disconnected from channel: {channel}")
    
    async def send_to_client(self, websocket: WebSocket, message: dict):
        """Send message to a specific WebSocket client"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            # Connection might be closed, clean it up
            await self._cleanup_dead_connection(websocket)
    
    async def broadcast_to_channel(self, channel: str, message: dict):
        """Broadcast message to all clients in a channel"""
        if channel not in self.connections:
            return
        
        # Create a copy of connections to avoid modification during iteration
        connections = self.connections[channel].copy()
        
        # Send to all connections in channel
        dead_connections = []
        for websocket in connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                dead_connections.append(websocket)
        
        # Clean up dead connections
        for websocket in dead_connections:
            await self._cleanup_dead_connection(websocket)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected clients"""
        for channel in list(self.connections.keys()):
            await self.broadcast_to_channel(channel, message)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.connections.values())
    
    def get_channel_connections(self, channel: str) -> int:
        """Get number of connections in a specific channel"""
        return len(self.connections.get(channel, set()))
    
    def get_channels(self) -> List[str]:
        """Get list of active channels"""
        return list(self.connections.keys())
    
    async def _cleanup_dead_connection(self, websocket: WebSocket):
        """Clean up a dead WebSocket connection"""
        # Find and remove from all channels
        for channel in list(self.connections.keys()):
            if websocket in self.connections[channel]:
                self.connections[channel].discard(websocket)
                
                # Clean up empty channels
                if not self.connections[channel]:
                    del self.connections[channel]
        
        # Clean up metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]


# Global instance
websocket_manager = WebSocketManager()


# Utility functions for experiment updates
async def notify_experiment_update(experiment_id: str, update_data: dict):
    """Send update to all clients monitoring a specific experiment"""
    channel = f"experiment:{experiment_id}"
    message = {
        "type": "experiment_update",
        "experiment_id": experiment_id,
        "data": update_data,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    await websocket_manager.broadcast_to_channel(channel, message)


async def notify_experiment_status(experiment_id: str, status: str, progress: float = None):
    """Send status update for an experiment"""
    update_data = {"status": status}
    if progress is not None:
        update_data["progress"] = progress
    
    await notify_experiment_update(experiment_id, update_data)


async def notify_experiment_error(experiment_id: str, error: str):
    """Send error notification for an experiment"""
    await notify_experiment_update(experiment_id, {
        "status": "error",
        "error": error
    })


async def notify_experiment_completed(experiment_id: str, results: dict):
    """Send completion notification for an experiment"""
    await notify_experiment_update(experiment_id, {
        "status": "completed",
        "results": results
    })