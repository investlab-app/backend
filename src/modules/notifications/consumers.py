import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer

from modules.investors.models import Investor
from modules.prices.constants import PRICES_CHANNEL_LAYER

logger = logging.getLogger(__name__)


class Websocket(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layer = None
        self.investor = None
        self.names = []

    async def connect(self):
        if not self.scope["user"].is_authenticated:
            await self.accept()
            await self.close()
            return

        clerk_id = self.scope["user"].id

        self.investor = await sync_to_async(
            Investor.objects.filter(clerk_id=clerk_id).first
        )()

        self.names = self.scope["url_route"]["kwargs"].get("names", "").split(",")
        self.layer = get_channel_layer()

        await self.layer.group_add(PRICES_CHANNEL_LAYER, self.channel_name)
        if self.investor:
            await self.layer.group_add(
                f"investor_{self.investor.id}", self.channel_name
            )

        await self.accept()

    async def receive_json(self, content=None, **kwargs):
        if content is None:
            return

        if "type" not in content:
            logger.warning("Received invalid message without type: %s", content)
            return

        if content["type"] == "ping":
            await self.send_json({"type": "pong"})
            return

        if content["type"] == "set_subscription":
            self.names = content.get("subscriptions", [])

    async def disconnect(self, code):
        if not self.layer:
            return
        await self.layer.group_discard(PRICES_CHANNEL_LAYER, self.channel_name)
        if self.investor:
            await self.layer.group_discard(
                f"investor_{self.investor.id}", self.channel_name
            )

    # TODO: Add validation for outgoing messages

    async def send_prices(self, event):
        data = event["data"]

        selected_tickers = [data[ticker] for ticker in self.names if ticker in data]
        if selected_tickers:
            await self.send_json({"type": "prices", "data": selected_tickers})

    async def send_notification(self, event):
        data = event["data"]
        await self.send_json({"type": "notification", "data": data["message"]})

    async def send_llm(self, event):
        data = event["data"]
        await self.send_json({"type": "llm", "data": data})

    async def send_order_update(self, event):
        data = event["data"]
        await self.send_json({"type": "order_update", "data": data})
