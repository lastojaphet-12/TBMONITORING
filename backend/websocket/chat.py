from fastapi import WebSocket, APIRouter

router = APIRouter(tags=["chat"])


@router.websocket("/ws/chat")
def chat_ws(ws: WebSocket):
    # Simple echo stub.
    # A real implementation would authenticate user and route messages.
    return ws.receive_text()

