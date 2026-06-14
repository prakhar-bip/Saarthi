"""
Shared WebSocket Connection Manager for Sarthi.
Imported by both main.py (to register the /ws/notifications endpoint)
and projects.py (to broadcast compilation progress events).
"""
import json
from loguru import logger
from fastapi import WebSocket



class ConnectionManager:
    def __init__(self):
        # Maps project_id -> list of connected WebSockets
        self._project_sockets: dict[str, list[WebSocket]] = {}
        # Global broadcast sockets (not tied to a project)
        self._global_sockets: list[WebSocket] = []

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self, websocket: WebSocket, project_id: str | None = None):
        await websocket.accept()
        if project_id:
            self._project_sockets.setdefault(project_id, []).append(websocket)
            logger.info(f"WS connected for project {project_id}. Total for project: {len(self._project_sockets[project_id])}")
        else:
            self._global_sockets.append(websocket)
            logger.info(f"Global WS connected. Total global: {len(self._global_sockets)}")

    def disconnect(self, websocket: WebSocket, project_id: str | None = None):
        if project_id and project_id in self._project_sockets:
            sockets = self._project_sockets[project_id]
            if websocket in sockets:
                sockets.remove(websocket)
            if not sockets:
                del self._project_sockets[project_id]
        elif websocket in self._global_sockets:
            self._global_sockets.remove(websocket)

    # ------------------------------------------------------------------
    # Messaging
    # ------------------------------------------------------------------

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send personal WS message: {e}")

    async def broadcast(self, message: str):
        """Broadcast to all global sockets."""
        dead = []
        for ws in list(self._global_sockets):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self._global_sockets:
                self._global_sockets.remove(ws)

    async def broadcast_to_project(self, project_id: str, payload: dict):
        """Send a JSON payload to every socket subscribed to a project."""
        message = json.dumps(payload)
        sockets = list(self._project_sockets.get(project_id, []))
        dead = []
        for ws in sockets:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            bucket = self._project_sockets.get(project_id, [])
            if ws in bucket:
                bucket.remove(ws)

    async def broadcast_progress(
        self,
        project_id: str,
        progress: int,
        step: str,
        status: str = "generating",
    ):
        """Convenience wrapper used by the compilation pipeline."""
        await self.broadcast_to_project(
            project_id,
            {
                "type": "progress",
                "project_id": project_id,
                "progress": progress,
                "step": step,
                "status": status,
            },
        )
        # Also push to global sockets so any dashboard listener sees it
        await self.broadcast(
            json.dumps(
                {
                    "type": "progress",
                    "project_id": project_id,
                    "progress": progress,
                    "step": step,
                    "status": status,
                }
            )
        )


# Singleton used across the whole application
manager = ConnectionManager()
