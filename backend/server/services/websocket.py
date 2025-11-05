from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    """
    Manages active WebSocket connections.
    We map a user_id to their active WebSocket.
    """
    def __init__(self):
        # We can't use our dummy auth here, so we'll map
        # the user_id (which we get from the dummy auth)
        # to their active WebSocket connection.
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        """Register a new connection."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"WebSocket connected for user: {user_id}")

    def disconnect(self, user_id: str):
        """Remove a disconnected user."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"WebSocket disconnected for user: {user_id}")

    async def send_json(self, user_id: str, message: dict):
        """Send a JSON message to a specific user."""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                print(f"Error sending WebSocket message to user {user_id}: {e}")
                self.disconnect(user_id)

# Create a single, importable instance
manager = ConnectionManager()