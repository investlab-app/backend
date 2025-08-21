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

        self.names = []
        self.layer = get_channel_layer()
        await self.layer.group_add(PRICES_CHANNEL_LAYER, self.channel_name)
        await self.accept()

    async def broadcast_receive(self, event):
        selected_tickers = [
            event["data"][ticker] for ticker in self.names if ticker in event["data"]
        ]
        if selected_tickers != []:
            await self.send(text_data=json.dumps({"prices": selected_tickers}))

    async def receive(self, text_data=None, bytes_data=None):
        try:
            json_data = json.loads(text_data)  # ty: ignore
        except Exception:
            return

        sub_list = json_data.get("subscribe", [])
        unsub_list = json_data.get("unsubscribe", [])
        self._process_sub_unsub_lists(sub_list, unsub_list)

    def _process_sub_unsub_lists(self, sub_list, unsub_list):
        for ticker in sub_list:
            if ticker not in self.names:
                self.names.append(ticker)

        for ticker in unsub_list:
            if ticker in self.names:
                self.names.remove(ticker)
