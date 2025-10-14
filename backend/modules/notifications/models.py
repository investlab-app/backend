from django.db import models
from django.utils.translation import gettext_lazy as _

from modules.core.models import BaseModel
from modules.instruments.models import Instrument
from modules.investors.models import Investor


class NotificationConfig(BaseModel):
    is_email = models.BooleanField(default=False, verbose_name=_("Send Email"))
    is_push = models.BooleanField(default=True, verbose_name=_("Send Push"))
    is_websocket = models.BooleanField(default=True, verbose_name=_("Send WebSocket"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    # created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At")) # REVIEW Already in baseModel

class PushSubscriptionCredentials(BaseModel):
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

