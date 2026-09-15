from fastapi import WebSocket


class ChatManager:
    def __init__(self):
        self.connections: dict[int, list[WebSocket]] = {}

    async def connect(self, conversation_id: int, websocket: WebSocket):
        await websocket.accept()
        self.connections.setdefault( conversation_id,[]).append(websocket)

    def disconnect(self, conversation_id: int, websocket: WebSocket):
        connections = self.connections.get(conversation_id)
        if not connections:
            return
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            del self.connections[conversation_id]

    async def send_to_conversation(self, conversation_id: int, data: dict):
        connections = self.connections.get(conversation_id, [])
        for websocket in connections:
            await websocket.send_json(data)
