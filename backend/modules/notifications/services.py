import json
import logging

from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.mail import send_mail
from pydantic import BaseModel
from pywebpush import WebPushException, webpush

from config.settings import FROM_EMAIL
from modules.authentication.services import ClerkUserService
from modules.investors.models import Investor

from .models import PushSubscription

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
    def sync_send_email(self, to: list[str], subject: str, body: str) -> bool:
        try:
            send_mail(
                subject=subject,
                message=body,
                recipient_list=to,
                from_email=FROM_EMAIL,
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error("Failed to send email to %s: %s", to, e)
            return False

    async def send_email(self, to: list[str], subject: str, body: str) -> bool:
        return await sync_to_async(self.sync_send_email)(to, subject, body)


class PushService:
    def sync_send_push(
        self, subscription: PushSubscription, title: str, body: str
    ) -> bool:
        try:
            payload = {
                "title": title,
                "body": body,
            }
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.p256dh,
                        "auth": subscription.auth,
                    },
                },
                data=json.dumps(payload),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims=settings.VAPID_CLAIMS,
            )
            return True
        except WebPushException as e:
            logger.error("Push notification failed: %s", e)
            return False
        except Exception as e:
            logger.error("Unexpected error sending push notification: %s", e)
            return False

    async def send_push(
        self, subscription: PushSubscription, title: str, body: str
    ) -> bool:
        return await sync_to_async(self.sync_send_push)(subscription, title, body)


class WebSocketService:
    def __init__(self, channel_layer=None):
        self.channel_layer = channel_layer or get_channel_layer()

    async def send_websocket_notification(
        self, investor_id: str, message: dict
    ) -> bool:
        try:
            group_name = f"investor_{investor_id}"

            await self.channel_layer.group_send(
                group_name,
                {
                    "type": "notification_receive",
                    "data": {
                        "investor_id": investor_id,
                        "message": message,
                    },
                },
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to send WebSocket notification to investor %s: %s",
                investor_id,
                e,
            )
            return False


class NotificationService:
    def __init__(
        self,
        email_service: EmailService | None = None,
        push_service: PushService | None = None,
        websocket_service: WebSocketService | None = None,
        clerk_user_service: ClerkUserService | None = None,
    ):
        self.email_service = email_service or EmailService()
        self.push_service = push_service or PushService()
        self.websocket_service = websocket_service or WebSocketService()
        self.clerk_user_service = clerk_user_service or ClerkUserService()

    async def send_email_notification(
        self, investor: Investor, email_payload: EmailPayload
    ) -> None:
        clerk_id = investor.clerk_id
        addresses = self.clerk_user_service.get_user_email_addresses(clerk_id)
        await self.email_service.send_email(
            to=addresses, subject=email_payload.subject, body=email_payload.body
        )

    def sync_send_email_notification(
        self, investor: Investor, email_payload: EmailPayload
    ) -> bool:
        clerk_id = investor.clerk_id
        addresses = self.clerk_user_service.get_user_email_addresses(clerk_id)
        return self.email_service.sync_send_email(
            to=addresses, subject=email_payload.subject, body=email_payload.body
        )

    async def send_push_notifications(
        self, investor: Investor, push_payload: PushPayload
    ) -> None:
        push_subscriptions = await sync_to_async(list)(
            PushSubscription.objects.filter(investor=investor)
        )
        for subscription in push_subscriptions:
            await self.push_service.send_push(
                subscription=subscription,
                title=push_payload.title,
                body=push_payload.body,
            )

    def sync_send_push_notifications(
        self, investor: Investor, push_payload: PushPayload
    ) -> None:
        push_subscriptions = PushSubscription.objects.filter(investor=investor)
        
        all_success = True
        for subscription in push_subscriptions:
            success = self.push_service.sync_send_push(
                subscription=subscription,
                title=push_payload.title,
                body=push_payload.body,
            )
            if not success:
                all_success = False
        return all_success

    async def send_websocket_notifications(
        self, investor: Investor, websocket_payload: WebSocketPayload
    ) -> None:
        await self.websocket_service.send_websocket_notification(
            investor_id=str(investor.id),
            message=websocket_payload.message,
        )
