from fastapi import WebSocket
from typing import Dict, List, Optional, Set
import json

class ConnectionManager:
    """Manage active WebSocket connections for users and jobs."""

    GLOBAL_SUBSCRIPTION = "__GLOBAL__"

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}        # user_id → ws
        self.job_subscribers: Dict[str, List[WebSocket]] = {}     # job_id → [ws]
        self.user_jobs: Dict[str, Set[str]] = {}                  # user_id → {job_ids}

    async def connect(self, user_id: str, websocket: WebSocket, job_id: Optional[str] = None):
        """Register a new connection and subscribe to job (or global if none)."""
        await websocket.accept()
        self.active_connections[user_id] = websocket

        subscription = job_id or self.GLOBAL_SUBSCRIPTION
        if subscription not in self.job_subscribers:
            self.job_subscribers[subscription] = []
        if websocket not in self.job_subscribers[subscription]:
            self.job_subscribers[subscription].append(websocket)

        if user_id not in self.user_jobs:
            self.user_jobs[user_id] = set()
        self.user_jobs[user_id].add(subscription)

        print(f"WebSocket connected: user={user_id}, job={job_id or '*'}")

    def disconnect(self, user_id: str, job_id: Optional[str] = None):
        """Remove connection and unsubscribe from job(s)."""
        ws = self.active_connections.pop(user_id, None)
        if not ws:
            return

        subscriptions = self.user_jobs.get(user_id, set())
        targets = {job_id} if job_id else set(subscriptions)
        if not targets:
            targets = {self.GLOBAL_SUBSCRIPTION}

        for subscription in targets:
            subscribers = self.job_subscribers.get(subscription)
            if not subscribers:
                continue
            if ws in subscribers:
                subscribers.remove(ws)
            if not subscribers:
                self.job_subscribers.pop(subscription, None)

        if job_id:
            subscriptions.discard(job_id)
        else:
            subscriptions.clear()

        if not subscriptions and user_id in self.user_jobs:
            self.user_jobs.pop(user_id, None)

        print(f"WebSocket disconnected: user={user_id}, job={job_id or '*'}")

    async def send_json(self, user_id: str, message: dict):
        """Send to a specific user."""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                print(f"Error sending to user {user_id}: {e}")
                self.disconnect(user_id)

    async def broadcast(self, message: dict, job_id: str):
        """Send to all clients subscribed to a job."""
        targets = [job_id, self.GLOBAL_SUBSCRIPTION]
        for target in targets:
            subscribers = self.job_subscribers.get(target)
            if not subscribers:
                continue

            dead_connections = []
            for ws in subscribers:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    print(f"WebSocket error for job {target}: {e}")
                    dead_connections.append(ws)

            for ws in dead_connections:
                subscribers.remove(ws)
            if not subscribers:
                self.job_subscribers.pop(target, None)

    async def send_job_update(self, job_id: str, status: str, extra: Optional[dict] = None):
        """Convenience: broadcast job status update."""
        payload = {
            "type": "JOB_STATUS_UPDATE",
            "data": {"status": status, **(extra or {})}
        }
        await self.broadcast(payload, job_id)

# Singleton
manager = ConnectionManager()