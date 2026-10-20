import asyncio
import concurrent.futures
import json
import logging
from collections import defaultdict
from typing import Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ProjectConnectionManager:
    """In-memory project channels; use a shared broker for multi-worker deployments."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, project_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        await self.register(project_id, websocket)

    async def register(self, project_id: str, websocket: WebSocket) -> None:
        self._loop = asyncio.get_running_loop()
        async with self._lock:
            self._connections[project_id].add(websocket)

    async def disconnect(self, project_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            clients = self._connections.get(project_id)
            if clients is not None:
                clients.discard(websocket)
                if not clients:
                    self._connections.pop(project_id, None)

    async def broadcast(self, project_id: str, event: dict[str, Any]) -> None:
        payload = json.dumps(event, default=str)
        async with self._lock:
            clients = tuple(self._connections.get(project_id, ()))
        stale: list[WebSocket] = []
        for websocket in clients:
            try:
                await websocket.send_text(payload)
            except Exception:
                logger.debug("Removing an unavailable project websocket")
                stale.append(websocket)
        for websocket in stale:
            await self.disconnect(project_id, websocket)

    async def broadcast_user(self, user_id: str, event: dict[str, Any]) -> None:
        """Deliver a personal event only to project sockets the user joined."""
        payload = json.dumps(event, default=str)
        async with self._lock:
            recipients = [
                (project_id, websocket)
                for project_id, sockets in self._connections.items()
                for websocket in sockets
                if getattr(websocket, "taskflow_user_id", None) == user_id
            ]
        stale: list[tuple[str, WebSocket]] = []
        for project_id, websocket in recipients:
            try:
                await websocket.send_text(payload)
            except Exception:
                stale.append((project_id, websocket))
        for project_id, websocket in stale:
            await self.disconnect(project_id, websocket)

    def connection_count(self, project_id: str) -> int:
        return len(self._connections.get(project_id, ()))


project_connections = ProjectConnectionManager()


def publish_project_event(project_id: Any, event_type: str, data: dict[str, Any]) -> None:
    """Schedule a committed event broadcast when an ASGI loop is active."""
    event = {"type": event_type, "project_id": str(project_id), "data": data}
    _schedule(project_connections.broadcast(str(project_id), event))


def publish_user_event(user_id: Any, event_type: str, project_id: Any, data: dict[str, Any]) -> None:
    event = {"type": event_type, "project_id": str(project_id), "data": data}
    _schedule(project_connections.broadcast_user(str(user_id), event))


def _schedule(coroutine: Any) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = project_connections._loop
        if loop is None or loop.is_closed():
            coroutine.close()
            return
        asyncio.run_coroutine_threadsafe(coroutine, loop)
    else:
        loop.create_task(coroutine)