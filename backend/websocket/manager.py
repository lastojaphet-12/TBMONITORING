import asyncio
import logging
import threading
from typing import Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.nurse_connections: Set[WebSocket] = set()

    async def connect_nurse(self, ws: WebSocket) -> None:
        await ws.accept()
        self.nurse_connections.add(ws)

    def disconnect_nurse(self, ws: WebSocket) -> None:
        self.nurse_connections.discard(ws)

    async def broadcast_to_nurses(self, message: dict) -> None:
        dead: Set[WebSocket] = set()
        for ws in self.nurse_connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.nurse_connections.discard(ws)


manager = ConnectionManager()

_broadcast_loop: asyncio.AbstractEventLoop | None = None
_broadcast_thread: threading.Thread | None = None


def _ensure_broadcast_loop() -> asyncio.AbstractEventLoop:
    global _broadcast_loop, _broadcast_thread
    if _broadcast_loop is None or not _broadcast_thread.is_alive():
        _broadcast_loop = asyncio.new_event_loop()
        _broadcast_thread = threading.Thread(
            target=_broadcast_loop.run_forever, daemon=True, name="ws-broadcast"
        )
        _broadcast_thread.start()
    return _broadcast_loop


def broadcast_alert_sync(alert_data: dict) -> None:
    loop = _ensure_broadcast_loop()
    asyncio.run_coroutine_threadsafe(
        manager.broadcast_to_nurses(alert_data), loop
    )
