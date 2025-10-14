import json
import logging

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.mail import send_mail
from pydantic import BaseModel
from pywebpush import WebPushException, webpush

from config.settings import FROM_EMAIL
from modules.authentication.services import ClerkUserService

from .models import Notification, PushSubscription

logger = logging.getLogger(__name__)

class EmailPayload(BaseModel):
    subject: str
    body: str


class PushPayload(BaseModel):
    title: str
    body: str


class WebSocketPayload(BaseModel):
    message: dict

class EmailService:

    async def send_email(self, to: list[str], subject: str, body: str) -> bool:
        pass


class PushService:
    async def send_push(
        self, subscription: PushSubscription, title: str, body: str
    ) -> bool:
        pass


class WebSocketService:
    def __init__(self, channel_layer):
        self.channel_layer = channel_layer

    async def send_websocket_notification(
        self, investor_id: str, message: dict
    ) -> bool:
        pass

class NotificationService:
    def __init__(
        self,
        email_service: "EmailService" = EmailService(),
        push_service: 'PushService' = PushService(),
        websocket_service: 'WebSocketService' = WebSocketService(),
        clerk_user_service: ClerkUserService = ClerkUserService(),
    ):
        pass

    async def send_email_notification(
        self, investor :Investor, email_payload: EmailPayload
    ) -> None:
        pass

    async def send_push_notifications(
        self, investor: Investor, push_payload: PushPayload
    ) -> None:
        pass

    async def send_websocket_notifications(
        self, investor: Investor, websocket_payload: WebSocketPayload
    ) -> None:
        pass

