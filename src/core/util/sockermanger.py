from fastapi import WebSocket, status


class SocketManager:
    def __init__(self):
        self.connections: dict[int:WebSocket] = {}


    async def connect(self, uid:int, socket:WebSocket):
        if uid in self.connections:
            old_conection = self.connections[uid]

            try:
                await old_conection.close(
                    code=status.WS_1008_POLICY_VIOLATION
                )

            except:
                pass
        
        await socket.accept()

        self.connections[uid] = socket
    

    def disconnect(self, uid:int):
        if uid in self.connections:
            del self.connections[uid]


    async def senf_notification(self, uids: int|list[int], message:dict):
        for id in uids:
            if id in self.connections:
                socket = self.connections[id]

                try:
                    await socket.send_json(message)

                except Exception as e:
                    self.disconnect(id)