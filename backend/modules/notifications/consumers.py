import json
import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer

from modules.investors.models import Investor
from modules.prices.constants import PRICES_CHANNEL_LAYER

logger = logging.getLogger(__name__)


class Websocket(AsyncWebsocketConsumer):
    """WebSocket consumer for prices channel - handles price subscriptions."""

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

    async def broadcast_receive(self, event):
        data = event["data"]

        selected_tickers = [data[ticker] for ticker in self.names if ticker in data]
        if selected_tickers:
            await self.send(text_data=json.dumps({"prices": selected_tickers}))

    async def notification_receive(self, event):
        """
        Handle price alert notifications for this specific investor.
        Only sends notifications to the user's own WebSocket connections.
        """
        data = event["data"]

        # Only send to the specific investor's connections (only if investor exists)
        if self.investor and str(data["investor_id"]) == str(self.investor.id):
            await self.send(text_data=json.dumps({"notification": data["message"]}))

    async def receive(self, text_data=None, _=None):
        if text_data is None:
            return

        if isinstance(text_data, (bytes, bytearray)):
            text_data = text_data.decode("utf-8")

        if text_data == "ping":
            await self.send(text_data="pong")
            return

        try:
            json_data = json.loads(text_data)
        except Exception:
            return

        self.names = json_data.get("set_subscription", [])

    async def disconnect(self, code):
        if not self.layer:
            return
        await self.layer.group_discard(PRICES_CHANNEL_LAYER, self.channel_name)
        if self.investor:
            await self.layer.group_discard(
                f"investor_{self.investor.id}", self.channel_name
            )


class NotificationsConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for notifications channel - handles in-app notifications."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layer = None
        self.investor = None

    async def connect(self):
        """Handle WebSocket connection for notifications."""
        if not self.scope["user"].is_authenticated:
            await self.accept()
            await self.close()
            return

        clerk_id = self.scope["user"].id

        self.investor = await sync_to_async(
            Investor.objects.filter(clerk_id=clerk_id).first
        )()

        if not self.investor:
            await self.accept()
            await self.close()
            return

        self.layer = get_channel_layer()

        # Subscribe to investor-specific notification group
        await self.layer.group_add(
            f"investor_notifications_{self.investor.id}",
            self.channel_name,
        )

        await self.accept()
        logger.info(
            f"Notifications WebSocket connected for investor {self.investor.id}"
        )

    async def notification_receive(self, event):
        """
        Receive notification message from channel layer and send to WebSocket.
        """
        notification = event["notification"]
        await self.send(text_data=json.dumps({"notification": notification}))

    async def receive(self, text_data=None, _=None):
        """Handle incoming messages from client."""
        if text_data is None:
            return

        if isinstance(text_data, (bytes, bytearray)):
            text_data = text_data.decode("utf-8")

        if text_data == "ping":
            await self.send(text_data="pong")
            return

    async def disconnect(self, code):
        """Handle WebSocket disconnection."""
        if not self.layer or not self.investor:
            return

        await self.layer.group_discard(
            f"investor_notifications_{self.investor.id}",
            self.channel_name,
        )
        logger.info(
            f"Notifications WebSocket disconnected for investor {self.investor.id}"
        )
