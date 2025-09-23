import asyncio
import json
import logging
from typing import Any

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from pydantic import BaseModel
from pywebpush import WebPushException, webpush

from config.settings import FROM_EMAIL
from modules.authentication.services import ClerkUserService

from .models import Notification, PriceAlert, PushSubscription

logger = logging.getLogger(__name__)


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
    def __init__(self, channel_layer):
        self.channel_layer = channel_layer

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


class EmailPayload(BaseModel):
    subject: str
    body: str


class PushPayload(BaseModel):
    title: str
    body: str


class WebSocketPayload(BaseModel):
    message: dict


class NotificationService:
    def __init__(
        self,
        email_service: EmailService,
        push_service: PushService,
        websocket_service: WebSocketService,
        clerk_user_service: ClerkUserService,
    ):
        self.email_service = email_service
        self.push_service = push_service
        self.websocket_service = websocket_service
        self.clerk_user_service = clerk_user_service

    async def send_email_notification(
        self, notification: Notification, email_payload: EmailPayload
    ) -> None:
        clerk_id = notification.investor.clerk_id
        addresses = self.clerk_user_service.get_user_email_addresses(clerk_id)
        await self.email_service.send_email(
            to=addresses, subject=email_payload.subject, body=email_payload.body
        )

    async def send_push_notifications(
        self, notification: Notification, push_payload: PushPayload
    ) -> None:
        push_subscriptions = await sync_to_async(list)(
            PushSubscription.objects.filter(investor=notification.investor)
        )
        for subscription in push_subscriptions:
            await self.push_service.send_push(
                subscription=subscription,
                title=push_payload.title,
                body=push_payload.body,
            )

    async def send_websocket_notifications(
        self, notification: Notification, websocket_payload: WebSocketPayload
    ) -> None:
        await self.websocket_service.send_websocket_notification(
            investor_id=str(notification.investor.id),
            message=websocket_payload.message,
        )


class PriceAlertHandler:
    def __init__(self, handler: NotificationService):
        self.handler = handler

    async def handle(
        self,
        prices: dict[str, Any],
    ) -> None:
        conditions = Q()

        for ticker, price_info in prices.items():
            current_price = price_info.get("close")
            if current_price is None:
                continue

            ticker_conditions = Q(
                instrument__ticker=ticker,
                threshold_type="above",
                threshold_value__lte=current_price,
            ) | Q(
                instrument__ticker=ticker,
                threshold_type="below",
                threshold_value__gte=current_price,
            )

            conditions |= ticker_conditions

        if not conditions.children:
            return

        query = PriceAlert.objects.filter(
            conditions,
            is_active=True,
        ).select_related(
            "instrument",
            "investor",
        )

        notifications = await sync_to_async(list)(query)

        # concurrency limit
        semaphore = asyncio.Semaphore(10)

        async def process_notification(notification):
            async with semaphore:
                language = notification.investor.language
                await self.send_notifications(notification, prices, language)
                await sync_to_async(notification.delete)()

        tasks = [
            asyncio.create_task(process_notification(notification))
            for notification in notifications
        ]
        await asyncio.gather(*tasks)

    async def send_notifications(
        self,
        notification: PriceAlert,
        prices: dict[str, Any],
        language: str,
    ) -> None:
        try:
            price_info = prices[notification.instrument.ticker]
            current_price = price_info["close"]

            if notification.is_email:
                email_payload = self.get_email_payload(
                    language,
                    notification.instrument.ticker,
                    current_price,
                    notification,
                )
                await self.handler.send_email_notification(
                    notification,
                    email_payload,
                )

            if notification.is_push:
                push_payload = self.get_push_payload(
                    language,
                    notification.instrument.ticker,
                    current_price,
                    notification,
                )
                await self.handler.send_push_notifications(
                    notification,
                    push_payload,
                )

            if notification.is_websocket:
                websocket_payload = self.get_websocket_payload(
                    language,
                    notification.instrument.ticker,
                    current_price,
                    notification,
                )
                await self.handler.send_websocket_notifications(
                    notification,
                    websocket_payload,
                )
        except Exception as e:
            logger.error("Error handling notification %s: %s", notification.id, e)

    def get_email_payload(
        self,
        language: str,
        ticker: str,
        current_price: float,
        notification: PriceAlert,
    ) -> EmailPayload:
        if language == "pl":
            threshold_type = (
                "powyżej" if notification.threshold_type == "above" else "poniżej"
            )
            return EmailPayload(
                subject="Alert cenowy",
                body=(
                    f"Twój alert dla {ticker}. "
                    f"został wyzwolony. Cena jest teraz "
                    f"{threshold_type} {notification.threshold_value}. "
                    f"Aktualna cena: {current_price}"
                ),
            )
        return EmailPayload(
            subject="Price Alert",
            body=(
                f"Your alert for {ticker}. The price is now "
                f"{notification.threshold_type} {notification.threshold_value}. "
                f"Current price: {current_price}"
            ),
        )

    def get_push_payload(
        self,
        language: str,
        ticker: str,
        current_price: float,
        notification: PriceAlert,
    ) -> PushPayload:
        if language == "pl":
            threshold_type = (
                "powyżej" if notification.threshold_type == "above" else "poniżej"
            )
            return PushPayload(
                title="Alert cenowy",
                body=(
                    f"Twój alert dla {ticker} "
                    f"został wyzwolony. Cena jest teraz "
                    f"{threshold_type} {notification.threshold_value}. "
                    f"Aktualna cena: {current_price}"
                ),
            )
        return PushPayload(
            title="Price Alert",
            body=(
                f"Your alert for {ticker} "
                f"has been triggered. The price is now "
                f"{notification.threshold_type} {notification.threshold_value}. "
                f"Current price: {current_price}"
            ),
        )

    def get_websocket_payload(
        self,
        language: str,
        ticker: str,
        current_price: float,
        notification: PriceAlert,
    ) -> WebSocketPayload:
        if language == "pl":
            threshold_type = (
                "powyżej" if notification.threshold_type == "above" else "poniżej"
            )
            return WebSocketPayload(
                message={
                    "type": "price_alert",
                    "title": "Alert cenowy",
                    "body": (
                        f"Twój alert dla {ticker} "
                        f"został wyzwolony. Cena jest teraz "
                        f"{threshold_type} {notification.threshold_value}. "
                        f"Aktualna cena: {current_price}"
                    ),
                }
            )
        return WebSocketPayload(
            message={
                "type": "price_alert",
                "title": "Price Alert",
                "body": (
                    f"Your alert for {ticker} "
                    f"has been triggered. The price is now "
                    f"{notification.threshold_type} {notification.threshold_value}. "
                    f"Current price: {current_price}"
                ),
            }
        )
