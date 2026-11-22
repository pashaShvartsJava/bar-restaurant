from fastapi import WebSocket


class ChatManager:
    def __init__(self):
        self.connections: dict[int, list[WebSocket]] = {}

    async def connect(self, conversation_id: int, websocket: WebSocket):
        await websocket.accept()
        self.connections.setdefault(conversation_id, []).append(websocket)

    async def disconnect(self, conversation_id: int, websocket: WebSocket):
        connections = self.connections.get(conversation_id)
        if not connections:
            return
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            self.connections.pop(conversation_id, None)

    async def send_to_conversation(self, conversation_id: int, data: dict):
        connections = self.connections.get(conversation_id, [])
        disconnected = []
        for websocket in connections.copy():
            try:
                await websocket.send_json(data)
            except Exception:
                disconnected.append(websocket)
        for websocket in disconnected:
            await self.disconnect(conversation_id, websocket)
