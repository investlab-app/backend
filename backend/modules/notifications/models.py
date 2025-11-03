from django.db import models
from django.utils.translation import gettext_lazy as _

from modules.core.models import BaseModel
from modules.investors.models import Investor


class Notification(BaseModel):
    """
    Stores notification history for all types of notifications.
    Used to display notification panel in the UI.
    """

    class Type(models.TextChoices):
        PRICE_ALERT = "price_alert", _("Price Alert")
        ORDER = "order", _("Order")
        TRANSACTION = "transaction", _("Transaction")
        SYSTEM = "system", _("System")

    investor = models.ForeignKey(
        Investor,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("Investor"),
    )
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.SYSTEM,
        verbose_name=_("Notification Type"),
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_("Title"),
    )
    message = models.TextField(
        verbose_name=_("Message"),
    )
    is_seen = models.BooleanField(
        default=False,
        verbose_name=_("Is Seen"),
    )
    related_object_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Related Object ID"),
        help_text=_("ID of the related object (e.g., price alert ID, order ID)"),
    )
    related_object_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Related Object Type"),
        help_text=_("Type of the related object (e.g., 'price_alert', 'order')"),
    )

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["investor", "-created_at"]),
            models.Index(fields=["investor", "is_seen", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.get_type_display()}: {self.title}"


class NotificationConfig(BaseModel):
    is_email = models.BooleanField(default=False, verbose_name=_("Send Email"))
    is_push = models.BooleanField(default=True, verbose_name=_("Send Push"))
    is_websocket = models.BooleanField(default=True, verbose_name=_("Send WebSocket"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        verbose_name = _("Notification Config")
        verbose_name_plural = _("Notification Configs")

    def __str__(self):
        return (
            f"NotificationConfig: Email({self.is_email}), Push({self.is_push}), "
            f"WebSocket({self.is_websocket})"
        )


class PushSubscription(BaseModel):
    endpoint = models.URLField(max_length=512, verbose_name=_("Endpoint"))
    p256dh = models.CharField(max_length=255, verbose_name=_("P256DH Key"))
    auth = models.CharField(max_length=255, verbose_name=_("Auth Key"))
    investor = models.ForeignKey(
        Investor, on_delete=models.CASCADE, verbose_name=_("Investor")
    )

    class Meta:
        verbose_name = _("Push Subscription")
        verbose_name_plural = _("Push Subscriptions")

    def __str__(self):
        return f"PushSubscription: {self.endpoint}"
