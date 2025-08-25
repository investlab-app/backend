import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer

from modules.prices.constants import PRICES_CHANNEL_LAYER


class PriceStreamConsumer(AsyncWebsocketConsumer):
    names = []

    async def connect(self):
        if not self.scope["user"].is_authenticated:
            await self.close()
            return

        self.names = self.scope["url_route"]["kwargs"]["names"].split(",")
        self.layer = get_channel_layer()
        await self.layer.group_add(PRICES_CHANNEL_LAYER, self.channel_name)
        await self.accept()

    async def broadcast_receive(self, event):
        selected_tickers = [
            event["data"][ticker] for ticker in self.names if ticker in event["data"]
        ]
        if selected_tickers != []:
            await self.send(text_data=json.dumps({"prices": selected_tickers}))

    async def receive(self, text_data=None, _=None):
        try:
            json_data = json.loads(text_data)  # ty: ignore
        except Exception:
            return

        self.names = json_data.get("set_subscription", [])
