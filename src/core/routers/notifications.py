from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from ..util.sockermanger import SocketManager
from ..util.security import check_access_token

manager = SocketManager()

router = APIRouter(prefix="/websocket", tags="Websocket api")

@router.websocket("")
async def connect(socket:WebSocket, payload:dict = Depends(check_access_token)):
    await manager.connect(payload.get("sub"), socket)

    