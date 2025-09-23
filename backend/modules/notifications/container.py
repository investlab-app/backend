from channels.layers import get_channel_layer

from modules.authentication.services import ClerkUserService
from modules.notifications.services import (
    EmailService,
    NotificationService,
    PriceAlertHandler,
    PushService,
    WebSocketService,
)


def get_price_alert_handler():
    email_service = EmailService()
    push_service = PushService()
    websocket_service = WebSocketService(get_channel_layer())
    clerk_user_service = ClerkUserService()
    notification_handler = NotificationService(
        email_service,
        push_service,
        websocket_service,
        clerk_user_service,
    )
    return PriceAlertHandler(notification_handler)
