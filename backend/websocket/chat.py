import logging

from fastapi import WebSocket, WebSocketDisconnect, APIRouter

from backend.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


@router.websocket("/ws/chat")
async def chat_ws(ws: WebSocket):
    await ws.accept()
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")


@router.websocket("/ws/alerts")
async def alert_ws(ws: WebSocket):
    await manager.connect_nurse(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_nurse(ws)
    except Exception:
        manager.disconnect_nurse(ws)
