"""
PropOS — WebSocket Server

Real-time data streaming to the dashboard frontend.
Publishes system state updates at a configurable interval.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from backend.core.logging import get_logger
from backend.core.state import get_state

logger = get_logger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)
        logger.info("WebSocket client connected", total=len(self._connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)
        logger.info("WebSocket client disconnected", total=len(self._connections))

    async def broadcast(self, data: dict[str, Any]) -> None:
        """Send data to all connected clients."""
        message = json.dumps(data, default=str)
        disconnected = []
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)

    @property
    def active_connections(self) -> int:
        return len(self._connections)


# Global connection manager
ws_manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time dashboard updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Send state update every second
            state = get_state()
            data = await state.to_dict()
            await websocket.send_json({"type": "state_update", "data": data})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        ws_manager.disconnect(websocket)
