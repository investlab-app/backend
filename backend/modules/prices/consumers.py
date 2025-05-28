import json

from channels.generic.websocket import AsyncWebsocketConsumer


class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({"message": "Connection established"}))

    async def disconnect(self, code):
        print(f"WebSocket disconnected with code: {code}")

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            return
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        print(f"Received message: {message}")

        await self.send(text_data=json.dumps({"message": f"Echo: {message}"}))
